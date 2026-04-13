from __future__ import annotations

import cv2
import numpy as np

PANEL_W = 320  # slightly wider to fit "HIGH" alert text


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
    """Append a dark stats panel on the RIGHT of *frame* and return the combined image."""
    h = frame.shape[0]
    panel = np.full((h, PANEL_W, 3), (30, 30, 30), dtype=np.uint8)

    cv2.line(panel, (0, 0), (0, h), (80, 80, 80), 2)

    font = cv2.FONT_HERSHEY_SIMPLEX
    x = 12

    cv2.putText(panel, f"FPS: {fps:.1f}", (x, 30), font, 0.75, (0, 220, 220), 2)
    cv2.line(panel, (x, 42), (PANEL_W - x, 42), (60, 60, 60), 1)

    cv2.putText(panel, exercise, (x, 68), font, 0.72, (255, 255, 255), 2)
    cv2.putText(panel, f"Reps: {rep_count}", (x, 100), font, 0.85, (50, 220, 50), 2)
    cv2.putText(panel, f"Stage: {stage}", (x, 132), font, 0.72, (200, 200, 200), 2)

    cv2.line(panel, (x, 148), (PANEL_W - x, 148), (60, 60, 60), 1)

    cv2.putText(panel, f"Angle: {angle:.1f}", (x, 174), font, 0.7, (255, 230, 0), 2)
    cv2.putText(panel, f"Form:  {form_score:.1f}", (x, 204), font, 0.7, (255, 180, 0), 2)
    cv2.putText(panel, f"XP:    {xp}", (x, 234), font, 0.7, (180, 255, 255), 2)

    # ── Asymmetry row ──────────────────────────────────────────────────────────
    if asymmetry_score is None:
        # No data yet — show grey placeholder
        cv2.putText(panel, "Asym: --", (x, 264), font, 0.65, (120, 120, 120), 2)
    else:
        asym_color = (0, 0, 255) if asym_alert else (50, 220, 50)
        cv2.putText(
            panel,
            f"Asym: {asymmetry_score:.1f}",
            (x, 264),
            font,
            0.65,
            asym_color,
            2,
        )

        if asym_alert:
            # ⚠ "Asymmetry HIGH" in red on the next line for visibility
            cv2.putText(
                panel,
                "! Asymmetry HIGH",
                (x, 290),
                font,
                0.62,
                (0, 60, 255),
                2,
            )

    # ── Fatigue row ────────────────────────────────────────────────────────────
    fatigue_y = 320 if asym_alert else 294
    if fatigue_flag:
        cv2.putText(panel, "! Fatigue", (x, fatigue_y), font, 0.7, (0, 100, 255), 2)

    combined = np.hstack([frame, panel])
    return combined