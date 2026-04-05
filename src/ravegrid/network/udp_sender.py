"""Envoi de l'état de la grille par UDP au format JSON.

Format du message :
{
  "seq":    <entier croissant>,
  "colors": {"1": "yellow", "2": "red", ...},   // mapping index → nom
  "grid":   [[0,1,0,2,...], [0,0,0,...], ...]    // 0 = vide, 1..N = couleur
}

La correspondance couleur → entier suit l'ordre d'apparition dans config.toml :
  première couleur = 1, deuxième = 2, etc.
  0 est réservé pour « case vide ».
"""

from __future__ import annotations

import json
import logging
import socket
import time

from ..config.schema import GridConfig, UdpConfig

logger = logging.getLogger(__name__)


class UdpSender:
    """Envoie périodiquement l'état de la grille en JSON sur un socket UDP.

    Utilisation :
        with UdpSender(udp_cfg, grid_cfg, color_names) as sender:
            sender.maybe_send(grid_colors)   # appelé à chaque frame
    """

    def __init__(
        self,
        config: UdpConfig,
        grid_config: GridConfig,
        color_names: list[str],
    ) -> None:
        self._config   = config
        self._rows     = grid_config.rows
        self._cols     = grid_config.cols
        self._interval = 1.0 / max(config.rate_hz, 0.1)
        self._last_send: float = 0.0
        self._seq: int = 0

        # Mapping couleur → entier (ordre d'apparition dans config.toml)
        self._color_to_int: dict[str, int] = {
            name: i + 1 for i, name in enumerate(color_names)
        }
        # Version JSON embarquée dans chaque message (référence pour le receveur)
        self._colors_ref: dict[str, str] = {
            str(i + 1): name for i, name in enumerate(color_names)
        }

        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        logger.info(
            "UdpSender prêt → %s:%d  %.1f Hz  couleurs=%s",
            config.host, config.port, config.rate_hz,
            list(color_names),
        )

    # ──────────────────────────────────────────────────────────────────────────

    def maybe_send(self, grid_colors: list[list[str | None]] | None) -> None:
        """Envoie le message si l'intervalle configuré est écoulé.

        grid_colors=None  → grille toute à zéro (plateau non détecté).
        """
        now = time.monotonic()
        if now - self._last_send < self._interval:
            return
        self._last_send = now
        self._seq += 1
        self._send(grid_colors)

    def close(self) -> None:
        self._sock.close()

    def __enter__(self) -> UdpSender:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    # ──────────────────────────────────────────────────────────────────────────

    def _send(self, grid_colors: list[list[str | None]] | None) -> None:
        if grid_colors is None:
            grid_int: list[list[int]] = [[0] * self._cols for _ in range(self._rows)]
        else:
            grid_int = [
                [self._color_to_int.get(cell, 0) for cell in row]
                for row in grid_colors
            ]

        payload = json.dumps(
            {"seq": self._seq, "colors": self._colors_ref, "grid": grid_int},
            separators=(",", ":"),   # JSON compact (pas d'espaces superflus)
        ).encode("utf-8")

        try:
            self._sock.sendto(payload, (self._config.host, self._config.port))
        except OSError as exc:
            logger.warning("UDP send échoué : %s", exc)
