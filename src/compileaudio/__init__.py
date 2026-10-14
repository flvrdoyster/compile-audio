"""compile-audio -- decoders for Compile's Windows-era audio containers.

Extraction only. 곡(MLK → 표준 MIDI)과 효과음(WLK → WAV)을 묶음에서 꺼낸다. 재삽입과
렌더링(MIDI → 음원)은 각 프로젝트가 따로 한다.

    from compileaudio import load
    kind, parsed = load(open("SMASH.MLK", "rb").read())
"""
from .detect import NotAudio, load

__all__ = ["NotAudio", "load"]
__version__ = "0.1.0"
