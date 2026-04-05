"""Chargement de la configuration depuis un fichier TOML."""

from __future__ import annotations

from pathlib import Path

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore[no-redef]

from .schema import AppConfig, ArucoConfig, CameraConfig, WindowConfig

_DEFAULT_PATH = Path("config.toml")


def load(path: Path | None = None) -> AppConfig:
    """Charge la configuration. Retourne les valeurs par défaut si le fichier est absent."""
    resolved = path or _DEFAULT_PATH
    if not resolved.exists():
        return AppConfig()

    with resolved.open("rb") as f:
        data = tomllib.load(f)

    cam_data   = data.get("camera", {})
    win_data   = data.get("window", {})
    aruco_data = data.get("aruco", {})

    return AppConfig(
        camera=CameraConfig(**cam_data)   if cam_data   else CameraConfig(),
        window=WindowConfig(**win_data)   if win_data   else WindowConfig(),
        aruco=ArucoConfig(**aruco_data)   if aruco_data else ArucoConfig(),
    )
