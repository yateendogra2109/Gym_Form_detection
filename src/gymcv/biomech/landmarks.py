from __future__ import annotations

from dataclasses import dataclass

from gymcv.biomech.angles import calculate_angle_2d


@dataclass(frozen=True)
class AngleReading:
    main_angle: float
    left_angle: float | None = None
    right_angle: float | None = None


EXERCISE_JOINTS = {
    "bicep_curl": {
        "left": ("LEFT_SHOULDER", "LEFT_ELBOW", "LEFT_WRIST"),
        "right": ("RIGHT_SHOULDER", "RIGHT_ELBOW", "RIGHT_WRIST"),
    },
    "squat": {
        "left": ("LEFT_HIP", "LEFT_KNEE", "LEFT_ANKLE"),
        "right": ("RIGHT_HIP", "RIGHT_KNEE", "RIGHT_ANKLE"),
    },
    "push_up": {
        "left": ("LEFT_SHOULDER", "LEFT_ELBOW", "LEFT_WRIST"),
        "right": ("RIGHT_SHOULDER", "RIGHT_ELBOW", "RIGHT_WRIST"),
    },
    "shoulder_press": {
        "left": ("LEFT_HIP", "LEFT_SHOULDER", "LEFT_ELBOW"),
        "right": ("RIGHT_HIP", "RIGHT_SHOULDER", "RIGHT_ELBOW"),
    },
    "lateral_raise": {
        "left": ("LEFT_HIP", "LEFT_SHOULDER", "LEFT_ELBOW"),
        "right": ("RIGHT_HIP", "RIGHT_SHOULDER", "RIGHT_ELBOW"),
    },
}


def _point(landmarks, idx: int) -> tuple[float, float]:
    p = landmarks[idx]
    return p.x, p.y


def _visible(landmarks, idx: int, threshold: float) -> bool:
    return landmarks[idx].visibility > threshold


def compute_exercise_angles(
    landmarks,
    landmark_enum,
    exercise: str,
    visibility_threshold: float,
    symmetry_visibility_threshold: float = 0.0,
) -> AngleReading | None:
    """Compute joint angles for the given exercise.

    Parameters
    ----------
    visibility_threshold:
        Minimum landmark visibility for the main (rep-counting) angle.
    symmetry_visibility_threshold:
        Threshold for left/right symmetry angles. Defaults to 0.0 so that
        both sides are always computed from any detected landmark.
    """
    joints = EXERCISE_JOINTS[exercise]

    def side_angle(side: str, threshold: float) -> float | None:
        names = joints[side]
        ids = [landmark_enum[name].value for name in names]
        if not all(_visible(landmarks, i, threshold) for i in ids):
            return None
        return calculate_angle_2d(
            _point(landmarks, ids[0]),
            _point(landmarks, ids[1]),
            _point(landmarks, ids[2]),
        )

    # Main angle – strict threshold keeps rep counting reliable.
    left_strict = side_angle("left", visibility_threshold)
    right_strict = side_angle("right", visibility_threshold)
    if left_strict is None and right_strict is None:
        return None
    main = right_strict if right_strict is not None else left_strict

    # Symmetry angles – relaxed threshold so both sides are always available.
    left_sym = side_angle("left", symmetry_visibility_threshold)
    right_sym = side_angle("right", symmetry_visibility_threshold)

    if left_sym is None or right_sym is None:
        return AngleReading(main_angle=main, left_angle=None, right_angle=None)

    # ✅ FIXED: Only discard if readings are EXACTLY equal (means same landmark
    # was used for both sides — a detection bug). Do NOT discard near-equal
    # readings; those are valid low-asymmetry reps that must be reported as ~0.
    if left_sym == right_sym:
        left_sym = None
        right_sym = None

    return AngleReading(main_angle=main, left_angle=left_sym, right_angle=right_sym)