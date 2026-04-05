"""Interface (Protocol) pour toute implémentation d'affichage."""

from __future__ import annotations

from typing import Protocol

import numpy as np


class Display(Protocol):
    """Port d'affichage — indépendant de pygame ou d'OpenCV."""

    def show(self, frame: np.ndarray) -> None:
        """Affiche une frame BGR à l'écran."""
        ...

    def handle_events(self) -> bool:
        """Traite les événements. Retourne False si l'utilisateur demande à quitter."""
        ...

    def close(self) -> None:
        """Ferme la fenêtre et libère les ressources."""
        ...
