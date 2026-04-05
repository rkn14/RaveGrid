"""Outil de calibration des seuils HSV pour la détection des jetons colorés.

Affichage en deux panneaux :
  Gauche  — flux caméra avec surbrillance des pixels détectés.
  Droite  — masque binaire (blanc = détecté) appliqué sur l'image de référence
             (vue rectifiée si les 4 marqueurs sont visibles, sinon caméra brute).

Raccourcis clavier :
  S          Sauvegarder les seuils courants dans config.toml
  R          Réinitialiser la couleur courante aux valeurs d'origine
  Q / Échap  Quitter sans sauvegarder
  Clic       Afficher la valeur HSV du pixel cliqué (terminal + image)

Usage depuis la racine du projet (venv activé) :
  python tools/calibrate_colors.py [--config config.toml]
"""

from __future__ import annotations

import argparse
import copy
import dataclasses
import sys
from pathlib import Path

# Assure que le package ravegrid est trouvable quelle que soit l'origine du lancement
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import cv2
import numpy as np

from ravegrid.capture.camera import OpenCvCamera
from ravegrid.capture.selector import select_camera_interactive
from ravegrid.config.loader import load as load_config
from ravegrid.config.schema import ColorRangeConfig
from ravegrid.config.writer import save as save_config
from ravegrid.domain.board import BoardCorners
from ravegrid.vision.board_detector import BoardDetector
from ravegrid.vision.rectifier import Rectifier

# ──────────────────────────────────────────────────────────────────────────────
# Constantes d'affichage
# ──────────────────────────────────────────────────────────────────────────────

_WIN        = "RaveGrid — Calibration couleurs"
_PANEL_W    = 640    # largeur de chaque demi-panneau
_PANEL_H    = 480    # hauteur de l'image (hors trackbars)
_FONT       = cv2.FONT_HERSHEY_SIMPLEX

# Couleur de surbrillance BGR pour chaque nom de jeton (copie légère de annotator.py)
_TOKEN_BGR: dict[str, tuple[int, int, int]] = {
    "yellow": (0, 220, 255),
    "red":    (0, 50, 220),
    "green":  (50, 200, 50),
    "blue":   (220, 80, 0),
    "orange": (0, 140, 255),
    "purple": (180, 0, 180),
}
_DEFAULT_BGR = (180, 180, 180)

# ──────────────────────────────────────────────────────────────────────────────
# Helpers affichage
# ──────────────────────────────────────────────────────────────────────────────

def _resize(img: np.ndarray, w: int, h: int) -> np.ndarray:
    return cv2.resize(img, (w, h), interpolation=cv2.INTER_LINEAR)


def _text(img: np.ndarray, txt: str, pos: tuple[int, int],
          scale: float = 0.55, color: tuple = (255, 255, 255)) -> None:
    cv2.putText(img, txt, pos, _FONT, scale, (0, 0, 0), 3, cv2.LINE_AA)
    cv2.putText(img, txt, pos, _FONT, scale, color,     1, cv2.LINE_AA)


def _compute_mask(frame_bgr: np.ndarray, rng: ColorRangeConfig) -> np.ndarray:
    hsv   = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)
    lower = np.array([rng.h_min, rng.s_min, rng.v_min], dtype=np.uint8)
    upper = np.array([rng.h_max, rng.s_max, rng.v_max], dtype=np.uint8)
    mask  = cv2.inRange(hsv, lower, upper)
    if rng.h_min2 is not None and rng.h_max2 is not None:
        l2 = np.array([rng.h_min2, rng.s_min, rng.v_min], dtype=np.uint8)
        u2 = np.array([rng.h_max2, rng.s_max, rng.v_max], dtype=np.uint8)
        mask = cv2.bitwise_or(mask, cv2.inRange(hsv, l2, u2))
    return mask


def _build_display(
    camera_frame: np.ndarray,
    ref_frame: np.ndarray,
    rng: ColorRangeConfig,
    color_name: str,
    hsv_sample: tuple[int, int, int] | None,
    markers_ok: bool,
) -> np.ndarray:
    fill_bgr = _TOKEN_BGR.get(color_name, _DEFAULT_BGR)

    # ── Panneau gauche : caméra + surbrillance ─────────────────────────────
    left = _resize(camera_frame, _PANEL_W, _PANEL_H).copy()
    mask_cam = _compute_mask(left, rng)
    highlight = left.copy()
    highlight[mask_cam > 0] = fill_bgr
    cv2.addWeighted(highlight, 0.55, left, 0.45, 0, left)

    ratio_cam = 100.0 * float(mask_cam.sum()) / (255.0 * mask_cam.size)
    marker_txt = "Marqueurs OK" if markers_ok else "Marqueurs non detectes"
    marker_col = (0, 220, 0) if markers_ok else (0, 165, 255)
    _text(left, f"Couleur : {color_name}", (10, 28))
    _text(left, marker_txt, (10, 56), color=marker_col)
    _text(left, f"Pixels detectes : {ratio_cam:.1f}%", (10, 84))
    if hsv_sample is not None:
        h, s, v = hsv_sample
        _text(left, f"HSV clic : H={h}  S={s}  V={v}", (10, 112), color=(0, 220, 255))
    _text(left, "S=sauvegarder  R=reset  Q=quitter  Clic=sampler",
          (10, _PANEL_H - 12), scale=0.42)

    # ── Panneau droit haut : image de référence ───────────────────────────
    ref_h = _PANEL_H // 2
    ref_aspect = ref_frame.shape[1] / max(ref_frame.shape[0], 1)
    ref_w = min(_PANEL_W, int(ref_h * ref_aspect))
    right_top = _resize(ref_frame, ref_w, ref_h)
    if ref_w < _PANEL_W:
        pad = np.zeros((ref_h, _PANEL_W - ref_w, 3), dtype=np.uint8)
        right_top = np.hstack([right_top, pad])
    lbl = "Vue rectifiee" if markers_ok else "Camera brute (marqueurs absents)"
    _text(right_top, lbl, (10, 28))

    # ── Panneau droit bas : masque binaire ────────────────────────────────
    mask_ref  = _compute_mask(_resize(ref_frame, _PANEL_W, ref_h), rng)
    ratio_ref = 100.0 * float(mask_ref.sum()) / (255.0 * mask_ref.size)
    right_bot = cv2.cvtColor(mask_ref, cv2.COLOR_GRAY2BGR)
    _text(right_bot, f"Masque HSV — {ratio_ref:.1f}% detectes", (10, 28))
    _text(right_bot,
          f"H[{rng.h_min}-{rng.h_max}]  S[{rng.s_min}-{rng.s_max}]  V[{rng.v_min}-{rng.v_max}]",
          (10, 56))

    right = np.vstack([right_top, right_bot])
    return np.hstack([left, right])


# ──────────────────────────────────────────────────────────────────────────────
# Trackbars
# ──────────────────────────────────────────────────────────────────────────────

def _setup_trackbars(win: str, n_colors: int) -> None:
    cv2.createTrackbar("Couleur",  win,   0, max(0, n_colors - 1), lambda _: None)
    cv2.createTrackbar("H  min",   win,   0, 179, lambda _: None)
    cv2.createTrackbar("H  max",   win,  35, 179, lambda _: None)
    cv2.createTrackbar("S  min",   win, 100, 255, lambda _: None)
    cv2.createTrackbar("S  max",   win, 255, 255, lambda _: None)
    cv2.createTrackbar("V  min",   win,  80, 255, lambda _: None)
    cv2.createTrackbar("V  max",   win, 255, 255, lambda _: None)


def _push_trackbars(win: str, rng: ColorRangeConfig) -> None:
    cv2.setTrackbarPos("H  min", win, rng.h_min)
    cv2.setTrackbarPos("H  max", win, rng.h_max)
    cv2.setTrackbarPos("S  min", win, rng.s_min)
    cv2.setTrackbarPos("S  max", win, rng.s_max)
    cv2.setTrackbarPos("V  min", win, rng.v_min)
    cv2.setTrackbarPos("V  max", win, rng.v_max)


def _pull_trackbars(win: str) -> tuple[int, ColorRangeConfig]:
    idx   = cv2.getTrackbarPos("Couleur", win)
    h_min = cv2.getTrackbarPos("H  min",  win)
    h_max = cv2.getTrackbarPos("H  max",  win)
    s_min = cv2.getTrackbarPos("S  min",  win)
    s_max = cv2.getTrackbarPos("S  max",  win)
    v_min = cv2.getTrackbarPos("V  min",  win)
    v_max = cv2.getTrackbarPos("V  max",  win)
    return idx, ColorRangeConfig(
        h_min=h_min, h_max=h_max,
        s_min=s_min, s_max=s_max,
        v_min=v_min, v_max=v_max,
    )


# ──────────────────────────────────────────────────────────────────────────────
# Callback souris
# ──────────────────────────────────────────────────────────────────────────────

# Partagé entre le callback et la boucle principale via un dict mutable
_state: dict = {"hsv_sample": None, "camera_frame": None, "win": None, "left_panel": None}

# Décalage vertical approximatif dû aux trackbars OpenCV (7 × ~27px sur Windows)
_TRACKBAR_OFFSET_PX = 27 * 7

# Tolérance appliquée autour de la valeur cliquée pour pré-remplir les sliders
_H_TOL = 12   # ± sur la teinte
_S_TOL = 60   # marge basse sur la saturation
_V_TOL = 60   # marge basse sur la luminosité


def _mouse_cb(event: int, x: int, y: int, flags: int, param: object) -> None:
    if event != cv2.EVENT_LBUTTONDOWN:
        return
    win   = _state["win"]
    panel = _state["left_panel"]   # image déjà redimensionnée à PANEL_W × PANEL_H
    if win is None or panel is None:
        return

    # Correction du décalage trackbar et vérification de la zone valide
    img_y = y - _TRACKBAR_OFFSET_PX
    if img_y < 0 or img_y >= _PANEL_H or x < 0 or x >= _PANEL_W:
        return

    # Échantillonnage direct sur le panneau affiché — pas de remapping
    hsv_img = cv2.cvtColor(panel, cv2.COLOR_BGR2HSV)
    h, s, v = (int(val) for val in hsv_img[img_y, x])
    _state["hsv_sample"] = (h, s, v)

    # Positionner les sliders autour de la valeur échantillonnée
    h_min = max(0,   h - _H_TOL)
    h_max = min(179, h + _H_TOL)
    s_min = max(0,   s - _S_TOL)
    v_min = max(0,   v - _V_TOL)
    cv2.setTrackbarPos("H  min", win, h_min)
    cv2.setTrackbarPos("H  max", win, h_max)
    cv2.setTrackbarPos("S  min", win, s_min)
    cv2.setTrackbarPos("V  min", win, v_min)

    print(f"  Clic  H={h}  S={s}  V={v}  →  H[{h_min}-{h_max}]  S≥{s_min}  V≥{v_min}")


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="calibrate_colors",
        description="Calibration interactive des seuils HSV — RaveGrid",
    )
    parser.add_argument("--config", default="config.toml",
                        help="chemin vers config.toml (défaut : config.toml)")
    args = parser.parse_args()

    config_path = Path(args.config)
    config      = load_config(config_path)

    color_names = list(config.colors.ranges.keys())
    if not color_names:
        print(
            "Aucune couleur définie dans [colors] de config.toml.\n"
            "Ajoutez une sous-section, ex. [colors.yellow], puis relancez."
        )
        return

    # Copie de référence pour le reset
    original_ranges = {k: copy.copy(v) for k, v in config.colors.ranges.items()}

    camera_index = select_camera_interactive(default=config.camera.index)
    cam_cfg = dataclasses.replace(config.camera, index=camera_index)

    detector  = BoardDetector(config.aruco)
    rectifier = Rectifier(config.grid)

    # ── Fenêtre OpenCV ──────────────────────────────────────────────────────
    cv2.namedWindow(_WIN, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(_WIN, _PANEL_W * 2, _PANEL_H + _TRACKBAR_OFFSET_PX)
    _setup_trackbars(_WIN, len(color_names))
    _push_trackbars(_WIN, config.colors.ranges[color_names[0]])
    _state["win"] = _WIN
    cv2.setMouseCallback(_WIN, _mouse_cb)

    prev_idx = 0

    print(f"\nCalibration démarrée — caméra {camera_index}")
    print(f"Couleurs disponibles : {color_names}")
    print("S=sauvegarder  R=reset  Q=quitter  Clic gauche=sampler HSV\n")

    with OpenCvCamera(cam_cfg) as camera:
        if not camera.is_opened:
            print(f"Erreur : impossible d'ouvrir la caméra {camera_index}")
            return

        while True:
            ok, frame = camera.read()
            if not ok:
                continue

            _state["camera_frame"] = frame
            _state["left_panel"]   = _resize(frame, _PANEL_W, _PANEL_H)

            idx, rng = _pull_trackbars(_WIN)
            idx = min(idx, len(color_names) - 1)
            color_name = color_names[idx]

            # Changement de couleur → recharger les trackbars depuis la config courante
            if idx != prev_idx:
                _push_trackbars(_WIN, config.colors.ranges[color_names[idx]])
                _, rng = _pull_trackbars(_WIN)
                prev_idx = idx

            # Mise à jour de la plage courante en mémoire (aperçu temps réel)
            config.colors.ranges[color_name] = rng

            # Détection ArUco → image de référence rectifiée si possible
            markers    = detector.detect(frame)
            corners    = BoardCorners.from_markers(markers)
            markers_ok = corners is not None

            if corners is not None:
                rect_result = rectifier.compute(corners)
                ref_frame   = rectifier.rectify(frame, rect_result)
            else:
                ref_frame = frame

            display = _build_display(
                frame, ref_frame, rng, color_name,
                _state["hsv_sample"], markers_ok,
            )
            cv2.imshow(_WIN, display)

            key = cv2.waitKey(1) & 0xFF

            if key in (ord("q"), ord("Q"), 27):
                break

            elif key in (ord("s"), ord("S")):
                save_config(config, config_path)
                print(f"Sauvegardé → {config_path}")
                for name, r in config.colors.ranges.items():
                    print(f"  [{name}]  H[{r.h_min}-{r.h_max}]  S[{r.s_min}-{r.s_max}]  V[{r.v_min}-{r.v_max}]")

            elif key in (ord("r"), ord("R")):
                if color_name in original_ranges:
                    config.colors.ranges[color_name] = copy.copy(original_ranges[color_name])
                    _push_trackbars(_WIN, config.colors.ranges[color_name])
                    _state["hsv_sample"] = None
                    print(f"Reset {color_name}")

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
