"""Génère et sauvegarde les 4 marqueurs ArUco à imprimer.

Usage (depuis la racine du projet, venv activé) :
    python tools/generate_markers.py

Les fichiers PNG sont écrits dans tools/markers/.
Taille par défaut : 400 × 400 px (imprimable à 6 × 6 cm à 170 dpi).

Correspondance ID → coin du plateau :
    ID 0  Haut-Gauche
    ID 1  Haut-Droit
    ID 2  Bas-Droit
    ID 3  Bas-Gauche
"""

from __future__ import annotations

from pathlib import Path

import cv2

DICTIONARY_NAME = "DICT_4X4_50"
MARKER_SIZE_PX = 400
OUTPUT_DIR = Path(__file__).parent / "markers"

MARKER_ROLES = {
    0: "haut_gauche",
    1: "haut_droit",
    2: "bas_droit",
    3: "bas_gauche",
}


def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)

    dict_id = getattr(cv2.aruco, DICTIONARY_NAME)
    dictionary = cv2.aruco.getPredefinedDictionary(dict_id)

    for marker_id, role in MARKER_ROLES.items():
        img = cv2.aruco.generateImageMarker(dictionary, marker_id, MARKER_SIZE_PX)
        filename = OUTPUT_DIR / f"marker_{marker_id}_{role}.png"
        cv2.imwrite(str(filename), img)
        print(f"  Écrit : {filename}")

    print(f"\n4 marqueurs générés dans {OUTPUT_DIR}/")
    print("Imprimer chaque fichier à la même taille physique (ex. 6 × 6 cm).")
    print("Placer dans les coins du plateau : ID 0 en haut-gauche, dans le sens horaire.")


if __name__ == "__main__":
    main()
