"""Détection des marqueurs ArUco du plateau."""

from __future__ import annotations

import logging

import cv2
import numpy as np

from ..config.schema import ArucoConfig
from ..domain.board import BOARD_MARKER_IDS, MarkerDetection

logger = logging.getLogger(__name__)


class BoardDetector:
    """Détecte les 4 marqueurs ArUco de coin dans une frame BGR.

    Retourne uniquement les marqueurs dont l'ID appartient à {0, 1, 2, 3}.
    Une liste vide signifie aucun marqueur trouvé ; une liste partielle
    signifie occlusion — la boucle principale gère la persistance de l'état.
    """

    def __init__(self, config: ArucoConfig) -> None:
        dict_id = getattr(cv2.aruco, config.dictionary, None)
        if dict_id is None:
            raise ValueError(
                f"Dictionnaire ArUco inconnu : '{config.dictionary}'. "
                f"Exemples valides : DICT_4X4_50, DICT_5X5_100."
            )
        dictionary = cv2.aruco.getPredefinedDictionary(dict_id)
        params = cv2.aruco.DetectorParameters()
        self._detector = cv2.aruco.ArucoDetector(dictionary, params)

    def detect(self, frame: np.ndarray) -> list[MarkerDetection]:
        """Détecte les marqueurs de plateau dans la frame BGR fournie."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        corners, ids, _ = self._detector.detectMarkers(gray)

        if ids is None:
            return []

        results: list[MarkerDetection] = []
        for marker_corners, marker_id in zip(corners, ids.flatten()):
            mid = int(marker_id)
            if mid not in BOARD_MARKER_IDS:
                continue
            results.append(
                MarkerDetection(id=mid, corners=marker_corners[0])  # (4, 2) float32
            )

        logger.debug("Marqueurs détectés : %s", [m.id for m in results])
        return results
