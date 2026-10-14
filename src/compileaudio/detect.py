"""파일 내용으로 형식을 판별한다 (확장자는 보지 않음)."""
from typing import Tuple, Union

from . import mlk, wlk


class NotAudio(ValueError):
    pass


def load(raw: bytes) -> Tuple[str, Union[list, wlk.Wlk]]:
    """("mlk", [Song, ...]) 또는 ("wlk", Wlk). 둘 다 아니면 NotAudio."""
    reasons = []
    try:
        return "mlk", mlk.parse(raw)
    except mlk.NotMlk as e:
        reasons.append(f"MLK 아님({e})")
    try:
        return "wlk", wlk.parse(raw)
    except wlk.NotWlk as e:
        reasons.append(f"WLK 아님({e})")
    raise NotAudio("; ".join(reasons))
