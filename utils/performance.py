"""Rolling delivered-frame telemetry."""
from collections import deque
from time import perf_counter

class FrameMeter:
    def __init__(self) -> None:
        self.intervals: deque[float] = deque(maxlen=90)
        self.last = perf_counter()

    def frame(self) -> None:
        now = perf_counter()
        self.intervals.append(now-self.last)
        self.last = now

    @property
    def fps(self) -> float:
        return len(self.intervals)/sum(self.intervals) if self.intervals else 0
