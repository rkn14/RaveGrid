"""Implémentation OpenCV de FrameSource."""

from __future__ import annotations

import cv2
import numpy as np

from ..config.schema import CameraConfig

# CAP_ANY = 0 : OpenCV choisit le meilleur backend disponible (MSMF, V4L2, etc.)
_BACKEND: int = cv2.CAP_ANY


class OpenCvCamera:
    """Caméra physique ou fichier vidéo via OpenCV."""

    def __init__(self, config: CameraConfig) -> None:
        self._cap = cv2.VideoCapture(config.index, _BACKEND)
        if self._cap.isOpened():
            self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.width)
            self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.height)

    def read(self) -> tuple[bool, np.ndarray]:
        return self._cap.read()

    def release(self) -> None:
        self._cap.release()

    @property
    def is_opened(self) -> bool:
        return self._cap.isOpened()

    def __enter__(self) -> OpenCvCamera:
        return self

    def __exit__(self, *_: object) -> None:
        self.release()
