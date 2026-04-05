"""Calcul de la transformation de perspective et projection de la grille."""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from ..config.schema import GridConfig
from ..domain.board import BoardCorners


@dataclass
class RectificationResult:
    """Matrices de perspective calculées à partir des 4 coins du plateau.

    M     : espace caméra → image rectifiée (top-down)
    M_inv : image rectifiée → espace caméra  (pour reprojeter la grille)
    """

    M:     np.ndarray   # shape (3, 3), float64
    M_inv: np.ndarray   # shape (3, 3), float64
    out_w: int
    out_h: int
    rows:  int
    cols:  int

    def grid_intersections_in_image(self) -> np.ndarray:
        """Retourne les (rows+1)×(cols+1) intersections de la grille
        reprojetées dans l'espace caméra (perspective).

        Shape retournée : (rows+1, cols+1, 2), float32.
        Indexing : pts[i, j] = point à la ligne i, colonne j.
        """
        cell_w = self.out_w / self.cols
        cell_h = self.out_h / self.rows

        pts = np.array(
            [[j * cell_w, i * cell_h]
             for i in range(self.rows + 1)
             for j in range(self.cols + 1)],
            dtype=np.float32,
        ).reshape(-1, 1, 2)

        back = cv2.perspectiveTransform(pts, self.M_inv)
        return back.reshape(self.rows + 1, self.cols + 1, 2)


class Rectifier:
    """Calcule la transformation de perspective à partir des coins du plateau."""

    def __init__(self, config: GridConfig) -> None:
        self._rows  = config.rows
        self._cols  = config.cols
        self._out_w = config.cols * config.cell_px
        self._out_h = config.rows * config.cell_px

    def compute(self, corners: BoardCorners) -> RectificationResult:
        """Calcule M et M_inv depuis les 4 corners intérieurs des marqueurs."""
        src = np.array([
            corners.top_left,
            corners.top_right,
            corners.bottom_right,
            corners.bottom_left,
        ], dtype=np.float32)

        dst = np.array([
            [0,            0           ],
            [self._out_w,  0           ],
            [self._out_w,  self._out_h ],
            [0,            self._out_h ],
        ], dtype=np.float32)

        M = cv2.getPerspectiveTransform(src, dst)
        return RectificationResult(
            M=M,
            M_inv=np.linalg.inv(M),
            out_w=self._out_w,
            out_h=self._out_h,
            rows=self._rows,
            cols=self._cols,
        )

    def rectify(self, frame: np.ndarray, result: RectificationResult) -> np.ndarray:
        """Retourne l'image du plateau redressée vue de dessus."""
        return cv2.warpPerspective(frame, result.M, (result.out_w, result.out_h))
