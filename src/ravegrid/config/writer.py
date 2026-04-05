"""Sérialisation d'AppConfig vers un fichier TOML.

Note : les commentaires du fichier original ne sont pas conservés lors d'une
réécriture (usage typique : outil de calibration).
"""

from __future__ import annotations

from pathlib import Path

from .schema import AppConfig


def save(config: AppConfig, path: Path) -> None:
    """Écrit AppConfig dans un fichier TOML (écrase le fichier existant)."""
    lines: list[str] = []

    _section(lines, "camera")
    _kv(lines, "index",  config.camera.index)
    _kv(lines, "width",  config.camera.width)
    _kv(lines, "height", config.camera.height)
    lines.append("")

    _section(lines, "window")
    _kv(lines, "title",      config.window.title, quote=True)
    _kv(lines, "width",      config.window.width)
    _kv(lines, "height",     config.window.height)
    _kv(lines, "fullscreen", config.window.fullscreen)
    lines.append("")

    _section(lines, "aruco")
    _kv(lines, "dictionary", config.aruco.dictionary, quote=True)
    lines.append("")

    _section(lines, "grid")
    _kv(lines, "rows",    config.grid.rows)
    _kv(lines, "cols",    config.grid.cols)
    _kv(lines, "cell_px", config.grid.cell_px)
    lines.append("")

    _section(lines, "colors")
    _kv(lines, "min_fill_ratio", config.colors.min_fill_ratio)
    _kv(lines, "center_crop",    config.colors.center_crop)

    for name, rng in config.colors.ranges.items():
        lines.append("")
        _section(lines, f"colors.{name}")
        _kv(lines, "h_min", rng.h_min)
        _kv(lines, "h_max", rng.h_max)
        _kv(lines, "s_min", rng.s_min)
        _kv(lines, "s_max", rng.s_max)
        _kv(lines, "v_min", rng.v_min)
        _kv(lines, "v_max", rng.v_max)
        if rng.h_min2 is not None:
            _kv(lines, "h_min2", rng.h_min2)
        if rng.h_max2 is not None:
            _kv(lines, "h_max2", rng.h_max2)

    lines.append("")
    _section(lines, "udp")
    _kv(lines, "enabled", config.udp.enabled)
    _kv(lines, "host",    config.udp.host, quote=True)
    _kv(lines, "port",    config.udp.port)
    _kv(lines, "rate_hz", config.udp.rate_hz)

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ──────────────────────────────────────────────────────────────────────────────

def _section(lines: list[str], name: str) -> None:
    lines.append(f"[{name}]")


def _kv(lines: list[str], key: str, value: object, quote: bool = False) -> None:
    if isinstance(value, bool):
        lines.append(f"{key} = {'true' if value else 'false'}")
    elif quote:
        lines.append(f'{key} = "{value}"')
    elif isinstance(value, float):
        lines.append(f"{key} = {value}")
    else:
        lines.append(f"{key} = {value}")
