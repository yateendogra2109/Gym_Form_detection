from __future__ import annotations

from collections import deque


class RepCounterFSM:
    def __init__(
        self,
        top_angle: float,
        bottom_angle: float,
        smoothing_window: int = 5,
        max_angle_guard: float | None = None,
        min_angle_guard: float | None = None,
    ) -> None:
        self.top_angle = top_angle
        self.bottom_angle = bottom_angle
        self.stage = "down"
        self.count = 0
        self._history: deque[float] = deque(maxlen=smoothing_window)
        self.last_angle = 0.0
        self.in_concentric = False
        # Guards: discard a rep if the peak angle during that rep violates bounds.
        # max_angle_guard – reject if peak EXCEEDS this (e.g. lateral raise ≤ 120°)
        # min_angle_guard – reject if peak NEVER reached this (e.g. shoulder press ≥ 130°)
        self._max_angle_guard = max_angle_guard
        self._min_angle_guard = min_angle_guard
        self._rep_peak: float = 0.0  # highest angle seen since entering "up" stage

    def update(self, angle: float) -> tuple[int, str, float, bool]:
        self._history.append(angle)
        smoothed = sum(self._history) / len(self._history)
        self.last_angle = smoothed
        rep_completed = False

        if smoothed <= self.top_angle and self.stage == "down":
            # Entering "up" position – reset peak tracker for this new rep attempt.
            self.stage = "up"
            self.in_concentric = False
            self._rep_peak = smoothed
        elif smoothed >= self.bottom_angle and self.stage == "up":
            # Rep would complete – check guards before accepting it.
            valid = True
            if self._max_angle_guard is not None and self._rep_peak > self._max_angle_guard:
                valid = False  # arm went too high (e.g. shoulder press triggering lateral raise)
            if self._min_angle_guard is not None and self._rep_peak < self._min_angle_guard:
                valid = False  # arm didn't reach required height (e.g. small drift on shoulder press)

            self.stage = "down"
            self.in_concentric = True
            if valid:
                self.count += 1
                rep_completed = True
            self._rep_peak = 0.0
        else:
            self.in_concentric = self.stage == "up"
            if self.stage == "up":
                self._rep_peak = max(self._rep_peak, smoothed)

        return self.count, self.stage, smoothed, rep_completed

