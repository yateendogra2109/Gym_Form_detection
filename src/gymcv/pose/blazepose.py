from __future__ import annotations

import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from gymcv.pose.pose_landmark import PoseLandmark

_MODEL_DIR = Path(__file__).resolve().parent / "models"
_MODEL_FILE = _MODEL_DIR / "pose_landmarker_lite.task"
_MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task"
)


def _ensure_task_model() -> Path:
    _MODEL_DIR.mkdir(parents=True, exist_ok=True)
    if not _MODEL_FILE.exists():
        urllib.request.urlretrieve(_MODEL_URL, _MODEL_FILE)
    return _MODEL_FILE


@dataclass
class _Lm:
    x: float
    y: float
    z: float
    visibility: float


class _LandmarkListShim:
    __slots__ = ("landmark",)

    def __init__(self, landmark: list[_Lm]) -> None:
        self.landmark = landmark


@dataclass
class _ProcessResultShim:
    pose_landmarks: _LandmarkListShim | None


class BlazePoseEstimator:
    """
    Pose estimation via MediaPipe BlazePose.
    Uses legacy `mp.solutions.pose` when available; otherwise Tasks API (Python 3.12+ wheels).
    """

    def __init__(self) -> None:
        import mediapipe as mp

        self._mp = mp
        if hasattr(mp, "solutions"):
            self._mode = "solutions"
            self._mp_pose = mp.solutions.pose
            self._pose = self._mp_pose.Pose(
                static_image_mode=False,
                model_complexity=1,
                enable_segmentation=False,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5,
            )
            self._drawer = mp.solutions.drawing_utils
            self._ts_ms = 0
        else:
            self._mode = "tasks"
            from mediapipe.tasks.python import BaseOptions
            from mediapipe.tasks.python.vision import PoseLandmarker, PoseLandmarkerOptions, RunningMode

            model_path = str(_ensure_task_model())
            opts = PoseLandmarkerOptions(
                base_options=BaseOptions(model_asset_path=model_path),
                running_mode=RunningMode.VIDEO,
                num_poses=1,
                min_pose_detection_confidence=0.5,
                min_pose_presence_confidence=0.5,
                min_tracking_confidence=0.5,
                output_segmentation_masks=False,
            )
            self._landmarker = PoseLandmarker.create_from_options(opts)
            from mediapipe.tasks.python.vision import pose_landmarker as plm

            self._pose_connections = plm.PoseLandmarksConnections.POSE_LANDMARKS
            self._ts_ms = 0

    @property
    def landmarks_enum(self) -> type[PoseLandmark]:
        return PoseLandmark

    def process(self, frame_bgr: np.ndarray) -> Any:
        if self._mode == "solutions":
            frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            return self._pose.process(frame_rgb)

        from mediapipe import Image, ImageFormat

        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        self._ts_ms += 33
        mp_image = Image(image_format=ImageFormat.SRGB, data=rgb)
        out = self._landmarker.detect_for_video(mp_image, self._ts_ms)
        if not out.pose_landmarks:
            return _ProcessResultShim(None)
        raw = out.pose_landmarks[0]
        landmark = [
            _Lm(
                x=float(p.x),
                y=float(p.y),
                z=float(p.z) if p.z is not None else 0.0,
                visibility=float(p.visibility) if p.visibility is not None else 1.0,
            )
            for p in raw
        ]
        return _ProcessResultShim(_LandmarkListShim(landmark))

    def draw(self, frame_bgr: np.ndarray, pose_landmarks: Any) -> None:
        if pose_landmarks is None:
            return
        if self._mode == "solutions":
            self._drawer.draw_landmarks(
                frame_bgr,
                pose_landmarks,
                self._mp_pose.POSE_CONNECTIONS,
            )
            return

        h, w = frame_bgr.shape[:2]
        pts = pose_landmarks.landmark
        for conn in self._pose_connections:
            a, b = pts[conn.start], pts[conn.end]
            if a.visibility < 0.5 or b.visibility < 0.5:
                continue
            p1 = (int(a.x * w), int(a.y * h))
            p2 = (int(b.x * w), int(b.y * h))
            cv2.line(frame_bgr, p1, p2, (88, 168, 255), 2)
        for p in pts:
            if p.visibility < 0.5:
                continue
            cx, cy = int(p.x * w), int(p.y * h)
            cv2.circle(frame_bgr, (cx, cy), 3, (0, 255, 0), -1)

    def close(self) -> None:
        if self._mode == "tasks" and hasattr(self, "_landmarker"):
            self._landmarker.close()
        elif self._mode == "solutions" and hasattr(self, "_pose"):
            self._pose.close()
