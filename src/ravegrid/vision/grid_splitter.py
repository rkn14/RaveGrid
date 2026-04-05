"""Découpage de l'image rectifiée en cellules individuelles."""

from __future__ import annotations

from collections.abc import Iterator

import numpy as np

from ..config.schema import GridConfig


class GridSplitter:
    """Itère sur les cellules d'une image rectifiée (vue top-down du plateau).

    Chaque cellule est une vue (slice) de l'image — pas une copie — donc
    aucun surcoût mémoire.
    """

    def __init__(self, config: GridConfig) -> None:
        self._rows    = config.rows
        self._cols    = config.cols
        self._cell_px = config.cell_px

    def iter_cells(
        self, rectified: np.ndarray
    ) -> Iterator[tuple[int, int, np.ndarray]]:
        """Yield (row, col, cell_image) pour chaque cellule de la grille.

        cell_image : vue BGR de shape (cell_px, cell_px, 3).
        """
        cpx = self._cell_px
        for r in range(self._rows):
            for c in range(self._cols):
                yield r, c, rectified[r * cpx : (r + 1) * cpx, c * cpx : (c + 1) * cpx]
