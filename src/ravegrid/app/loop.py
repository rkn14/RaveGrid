"""Boucle principale de l'application : acquisition → vision → affichage."""

from __future__ import annotations

import dataclasses
import logging

from ..capture.camera import OpenCvCamera
from ..config.schema import AppConfig
from ..domain.board import BoardCorners
from ..ui.annotator import draw_cell_colors, draw_grid, draw_markers
from ..ui.pygame_display import PygameDisplay
from ..vision.board_detector import BoardDetector
from ..vision.cell_classifier import CellClassifier
from ..vision.grid_splitter import GridSplitter
from ..vision.rectifier import RectificationResult, Rectifier

logger = logging.getLogger(__name__)


class AppLoop:
    """Orchestre caméra, détection ArUco, rectification, classification et affichage."""

    def __init__(self, config: AppConfig, camera_index: int) -> None:
        self._config = config
        self._camera_index = camera_index

    def run(self) -> None:
        detector   = BoardDetector(self._config.aruco)
        rectifier  = Rectifier(self._config.grid)
        splitter   = GridSplitter(self._config.grid)
        classifier = CellClassifier(self._config.colors)
        cam_config = dataclasses.replace(self._config.camera, index=self._camera_index)

        # Dernier état persisté (maintenu en cas d'occlusion brève des marqueurs)
        last_rect:        RectificationResult | None = None
        last_grid_colors: list[list[str | None]] | None = None

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

                    # --- Vision ---
                    markers = detector.detect(frame)
                    corners = BoardCorners.from_markers(markers)

                    if corners is not None:
                        last_rect        = rectifier.compute(corners)
                        rectified        = rectifier.rectify(frame, last_rect)
                        last_grid_colors = classifier.classify_grid(rectified, splitter)

                    # --- Annotation (ordre : couleurs → grille → marqueurs) ---
                    annotated = frame.copy()
                    if last_rect is not None and last_grid_colors is not None:
                        annotated = draw_cell_colors(annotated, last_rect, last_grid_colors)
                        annotated = draw_grid(annotated, last_rect)
                    annotated = draw_markers(annotated, markers)

                    display.show(annotated)
                    running = display.handle_events()
