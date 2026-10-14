"""실제 게임 파일로 회귀 해시를 만든다 (게임 데이터는 저장소에 넣지 않는다).

    python tests/make_manifest.py <corpus 폴더>

corpus 폴더 아래 아무 곳에나 MLK·WLK를 두면 된다(`kaisin/SMASH.MLK` 식). 출력이 *의도적으로*
바뀔 때만 다시 만든다.
"""
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from compileaudio import extract as ex

MANIFEST = os.path.join(os.path.dirname(__file__), "vectors", "corpus.json")


def hashes(corpus):
    out = {}
    for r in ex.scan(corpus):
        if r.status != ex.OK:
            continue
        for name, data in r.outputs.items():
            out[f"{r.source}#{name}"] = hashlib.sha256(data).hexdigest()
    return out


if __name__ == "__main__":
    table = hashes(sys.argv[1])
    with open(MANIFEST, "w", encoding="utf-8") as f:
        f.write("{\n" + ",\n".join(f"{json.dumps(k)}: {json.dumps(v)}" for k, v in sorted(table.items())) + "\n}\n")
    print(len(table), "entries ->", MANIFEST)
