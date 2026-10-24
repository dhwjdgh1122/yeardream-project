from dataclasses import dataclass
from math import isfinite
from time import monotonic


class AnalysisTimeout(TimeoutError):
    """The shared collection/detection time budget has expired."""


@dataclass(frozen=True)
class Deadline:
    expires_at: float

    @classmethod
    def after(cls, seconds: float):
        if not isfinite(seconds) or seconds <= 0:
            raise ValueError("Time budget must be finite and positive")
        return cls(monotonic() + seconds)

    def remaining(self) -> float:
        remaining = self.expires_at - monotonic()
        if remaining <= 0:
            raise AnalysisTimeout("분석 시간 제한에 도달했습니다.")
        return remaining

    def check(self):
        self.remaining()
