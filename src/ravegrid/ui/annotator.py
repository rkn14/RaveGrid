"""Surcouches graphiques OpenCV dessinées sur la frame avant affichage."""

from __future__ import annotations

import cv2
import numpy as np

from ..domain.board import BOARD_MARKER_IDS, MarkerDetection
from ..vision.rectifier import RectificationResult

# Couleur de remplissage BGR pour chaque nom de couleur de jeton.
# Ajouter une entrée ici lors de l'ajout d'une nouvelle couleur.
_TOKEN_FILL_BGR: dict[str, tuple[int, int, int]] = {
    "yellow": (0, 220, 255),
    "red":    (0, 50, 220),
    "green":  (50, 200, 50),
    "blue":   (220, 80, 0),
    "orange": (0, 140, 255),
    "purple": (180, 0, 180),
    "white":  (230, 230, 230),
}
_TOKEN_FILL_DEFAULT = (128, 128, 128)   # couleur inconnue

# Couleur BGR par ID de marqueur
_MARKER_COLOR: dict[int, tuple[int, int, int]] = {
    0: (0, 255, 0),    # Haut-Gauche  — vert
    1: (255, 255, 0),  # Haut-Droit   — cyan
    2: (0, 0, 255),    # Bas-Droit    — rouge
    3: (255, 0, 255),  # Bas-Gauche   — magenta
}

_FONT = cv2.FONT_HERSHEY_SIMPLEX


def draw_markers(frame: np.ndarray, markers: list[MarkerDetection]) -> np.ndarray:
    """Retourne une copie de la frame avec les marqueurs annotés.

    Pour chaque marqueur détecté :
    - contour du carré (couleur propre au coin)
    - point rouge sur le corner intérieur (point de référence grille)
    - étiquette avec l'ID et le rôle (coin du plateau)

    En haut à gauche : statut global (N/4 marqueurs visibles).
    """
    out = frame.copy()

    for m in markers:
        color = _MARKER_COLOR.get(m.id, (255, 255, 255))
        pts = m.corners.astype(np.int32)

        # Contour du marqueur
        cv2.polylines(out, [pts], isClosed=True, color=color, thickness=2)

        # Corner intérieur (point de référence pour la grille future)
        inner = tuple(m.inner_corner.astype(int))
        cv2.circle(out, inner, 7, color, thickness=-1)
        cv2.circle(out, inner, 7, (255, 255, 255), thickness=1)

        # Étiquette au centre du marqueur
        cx, cy = m.center.astype(int)
        label = f"ID{m.id} {m.role}"
        (tw, th), _ = cv2.getTextSize(label, _FONT, 0.55, 2)
        cv2.rectangle(out, (cx - tw // 2 - 4, cy - th - 6), (cx + tw // 2 + 4, cy + 4), (0, 0, 0), -1)
        cv2.putText(out, label, (cx - tw // 2, cy), _FONT, 0.55, color, 2, cv2.LINE_AA)

    # Statut global
    found_ids = {m.id for m in markers}
    n = len(found_ids & BOARD_MARKER_IDS)
    all_ok = n == 4
    status_text = f"Marqueurs : {n}/4" + ("  OK" if all_ok else "  en attente...")
    status_color = (0, 220, 0) if all_ok else (0, 165, 255)
    cv2.putText(out, status_text, (20, 40), _FONT, 1.0, (0, 0, 0), 4, cv2.LINE_AA)
    cv2.putText(out, status_text, (20, 40), _FONT, 1.0, status_color, 2, cv2.LINE_AA)

    return out


def draw_grid(frame: np.ndarray, rect: RectificationResult) -> np.ndarray:
    """Dessine la grille dans l'espace perspective de la frame caméra.

    - Bordure extérieure : blanc, épaisseur 2
    - Lignes internes    : gris clair, épaisseur 1
    Les lignes restent droites sous une transformation projective :
    seules les extrémités de chaque ligne sont reprojetées.
    """
    out = frame.copy()
    pts = rect.grid_intersections_in_image()  # shape (rows+1, cols+1, 2)
    rows, cols = rect.rows, rect.cols

    _COLOR_BORDER   = (255, 255, 255)
    _COLOR_INTERNAL = (160, 160, 160)

    def _line(i0: int, j0: int, i1: int, j1: int, border: bool) -> None:
        color     = _COLOR_BORDER if border else _COLOR_INTERNAL
        thickness = 2 if border else 1
        p1 = tuple(pts[i0, j0].astype(int))
        p2 = tuple(pts[i1, j1].astype(int))
        cv2.line(out, p1, p2, color, thickness, cv2.LINE_AA)

    # Lignes horizontales (rows + 1 lignes, de col 0 à col cols)
    for i in range(rows + 1):
        _line(i, 0, i, cols, border=(i == 0 or i == rows))

    # Lignes verticales (cols + 1 lignes, de row 0 à row rows)
    for j in range(cols + 1):
        _line(0, j, rows, j, border=(j == 0 or j == cols))

    return out


_TOKEN_BORDER_THICKNESS = 2   # épaisseur du cadre autour d'une case détectée
_TOKEN_LABEL_SCALE      = 0.35
_TOKEN_LABEL_FONT       = cv2.FONT_HERSHEY_SIMPLEX


def draw_cell_colors(
    frame: np.ndarray,
    rect: RectificationResult,
    grid_colors: list[list[str | None]],
) -> np.ndarray:
    """Pour chaque case occupée : dessine un contour coloré + le nom de la couleur.

    L'image vidéo n'est jamais modifiée (pas de fill, pas de transparence).
    """
    out = frame.copy()
    pts = rect.grid_intersections_in_image()  # shape (rows+1, cols+1, 2)

    for r, row_colors in enumerate(grid_colors):
        for c, color_name in enumerate(row_colors):
            if color_name is None:
                continue
            color = _TOKEN_FILL_BGR.get(color_name, _TOKEN_FILL_DEFAULT)
            quad = np.array(
                [pts[r, c], pts[r, c + 1], pts[r + 1, c + 1], pts[r + 1, c]],
                dtype=np.int32,
            )

            # Contour de la case
            cv2.polylines(out, [quad], isClosed=True, color=color,
                          thickness=_TOKEN_BORDER_THICKNESS, lineType=cv2.LINE_AA)

            # Nom de la couleur centré dans la case
            cx, cy = quad.mean(axis=0).astype(int)
            (tw, th), _ = cv2.getTextSize(color_name, _TOKEN_LABEL_FONT, _TOKEN_LABEL_SCALE, 1)
            tx, ty = cx - tw // 2, cy + th // 2
            cv2.putText(out, color_name, (tx, ty), _TOKEN_LABEL_FONT,
                        _TOKEN_LABEL_SCALE, (0, 0, 0), 2, cv2.LINE_AA)
            cv2.putText(out, color_name, (tx, ty), _TOKEN_LABEL_FONT,
                        _TOKEN_LABEL_SCALE, color, 1, cv2.LINE_AA)

    return out
