from __future__ import annotations

import cv2
import numpy as np

PANEL_W = 300  # width of the right-side stats panel in pixels


def draw_stats(
    frame,
    rep_count: int,
    stage: str,
    angle: float,
    fps: float,
    exercise: str,
    form_score: float,
    asymmetry_score: float | None,
    fatigue_flag: bool,
    xp: int,
    asym_alert: bool = False,
):
    """Append a dark stats panel on the RIGHT of *frame* and return the combined image.

    The original *frame* is NOT modified — a new wider array is returned.
    Callers must use the returned value for imshow / further processing.
    """
    h = frame.shape[0]
    panel = np.full((h, PANEL_W, 3), (30, 30, 30), dtype=np.uint8)

    # Thin accent line separating panel from camera
    cv2.line(panel, (0, 0), (0, h), (80, 80, 80), 2)

    font = cv2.FONT_HERSHEY_SIMPLEX
    x = 12  # left margin inside the panel

    # FPS – top right accent
    cv2.putText(panel, f"FPS: {fps:.1f}", (x, 30), font, 0.75, (0, 220, 220), 2)

    # Divider
    cv2.line(panel, (x, 42), (PANEL_W - x, 42), (60, 60, 60), 1)

    cv2.putText(panel, exercise, (x, 68), font, 0.72, (255, 255, 255), 2)
    cv2.putText(panel, f"Reps: {rep_count}", (x, 100), font, 0.85, (50, 220, 50), 2)
    cv2.putText(panel, f"Stage: {stage}", (x, 132), font, 0.72, (200, 200, 200), 2)

    # Divider
    cv2.line(panel, (x, 148), (PANEL_W - x, 148), (60, 60, 60), 1)

    cv2.putText(panel, f"Angle: {angle:.1f}", (x, 174), font, 0.7, (255, 230, 0), 2)
    cv2.putText(panel, f"Form:  {form_score:.1f}", (x, 204), font, 0.7, (255, 180, 0), 2)
    cv2.putText(panel, f"XP:    {xp}", (x, 234), font, 0.7, (180, 255, 255), 2)

    if asymmetry_score is not None:
        color = (0, 200, 80) if not asym_alert else (30, 80, 255)
        cv2.putText(panel, f"Asym diff: {asymmetry_score:.1f}\u00b0", (x, 264), font, 0.62, color, 2)
        if asym_alert:
            cv2.putText(panel, "Asymmetry High!", (x, 284), font, 0.58, (0, 80, 255), 2)

    if fatigue_flag:
        cv2.putText(panel, "! Fatigue", (x, 294), font, 0.7, (0, 100, 255), 2)

    combined = np.hstack([frame, panel])
    return combined

