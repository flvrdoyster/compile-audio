"""폴더나 파일에서 MLK·WLK를 판별해 곡(.mid)과 효과음(.wav)으로 푼다.

묶음 파일 하나당 출력 폴더 안에 그 파일 이름(상대 경로)의 폴더가 하나 생기고, 번호는 컨테이너
안의 0부터 순번이다.

    <출력>/SMASH.MLK/bgm_00.mid … index.json
    <출력>/GENSEI.WLK/se_00.wav … index.json
"""
import json
import os
from dataclasses import dataclass, field
from typing import Dict, Iterator

from . import mlk, wlk
from .detect import NotAudio, load
from .wav import to_wav

OK, SKIPPED, UNKNOWN = "변환", "건너뜀", "판별 불가"
MAX_SIZE = 32 * 1024 * 1024      # 디스크 이미지 같은 큰 파일은 열어 보지 않음


@dataclass
class Result:
    source: str
    status: str
    kind: str = ""
    variant: str = ""
    note: str = ""
    outputs: Dict[str, bytes] = field(default_factory=dict)
    index: dict = field(default_factory=dict)


def _from_mlk(songs) -> Result:
    outputs, entries = {}, []
    for s in songs:
        name = f"bgm_{s.index:02d}.mid"
        info = mlk.smf_info(s.data)
        outputs[name] = s.data
        entries.append({"file": name, "flag": s.flag, "loop": s.loop, "division": info.division,
                        "loopTick": info.loop_tick, "endTick": info.end_tick})
    return Result("", OK, "mlk", "", f"곡 {len(songs)}", outputs, {"kind": "mlk", "songs": entries})


def _from_wlk(w: wlk.Wlk) -> Result:
    outputs, entries = {}, []
    for s in w.samples:
        name = f"se_{s.index:02d}.wav"
        outputs[name] = to_wav(s.data, s.channels, s.rate, s.bits)
        e = {"file": name, "b0": s.flag, "format": s.format, "rate": s.rate, "bits": s.bits,
             "channels": s.channels, "frames": s.frames}
        if s.extra:
            e["extra"] = list(s.extra)
        entries.append(e)
    index = {"kind": "wlk", "variant": w.variant, "samples": entries}
    return Result("", OK, "wlk", w.variant, f"효과음 {len(w.samples)}", outputs, index)


def examine(path: str, rel: str = "") -> Result:
    rel = rel or os.path.basename(path)
    size = os.path.getsize(path)
    if size == 0 or size > MAX_SIZE:
        return Result(rel, SKIPPED, note="비었거나 너무 큼")
    try:
        kind, parsed = load(open(path, "rb").read())
    except NotAudio as e:
        return Result(rel, UNKNOWN, note=str(e))
    r = _from_mlk(parsed) if kind == "mlk" else _from_wlk(parsed)
    r.source = rel
    return r


def scan(src: str) -> Iterator[Result]:
    if os.path.isfile(src):
        yield examine(src)
        return
    for dirpath, _, names in sorted(os.walk(src)):
        for fn in sorted(names):
            if fn.startswith("."):
                continue
            full = os.path.join(dirpath, fn)
            yield examine(full, os.path.relpath(full, src))


def save(result: Result, dest: str) -> str:
    folder = os.path.join(dest, result.source)
    os.makedirs(folder, exist_ok=True)
    for name, data in result.outputs.items():
        with open(os.path.join(folder, name), "wb") as f:
            f.write(data)
    with open(os.path.join(folder, "index.json"), "w", encoding="utf-8") as f:
        json.dump(result.index, f, ensure_ascii=False, indent=1)
    return folder
