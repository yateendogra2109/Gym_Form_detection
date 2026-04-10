from __future__ import annotations


class AsymmetryScorer:
    """Simple left-right angle asymmetry detector.

    score = abs(left_angle - right_angle) in degrees.
      - 0   → perfect symmetry (identical on both sides)
      - high → large asymmetry

    alert fires when score exceeds alert_threshold_deg.
    """

    def __init__(self, alert_threshold_deg: float = 15.0) -> None:
        self.alert_threshold_deg = alert_threshold_deg

    def score(self, left_angle: float | None, right_angle: float | None) -> tuple[float | None, bool]:
        if left_angle is None or right_angle is None:
            return None, False
        diff = abs(left_angle - right_angle)
        alert = diff > self.alert_threshold_deg
        return diff, alert


