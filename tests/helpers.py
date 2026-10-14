"""테스트용 합성 컨테이너 -- 게임 데이터 없이 파서를 검증한다."""
import struct


def smf(loop_tick=None, end_tick=96, division=48, tempo_marker=True):
    """트랙 1개짜리 형식 0 SMF. loop_tick을 주면 그 틱에 `FF 59 02` 마커를 둔다."""
    body = b""
    tick = 0
    if loop_tick is not None:
        body += _vlq(loop_tick - tick) + b"\xFF\x59\x02\x00\x00"
        tick = loop_tick
    if tempo_marker:  # 길이 4인 정상 박자표는 마커가 아니다
        body += _vlq(0) + b"\xFF\x58\x04\x04\x02\x18\x08"
    body += _vlq(0) + b"\x90\x3C\x40" + _vlq(end_tick - tick - 10) + b"\x80\x3C\x00"
    body += _vlq(10) + b"\xFF\x2F\x00"
    return (b"MThd" + struct.pack(">IHHH", 6, 0, 1, division)
            + b"MTrk" + struct.pack(">I", len(body)) + body)


def _vlq(v):
    out = [v & 0x7F]
    v >>= 7
    while v:
        out.append(0x80 | (v & 0x7F))
        v >>= 7
    return bytes(reversed(out))


def mlk(songs, tail=b""):
    """songs: [(flag, smf_bytes)]"""
    table = bytes([len(songs)])
    offset = 1 + 9 * len(songs)
    body = b""
    for flag, data in songs:
        table += bytes([flag]) + struct.pack("<II", offset + len(body), len(data))
        body += data
    return table + body + tail


def _entries(samples, table_end, extra):
    out, body, offset = b"", b"", table_end
    for flag, fmt, rate, pcm, *x in samples:
        out += bytes([flag, fmt]) + struct.pack("<III", offset + len(body), len(pcm), rate)
        if extra:
            out += struct.pack("<ii", *(x[0] if x else (0, 0)))
        body += pcm
    return out, body


def wlk_headerless(samples):
    """samples: [(b0, format, rate, pcm)]"""
    table_end = 2 + 14 * len(samples)
    entries, body = _entries(samples, table_end, extra=False)
    return struct.pack("<H", len(samples) - 1) + entries + body


def wlk_v2(samples):
    """samples: [(b0, format, rate, pcm, (extra0, extra1))]"""
    table_end = 12 + 22 * len(samples)
    entries, body = _entries(samples, table_end, extra=True)
    return b"WLKF0200" + struct.pack("<I", len(samples)) + entries + body
