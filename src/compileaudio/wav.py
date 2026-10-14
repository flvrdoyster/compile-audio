"""PCM → WAV. 8비트는 부호 없는 형식 그대로(WAV 표준과 같음), 16비트는 부호 있는 LE."""
import struct


def to_wav(pcm: bytes, channels: int, rate: int, bits: int) -> bytes:
    block = channels * bits // 8
    return (b"RIFF" + struct.pack("<I", 36 + len(pcm)) + b"WAVE"
            + b"fmt " + struct.pack("<IHHIIHH", 16, 1, channels, rate, rate * block, block, bits)
            + b"data" + struct.pack("<I", len(pcm)) + pcm)
