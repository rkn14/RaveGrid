"""Interface (Protocol) pour toute source d'images."""

from __future__ import annotations

from typing import Protocol

import numpy as np


class FrameSource(Protocol):
    """Port d'acquisition d'images — indépendant d'OpenCV."""

    def read(self) -> tuple[bool, np.ndarray]:
        """Retourne (succès, frame BGR)."""
        ...

    def release(self) -> None:
        """Libère la ressource matérielle."""
        ...

    @property
    def is_opened(self) -> bool:
        """True si la source est prête à fournir des images."""
        ...
