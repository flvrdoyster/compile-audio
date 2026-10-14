import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.dirname(__file__))
import helpers
from compileaudio import extract as ex


def test_scan_and_save(tmp_path):
    game = tmp_path / "game"
    (game / "sub").mkdir(parents=True)
    songs = [(1, helpers.smf(loop_tick=24)), (0, helpers.smf())]
    (game / "SMASH.MLK").write_bytes(helpers.mlk(songs))
    (game / "sub" / "PCM.WLK").write_bytes(helpers.wlk_v2([(255, 0, 22050, b"\x80" * 8, (-500, 0))]))
    (game / "README.TXT").write_bytes(b"hello, this is not audio data at all" * 3)
    (game / "EMPTY").write_bytes(b"")

    out = tmp_path / "out"
    results = list(ex.scan(str(game)))
    by = {r.source: r for r in results}
    assert by["SMASH.MLK"].status == ex.OK and by["sub/PCM.WLK"].status == ex.OK
    assert by["README.TXT"].status == ex.UNKNOWN and by["EMPTY"].status == ex.SKIPPED

    for r in results:
        if r.status == ex.OK:
            ex.save(r, str(out))
    assert (out / "SMASH.MLK" / "bgm_00.mid").read_bytes() == songs[0][1]
    idx = json.loads((out / "SMASH.MLK" / "index.json").read_text(encoding="utf-8"))
    assert idx["songs"][0]["loopTick"] == 24 and idx["songs"][1]["loop"] is False
    wav = (out / "sub" / "PCM.WLK" / "se_00.wav").read_bytes()
    assert wav[:4] == b"RIFF" and len(wav) == 44 + 8
    idx = json.loads((out / "sub" / "PCM.WLK" / "index.json").read_text(encoding="utf-8"))
    assert idx["variant"] == "WLKF0200" and idx["samples"][0]["extra"] == [-500, 0]
