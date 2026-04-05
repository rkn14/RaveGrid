"""Boucle principale de l'application : acquisition → affichage."""

from __future__ import annotations

import dataclasses
import logging

from ..capture.camera import OpenCvCamera
from ..config.schema import AppConfig
from ..ui.pygame_display import PygameDisplay

logger = logging.getLogger(__name__)


class AppLoop:
    """Orchestre la caméra et l'affichage jusqu'à l'arrêt demandé par l'utilisateur."""

    def __init__(self, config: AppConfig, camera_index: int) -> None:
        self._config = config
        self._camera_index = camera_index

    def run(self) -> None:
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
                    display.show(frame)
                    running = display.handle_events()
