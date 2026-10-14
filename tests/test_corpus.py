"""실제 게임 파일에 대한 회귀 -- 해시만 비교, 데이터는 커밋하지 않는다.

COMPILE_AUDIO_CORPUS를 MLK·WLK가 들어 있는 폴더로 지정하면 돌고, 없으면 건너뜀.
`make_manifest.py`로 만든 값과 하나라도 다르면 실패한다.
"""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
from make_manifest import MANIFEST, hashes

CORPUS = os.environ.get("COMPILE_AUDIO_CORPUS")


@pytest.mark.skipif(not CORPUS, reason="set COMPILE_AUDIO_CORPUS to run")
def test_corpus_matches_manifest():
    manifest = json.load(open(MANIFEST, encoding="utf-8"))
    got = hashes(CORPUS)
    checked = [k for k in manifest if k in got]
    assert checked, "manifest matched no files -- wrong corpus path?"
    bad = [k for k in checked if got[k] != manifest[k]]
    assert not bad, f"{len(bad)}/{len(checked)} outputs differ: {bad[:5]}"
