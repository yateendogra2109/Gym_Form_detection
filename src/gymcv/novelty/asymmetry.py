from __future__ import annotations


class AsymmetryScorer:
    def __init__(self, alert_threshold: float = 20.0) -> None:
        self.alert_threshold = alert_threshold
        self.prev_score = None

    def score(self, left_angle: float | None, right_angle: float | None):
        if left_angle is None or right_angle is None:
            return None, False

        diff = abs(left_angle - right_angle)

        # ✅ Use raw difference (degrees)
        score = diff

        # ✅ Light smoothing
        if self.prev_score is None:
            smoothed = score
        else:
            smoothed = 0.6 * self.prev_score + 0.4 * score

        self.prev_score = smoothed

        alert = smoothed > self.alert_threshold

        return smoothed, alert