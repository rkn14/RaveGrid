"""Schémas de configuration (dataclasses)."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CameraConfig:
    index: int = 0
    width: int = 1280
    height: int = 720


@dataclass
class WindowConfig:
    title: str = "RaveGrid"
    width: int = 1280
    height: int = 720
    fullscreen: bool = False


@dataclass
class ArucoConfig:
    dictionary: str = "DICT_4X4_50"


@dataclass
class GridConfig:
    rows: int = 8
    cols: int = 32
    cell_px: int = 64   # résolution en pixels d'une cellule dans l'image rectifiée


@dataclass
class ColorRangeConfig:
    """Plage HSV pour détecter une couleur de jeton.

    h_min/h_max : teinte (0–179 dans OpenCV)
    s_min/s_max : saturation (0–255)
    v_min/v_max : luminosité (0–255)
    h_min2/h_max2 : seconde plage de teinte optionnelle (pour le rouge qui wrappe autour de H=0)
    """
    h_min: int
    h_max: int
    s_min: int = 100
    s_max: int = 255
    v_min: int = 80
    v_max: int = 255
    h_min2: int | None = None   # seconde plage — uniquement pour le rouge
    h_max2: int | None = None


@dataclass
class ColorsConfig:
    """Paramètres de détection des jetons colorés.

    ranges : dict nom_couleur → ColorRangeConfig
             Chaque sous-section [colors.<nom>] dans config.toml devient une entrée.
    """
    min_fill_ratio: float = 0.30   # fraction minimale de pixels colorés pour valider la détection
    center_crop:    float = 0.60   # fraction du centre de la cellule analysée (évite les bords de grille)
    ranges: dict[str, ColorRangeConfig] = field(default_factory=dict)


@dataclass
class UdpConfig:
    """Paramètres d'envoi de l'état de la grille par UDP (JSON)."""
    host:    str   = "127.0.0.1"
    port:    int   = 9000
    rate_hz: float = 10.0    # envois par seconde
    enabled: bool  = True


@dataclass
class AppConfig:
    camera: CameraConfig = field(default_factory=CameraConfig)
    window: WindowConfig = field(default_factory=WindowConfig)
    aruco: ArucoConfig = field(default_factory=ArucoConfig)
    grid: GridConfig = field(default_factory=GridConfig)
    colors: ColorsConfig = field(default_factory=ColorsConfig)
    udp: UdpConfig = field(default_factory=UdpConfig)
