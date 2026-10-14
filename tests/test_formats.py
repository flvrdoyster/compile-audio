import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.dirname(__file__))
import helpers
from compileaudio import NotAudio, load, mlk, wlk
from compileaudio.wav import to_wav


def test_mlk_roundtrip():
    songs = [(1, helpers.smf(loop_tick=24)), (0, helpers.smf()), (2, helpers.smf())]
    parsed = mlk.parse(helpers.mlk(songs, tail=b"\0" * 24))
    assert [s.flag for s in parsed] == [1, 0, 2]
    assert [s.data for s in parsed] == [d for _, d in songs]
    assert [s.loop for s in parsed] == [True, False, False]   # 반복은 비트 0만


def test_smf_info_loop_marker_and_end():
    info = mlk.smf_info(helpers.smf(loop_tick=24, end_tick=96, division=48))
    assert (info.division, info.loop_tick, info.end_tick) == (48, 24, 96)
    assert (info.format, info.tracks) == (0, 1)


def test_smf_info_time_signature_is_not_a_loop_marker():
    # 길이 4인 FF 58(정상 박자표)만 있으면 반복 마커 없음
    assert mlk.smf_info(helpers.smf(loop_tick=None)).loop_tick is None


def test_mlk_rejects_non_smf_and_out_of_range():
    good = helpers.mlk([(1, helpers.smf())])
    with pytest.raises(mlk.NotMlk):
        mlk.parse(b"\x01" + b"\x01\x0a\0\0\0\x20\0\0\0" + b"x" * 40)   # MThd 아님
    with pytest.raises(mlk.NotMlk):
        mlk.parse(good[:20])                                                                  # 잘림
    with pytest.raises(mlk.NotMlk):
        mlk.parse(b"")


PCM8 = bytes(range(0, 200, 2))


def test_wlk_headerless_roundtrip():
    raw = helpers.wlk_headerless([(0, 0x00, 11025, PCM8), (0, 0x80, 22050, PCM8 * 2)])
    w = wlk.parse(raw)
    assert w.variant == "headerless" and w.trailing == 0
    a, b = w.samples
    assert (a.rate, a.bits, a.channels, a.frames, a.extra, a.data) == (11025, 8, 1, len(PCM8), (), PCM8)
    assert (b.rate, b.bits, b.frames) == (22050, 16, len(PCM8))


def test_wlk_v2_roundtrip_with_extra():
    raw = helpers.wlk_v2([(255, 0x00, 22050, PCM8, (-500, 0)), (255, 0xC0, 44100, PCM8, (-1200, 7))])
    w = wlk.parse(raw)
    assert w.variant == "WLKF0200" and w.trailing == 0
    assert w.samples[0].extra == (-500, 0) and w.samples[1].extra == (-1200, 7)
    assert w.samples[1].bits == 16 and w.samples[1].channels == 2
    assert w.samples[1].frames == len(PCM8) // 4


def test_containers_reject_each_other():
    m = helpers.mlk([(1, helpers.smf())])
    w1 = helpers.wlk_headerless([(0, 0, 11025, PCM8)])
    w2 = helpers.wlk_v2([(255, 0, 22050, PCM8, (0, 0))])
    for raw in (w1, w2):
        with pytest.raises(mlk.NotMlk):
            mlk.parse(raw)
    with pytest.raises(wlk.NotWlk):
        wlk.parse(m)


def test_load_picks_the_right_reader():
    assert load(helpers.mlk([(1, helpers.smf())]))[0] == "mlk"
    kind, w = load(helpers.wlk_v2([(255, 0, 22050, PCM8, (0, 0))]))
    assert (kind, w.variant) == ("wlk", "WLKF0200")
    kind, w = load(helpers.wlk_headerless([(0, 0, 11025, PCM8)]))
    assert (kind, w.variant) == ("wlk", "headerless")
    with pytest.raises(NotAudio):
        load(b"not audio at all, just some text" * 4)


def test_wlk_rejects_overlap_and_bad_rate():
    raw = bytearray(helpers.wlk_headerless([(0, 0, 11025, PCM8), (0, 0, 11025, PCM8)]))
    raw[2 + 14 + 2] = 2        # 두 번째 오프셋을 앞으로 당겨 겹치게
    with pytest.raises(wlk.NotWlk):
        wlk.parse(bytes(raw))
    with pytest.raises(wlk.NotWlk):
        wlk.parse(helpers.wlk_headerless([(0, 0, 5, PCM8)]))


def test_wav_header():
    w = to_wav(b"\x80" * 10, 1, 11025, 8)
    assert w[:4] == b"RIFF" and w[8:12] == b"WAVE" and len(w) == 44 + 10
    assert int.from_bytes(w[24:28], "little") == 11025 and int.from_bytes(w[34:36], "little") == 8
