"""Détection des caméras disponibles et sélection interactive."""

from __future__ import annotations

import contextlib
import os

import cv2

_MAX_PROBE = 8
# CAP_ANY = 0 : OpenCV choisit le meilleur backend disponible (MSMF, V4L2, etc.)
_BACKEND: int = cv2.CAP_ANY


@contextlib.contextmanager
def _silence_stderr():
    """Redirige stderr au niveau du descripteur de fichier pour masquer les logs C++ d'OpenCV."""
    devnull_fd = os.open(os.devnull, os.O_WRONLY)
    saved_fd = os.dup(2)
    os.dup2(devnull_fd, 2)
    os.close(devnull_fd)
    try:
        yield
    finally:
        os.dup2(saved_fd, 2)
        os.close(saved_fd)


def probe_cameras() -> list[int]:
    """Retourne la liste des indices de caméras fonctionnelles."""
    found: list[int] = []
    with _silence_stderr():
        for i in range(_MAX_PROBE):
            cap = cv2.VideoCapture(i, _BACKEND)
            if cap.isOpened():
                found.append(i)
                cap.release()
    return found


def select_camera_interactive(default: int = 0) -> int:
    """Affiche les caméras disponibles et demande à l'utilisateur de choisir."""
    print("Détection des caméras disponibles", end="", flush=True)
    cameras = probe_cameras()
    print()  # saut de ligne après les points de progression

    if not cameras:
        print("  Aucune caméra détectée — index 0 utilisé par défaut.")
        return 0

    print("\nCaméras disponibles :")
    for i, idx in enumerate(cameras):
        marker = "  ← défaut" if idx == default else ""
        print(f"  [{i}]  index caméra {idx}{marker}")

    if len(cameras) == 1:
        print(f"\nUne seule caméra détectée — sélection automatique (index {cameras[0]}).")
        return cameras[0]

    print(f"\nChoisissez une caméra [0–{len(cameras) - 1}] (Entrée = défaut [{default}]) : ", end="", flush=True)
    raw = input().strip()

    if raw == "":
        chosen = default if default in cameras else cameras[0]
        print(f"  → défaut : index {chosen}")
        return chosen

    try:
        n = int(raw)
        if 0 <= n < len(cameras):
            print(f"  → index {cameras[n]}")
            return cameras[n]
    except ValueError:
        pass

    fallback = default if default in cameras else cameras[0]
    print(f"  Choix invalide — retour au défaut : index {fallback}")
    return fallback
