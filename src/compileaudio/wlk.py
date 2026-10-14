"""WLK -- Compile Windows 게임의 효과음(PCM) 묶음. 두 변종이 있다.

헤더 없는 형 (환세쾌진극 `GENSEI.WLK`)
    [u16le 개수-1]
    N x { u8 b0, u8 형식, u32le 오프셋, u32le 크기, u32le 샘플레이트 }     (14바이트)
    ... PCM ...

`WLKF0200` 형 (취호전 `PCMDATA.WLK`)
    "WLKF0200", u32le 개수 N
    N x { 위의 14바이트, i32le 두 개 }                                       (22바이트)
    ... PCM ...
    덧붙은 8바이트는 -500·-700·-1200 같은 값이 많아 DirectSound식 감쇠(1/100dB)로 보이나
    미확인이라 값 그대로 `extra`에 둔다. 항목 크기는 첫 오프셋에서 거꾸로 구한다.

형식 바이트: 비트 7 = 16비트(아니면 8비트 부호 없음), 비트 6 = 스테레오(실제 파일엔 없음).
비트 5(0x20)도 취호전 4개에 서 있으나 뜻 미확인. PCM은 가공 없이
이어 붙어 있고 데이터는 표 바로 뒤에서 시작해 파일 끝에서 끝난다(두 변종 다 확인).
"""
import struct
from dataclasses import dataclass
from typing import List, Tuple

MAGIC = b"WLKF0200"
BASE = 14


class NotWlk(ValueError):
    pass


@dataclass
class Sample:
    index: int
    flag: int            # b0. 환세쾌진극은 전부 0, 취호전은 전부 255
    format: int
    offset: int
    size: int
    rate: int
    extra: Tuple[int, ...]
    data: bytes

    @property
    def bits(self) -> int:
        return 16 if self.format & 0x80 else 8

    @property
    def channels(self) -> int:
        return 2 if self.format & 0x40 else 1

    @property
    def frames(self) -> int:
        return self.size // (self.bits // 8 * self.channels)


@dataclass
class Wlk:
    variant: str         # "headerless" | "WLKF0200"
    samples: List[Sample]
    trailing: int        # 마지막 샘플 뒤에 남은 바이트


def _read(raw: bytes, variant: str, count: int, table: int, entry: int) -> Wlk:
    table_end = table + entry * count
    if count == 0 or entry < BASE or table_end > len(raw):
        raise NotWlk("항목 표가 맞지 않음")
    samples = []
    prev_end = table_end
    for i in range(count):
        p = table + i * entry
        flag, fmt = raw[p], raw[p + 1]
        offset, size, rate = struct.unpack_from("<III", raw, p + 2)
        if not 1000 <= rate <= 192000:
            raise NotWlk(f"{i}번 샘플레이트 {rate}")
        if offset < prev_end or offset + size > len(raw):
            raise NotWlk(f"{i}번이 겹치거나 파일 밖을 가리킴")
        frame = (2 if fmt & 0x80 else 1) * (2 if fmt & 0x40 else 1)
        if size % frame:
            raise NotWlk(f"{i}번 크기가 프레임 단위가 아님")
        n_extra = (entry - BASE) // 4
        extra = struct.unpack_from(f"<{n_extra}i", raw, p + BASE) if n_extra else ()
        samples.append(Sample(i, flag, fmt, offset, size, rate, extra, raw[offset:offset + size]))
        prev_end = offset + size
    return Wlk(variant, samples, len(raw) - prev_end)


def parse(raw: bytes) -> Wlk:
    if raw[:8] == MAGIC:
        if len(raw) < 12 + BASE:
            raise NotWlk("WLKF0200 헤더가 잘림")
        count = struct.unpack_from("<I", raw, 8)[0]
        if count == 0 or 12 + BASE > len(raw):
            raise NotWlk("개수 0")
        first = struct.unpack_from("<I", raw, 12 + 2)[0]
        span = first - 12
        if span <= 0 or span % count:
            raise NotWlk("첫 오프셋에서 항목 크기가 나누어떨어지지 않음")
        return _read(raw, "WLKF0200", count, 12, span // count)
    if len(raw) < 2 + BASE:
        raise NotWlk("너무 짧음")
    count = struct.unpack_from("<H", raw, 0)[0] + 1
    return _read(raw, "headerless", count, 2, BASE)
