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
class AppConfig:
    camera: CameraConfig = field(default_factory=CameraConfig)
    window: WindowConfig = field(default_factory=WindowConfig)
