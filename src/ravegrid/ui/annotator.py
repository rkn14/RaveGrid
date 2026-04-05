"""Surcouches graphiques OpenCV dessinées sur la frame avant affichage."""

from __future__ import annotations

import cv2
import numpy as np

from ..domain.board import BOARD_MARKER_IDS, MarkerDetection

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
