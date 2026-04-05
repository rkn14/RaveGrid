"""Classification de la couleur d'un jeton dans une cellule de la grille."""

from __future__ import annotations

import cv2
import numpy as np

from ..config.schema import ColorsConfig
from ..domain.board import CellState
from .grid_splitter import GridSplitter


class CellClassifier:
    """Détecte la couleur du jeton présent dans une cellule (ou None si vide).

    Algorithme :
    1. Rogner le centre de la cellule (center_crop évite les lignes de grille).
    2. Convertir en HSV.
    3. Appliquer le masque de chaque couleur configurée.
    4. Retourner la première couleur dont la proportion de pixels dépasse min_fill_ratio.
    5. Si aucune couleur ne dépasse le seuil → case vide (None).

    Ajouter une couleur : ajouter une sous-section [colors.<nom>] dans config.toml.
    """

    def __init__(self, config: ColorsConfig) -> None:
        self._config = config

    def classify(self, cell: np.ndarray) -> str | None:
        """Retourne le nom de la couleur détectée, ou None si la case est vide."""
        cpx = cell.shape[0]
        margin = max(1, int(cpx * (1.0 - self._config.center_crop) / 2))
        crop = cell[margin : cpx - margin, margin : cpx - margin]

        if crop.size == 0:
            return None

        hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)

        for color_name, rng in self._config.ranges.items():
            lower = np.array([rng.h_min, rng.s_min, rng.v_min], dtype=np.uint8)
            upper = np.array([rng.h_max, rng.s_max, rng.v_max], dtype=np.uint8)
            mask = cv2.inRange(hsv, lower, upper)

            # Seconde plage de teinte (nécessaire pour le rouge qui wrappe autour de H=0)
            if rng.h_min2 is not None and rng.h_max2 is not None:
                lower2 = np.array([rng.h_min2, rng.s_min, rng.v_min], dtype=np.uint8)
                upper2 = np.array([rng.h_max2, rng.s_max, rng.v_max], dtype=np.uint8)
                mask = cv2.bitwise_or(mask, cv2.inRange(hsv, lower2, upper2))

            ratio = float(mask.sum()) / (255.0 * mask.size)
            if ratio >= self._config.min_fill_ratio:
                return color_name

        return None

    def classify_grid(
        self,
        rectified: np.ndarray,
        splitter: GridSplitter,
    ) -> list[list[str | None]]:
        """Retourne une grille [row][col] de couleurs (str) ou None (vide)."""
        grid: list[list[str | None]] = [
            [None] * splitter._cols for _ in range(splitter._rows)
        ]
        for r, c, cell in splitter.iter_cells(rectified):
            grid[r][c] = self.classify(cell)
        return grid
