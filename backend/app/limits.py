from dataclasses import dataclass
from math import isfinite
from time import monotonic


class AnalysisTimeout(TimeoutError):
    """The shared collection/detection time budget has expired."""


class AnalysisCancelled(AnalysisTimeout):
    """A cooperative user cancellation, preserving fully analyzed documents."""


@dataclass(frozen=True)
class Deadline:
    expires_at: float
    cancel_event: object = None

    @classmethod
    def after(cls, seconds: float, cancel_event=None):
        if not isfinite(seconds) or seconds <= 0:
            raise ValueError("Time budget must be finite and positive")
        return cls(monotonic() + seconds, cancel_event)

    @property
    def cancelled(self):
        return self.cancel_event is not None and self.cancel_event.is_set()

    def remaining(self) -> float:
        if self.cancelled:
            raise AnalysisCancelled('사용자가 분석 중단을 요청했습니다.')
        remaining = self.expires_at - monotonic()
        if remaining <= 0:
            raise AnalysisTimeout("분석 시간 제한에 도달했습니다.")
        return remaining

    def check(self):
        self.remaining()
