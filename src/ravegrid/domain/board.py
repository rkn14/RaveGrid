"""Modèles métier liés au plateau physique."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# Correspondance ID ArUco → coin du plateau (définie dans vision-marqueurs-aruco.md)
#   ID 0 → Haut-Gauche   corner intérieur = index 2 (bas-droit  du marqueur)
#   ID 1 → Haut-Droit    corner intérieur = index 3 (bas-gauche du marqueur)
#   ID 2 → Bas-Droit     corner intérieur = index 0 (haut-gauche du marqueur)
#   ID 3 → Bas-Gauche    corner intérieur = index 1 (haut-droit  du marqueur)
MARKER_INNER_CORNER: dict[int, int] = {0: 2, 1: 3, 2: 0, 3: 1}

MARKER_ROLE: dict[int, str] = {
    0: "Haut-Gauche",
    1: "Haut-Droit",
    2: "Bas-Droit",
    3: "Bas-Gauche",
}

BOARD_MARKER_IDS: frozenset[int] = frozenset(MARKER_ROLE)


@dataclass
class MarkerDetection:
    """Un marqueur ArUco détecté dans la frame courante."""

    id: int
    corners: np.ndarray  # shape (4, 2), float32 — ordre ArUco : TL, TR, BR, BL

    @property
    def role(self) -> str:
        return MARKER_ROLE.get(self.id, f"ID {self.id}")

    @property
    def inner_corner(self) -> np.ndarray:
        """Point de référence pour la grille (corner intérieur du marqueur)."""
        return self.corners[MARKER_INNER_CORNER[self.id]]

    @property
    def center(self) -> np.ndarray:
        return self.corners.mean(axis=0)


@dataclass
class BoardCorners:
    """Les 4 corners intérieurs des marqueurs, prêts pour la perspective transform."""

    top_left:     np.ndarray  # shape (2,), float32
    top_right:    np.ndarray
    bottom_right: np.ndarray
    bottom_left:  np.ndarray

    @classmethod
    def from_markers(cls, markers: list[MarkerDetection]) -> BoardCorners | None:
        """Construit BoardCorners si les 4 marqueurs requis sont présents."""
        by_id = {m.id: m for m in markers}
        if not BOARD_MARKER_IDS.issubset(by_id):
            return None
        return cls(
            top_left=by_id[0].inner_corner,
            top_right=by_id[1].inner_corner,
            bottom_right=by_id[2].inner_corner,
            bottom_left=by_id[3].inner_corner,
        )
