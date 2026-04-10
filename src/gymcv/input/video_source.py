from __future__ import annotations

import cv2


class VideoSource:
    def __init__(self, source: int | str = 0, width: int = 640, height: int = 480) -> None:
        self.cap = cv2.VideoCapture(source)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    def read(self):
        return self.cap.read()

    def release(self) -> None:
        self.cap.release()

