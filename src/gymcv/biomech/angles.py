from __future__ import annotations

from collections.abc import Iterable
import math

import numpy as np


def calculate_angle_2d(a: Iterable[float], b: Iterable[float], c: Iterable[float]) -> float:
    a_np = np.array(list(a), dtype=float)
    b_np = np.array(list(b), dtype=float)
    c_np = np.array(list(c), dtype=float)

    radians = math.atan2(c_np[1] - b_np[1], c_np[0] - b_np[0]) - math.atan2(
        a_np[1] - b_np[1], a_np[0] - b_np[0]
    )
    angle = abs(math.degrees(radians))
    if angle > 180.0:
        angle = 360.0 - angle
    return angle

