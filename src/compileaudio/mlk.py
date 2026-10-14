"""MLK -- Compile Windows 게임의 MIDI 곡 묶음.

    [u8  곡 수 N]
    N x { u8 플래그, u32le 오프셋, u32le 크기 }      (9바이트 항목)
    ... 표준 MIDI 파일(SMF) N개 ...                  (뒤에 어느 항목도 가리키지 않는 꼬리가 있을 수 있음)

플래그 비트 0이 반복. 환세쾌진극 EXE 분석에서 읽는 비트는 0뿐임이 확인됐고, 그 밖의
값(0·1·2)은 곡 종류에 따라 갈리지만 의미는 미확인. SMF는 전부 형식 0·트랙 1개.
반복 시작점은 길이 2인 메타 이벤트 `FF 59`(또는 `FF 58`)가 놓인 틱이고, 없으면 곡 처음.
(`FF 58`은 정상 박자표라 길이 4 -- 길이가 2일 때만 마커로 본다.)
"""
import struct
from dataclasses import dataclass
from typing import List, Optional

ENTRY = 9


class NotMlk(ValueError):
    pass


@dataclass
class Song:
    index: int
    flag: int
    offset: int
    size: int
    data: bytes

    @property
    def loop(self) -> bool:
        return bool(self.flag & 1)


@dataclass
class SmfInfo:
    format: int
    tracks: int
    division: int
    loop_tick: Optional[int]
    end_tick: int


def parse(raw: bytes) -> List[Song]:
    if not raw:
        raise NotMlk("빈 파일")
    n = raw[0]
    if n == 0:
        raise NotMlk("곡 수 0")
    table_end = 1 + ENTRY * n
    if table_end > len(raw):
        raise NotMlk("항목 표가 파일보다 김")
    songs = []
    for i in range(n):
        flag = raw[1 + i * ENTRY]
        offset, size = struct.unpack_from("<II", raw, 2 + i * ENTRY)
        if offset < table_end or size < 14 or offset + size > len(raw):
            raise NotMlk(f"{i}번 항목이 파일 밖을 가리킴")
        if raw[offset:offset + 4] != b"MThd":
            raise NotMlk(f"{i}번 항목이 SMF가 아님")
        songs.append(Song(i, flag, offset, size, raw[offset:offset + size]))
    return songs


def _vlq(d: bytes, i: int):
    v = 0
    while True:
        b = d[i]
        i += 1
        v = (v << 7) | (b & 0x7F)
        if b < 0x80:
            return v, i


def smf_info(smf: bytes) -> SmfInfo:
    """분해능·반복 틱·끝 틱. 반복 마커는 길이 2인 `FF 59`/`FF 58` (마지막 것이 이긴다)."""
    header_len = struct.unpack_from(">I", smf, 4)[0]
    fmt, tracks, division = struct.unpack_from(">HHH", smf, 8)
    p = 8 + header_len
    loop_tick = None
    end_tick = 0
    for _ in range(tracks):
        length = struct.unpack_from(">I", smf, p + 4)[0]
        track = smf[p + 8:p + 8 + length]
        p += 8 + length
        i = tick = running = 0
        while i < len(track):
            dt, i = _vlq(track, i)
            tick += dt
            status = track[i]
            if status == 0xFF:
                kind = track[i + 1]
                ln, j = _vlq(track, i + 2)
                i = j + ln
                if kind in (0x59, 0x58) and ln == 2:
                    loop_tick = tick
                elif kind == 0x2F:
                    end_tick = max(end_tick, tick)
                    break
            elif status in (0xF0, 0xF7):
                ln, j = _vlq(track, i + 1)
                i = j + ln
            else:
                if status & 0x80:
                    running = status
                    i += 1
                i += 1 if (running >> 4) in (0xC, 0xD) else 2
    return SmfInfo(fmt, tracks, division, loop_tick, end_tick)
