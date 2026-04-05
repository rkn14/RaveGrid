"""Point d'entrée en ligne de commande."""

from __future__ import annotations

import argparse
import logging
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="ravegrid",
        description="RaveGrid — analyse de plateau physique par vision (OpenCV + pygame)",
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="afficher les versions et quitter",
    )
    parser.add_argument(
        "--config",
        metavar="FICHIER",
        help="chemin vers un fichier config.toml (défaut : config.toml à la racine)",
    )
    parser.add_argument(
        "--log-level",
        default="WARNING",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="niveau de journalisation (défaut : WARNING)",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(levelname)s  %(name)s  %(message)s",
    )

    if args.version:
        import cv2
        import pygame

        from ravegrid import __version__ as pkg_version

        print(f"ravegrid {pkg_version}")
        print(f"OpenCV   {cv2.__version__}")
        print(f"pygame   {pygame.version.ver}")
        return 0

    from pathlib import Path

    from ravegrid.app.loop import AppLoop
    from ravegrid.capture.selector import select_camera_interactive
    from ravegrid.config.loader import load as load_config

    config_path = Path(args.config) if args.config else None
    config = load_config(config_path)

    camera_index = select_camera_interactive(default=config.camera.index)
    AppLoop(config, camera_index).run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
