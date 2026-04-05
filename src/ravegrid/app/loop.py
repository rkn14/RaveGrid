"""Boucle principale de l'application : acquisition → vision → affichage."""

from __future__ import annotations

import dataclasses
import logging

from ..capture.camera import OpenCvCamera
from ..config.schema import AppConfig
from ..ui.annotator import draw_markers
from ..ui.pygame_display import PygameDisplay
from ..vision.board_detector import BoardDetector

logger = logging.getLogger(__name__)


class AppLoop:
    """Orchestre la caméra, la détection ArUco et l'affichage."""

    def __init__(self, config: AppConfig, camera_index: int) -> None:
        self._config = config
        self._camera_index = camera_index

    def run(self) -> None:
        detector = BoardDetector(self._config.aruco)
        cam_config = dataclasses.replace(self._config.camera, index=self._camera_index)

        with OpenCvCamera(cam_config) as camera:
            if not camera.is_opened:
                logger.error("Impossible d'ouvrir la caméra %d", self._camera_index)
                return

            with PygameDisplay(self._config.window) as display:
                running = True
                while running:
                    ok, frame = camera.read()
                    if not ok:
                        logger.warning("Frame vide reçue — lecture ignorée")
                        continue

                    markers = detector.detect(frame)
                    annotated = draw_markers(frame, markers)

                    display.show(annotated)
                    running = display.handle_events()
