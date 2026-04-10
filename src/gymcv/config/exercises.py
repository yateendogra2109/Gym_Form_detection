from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExerciseConfig:
    name: str
    primary_side: str
    top_angle: float
    bottom_angle: float
    smoothing_window: int
    visibility_threshold: float
    ideal_bottom_min: float
    ideal_bottom_max: float
    ideal_top_min: float
    ideal_top_max: float
    symmetry_enabled: bool
    fatigue_rom_drop_pct: float = 0.15
    fatigue_velocity_drop_pct: float = 0.20
    # Guard rails: if the peak angle during a rep EXCEEDS max_angle_guard the rep is
    # rejected (prevents shoulder-press ROM from triggering lateral-raise counts).
    # If the peak angle NEVER reaches min_angle_guard the rep is also rejected
    # (prevents small drifts from triggering exercises that need large ROM).
    max_angle_guard: float | None = None  # cap: discard rep if peak > this
    min_angle_guard: float | None = None  # floor: discard rep if peak < this


SUPPORTED_EXERCISES: dict[str, ExerciseConfig] = {
    "bicep_curl": ExerciseConfig(
        name="bicep_curl",
        primary_side="right",
        top_angle=50.0,
        bottom_angle=150.0,
        smoothing_window=5,
        visibility_threshold=0.5,
        ideal_bottom_min=145.0,
        ideal_bottom_max=175.0,
        ideal_top_min=35.0,
        ideal_top_max=70.0,
        symmetry_enabled=False,
    ),
    "squat": ExerciseConfig(
        name="squat",
        primary_side="right",
        top_angle=95.0,
        bottom_angle=165.0,
        smoothing_window=5,
        visibility_threshold=0.5,
        ideal_bottom_min=80.0,
        ideal_bottom_max=105.0,
        ideal_top_min=155.0,
        ideal_top_max=180.0,
        symmetry_enabled=True,
    ),
    "push_up": ExerciseConfig(
        name="push_up",
        primary_side="right",
        top_angle=80.0,
        bottom_angle=165.0,
        smoothing_window=5,
        visibility_threshold=0.5,
        ideal_bottom_min=75.0,
        ideal_bottom_max=100.0,
        ideal_top_min=150.0,
        ideal_top_max=180.0,
        symmetry_enabled=False,
    ),
    "shoulder_press": ExerciseConfig(
        # Angle = HIP→SHOULDER→ELBOW (shoulder elevation).
        # Arms at sides (rest) ≈ 20-30°; fully pressed overhead ≈ 155-170°.
        # FSM: 'up' when smoothed >= top_angle (arm overhead), 'down' when <= bottom_angle.
        name="shoulder_press",
        primary_side="right",
        top_angle=140.0,      # arm is 'up' (overhead) when angle >= 140°
        bottom_angle=50.0,    # arm is 'down' (at sides) when angle <= 50°
        smoothing_window=5,
        visibility_threshold=0.5,
        ideal_bottom_min=15.0,
        ideal_bottom_max=55.0,
        ideal_top_min=140.0,
        ideal_top_max=180.0,
        symmetry_enabled=True,
        # Must reach at least 130° to confirm arm went overhead (blocks bicep curl drift).
        min_angle_guard=130.0,
    ),
    "lateral_raise": ExerciseConfig(
        # Angle = HIP→SHOULDER→ELBOW (arm elevation from torso side).
        # Arm at sides (rest) ≈ 15-30°;  arm raised to horizontal ≈ 85-100°.
        # Lateral raises NEVER go overhead (>120°) — unlike shoulder press.
        # FSM uses inverted semantics here:
        #   'up'   = small angle (arm back at side, ≤ top_angle=30°)
        #   'down' = large angle (arm raised to horizontal, ≥ bottom_angle=75°)
        # A rep is complete when we cycle: up→down→up.
        name="lateral_raise",
        primary_side="right",
        top_angle=30.0,       # arm 'at rest' when angle <= 30° (arm at side)
        bottom_angle=75.0,    # rep peaks when angle >= 75° (arm at horizontal)
        smoothing_window=5,
        visibility_threshold=0.5,
        ideal_bottom_min=70.0,
        ideal_bottom_max=100.0,
        ideal_top_min=10.0,
        ideal_top_max=35.0,
        symmetry_enabled=True,
        # Discard rep if arm went above 120° — that's a shoulder press, not a lateral raise.
        max_angle_guard=120.0,
    ),
}

# Human-readable labels for Streamlit / overlays (stable order for dropdowns).
EXERCISE_UI_ORDER: tuple[str, ...] = (
    "bicep_curl",
    "squat",
    "push_up",
    "shoulder_press",
    "lateral_raise",
)

EXERCISE_LABELS: dict[str, str] = {
    "bicep_curl": "Bicep curl",
    "squat": "Squat",
    "push_up": "Push-up",
    "shoulder_press": "Shoulder press",
    "lateral_raise": "Lateral raise",
}


def exercise_select_options() -> list[tuple[str, str]]:
    """Return (config_key, display_label) pairs for UI widgets."""
    return [(k, EXERCISE_LABELS.get(k, k)) for k in EXERCISE_UI_ORDER if k in SUPPORTED_EXERCISES]
