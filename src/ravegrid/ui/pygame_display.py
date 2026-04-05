"""Implémentation Display basée sur pygame."""

from __future__ import annotations

import cv2
import numpy as np
import pygame

from ..config.schema import WindowConfig


class PygameDisplay:
    """Fenêtre pygame affichant les frames OpenCV (BGR → RGB).

    Raccourcis clavier :
      F11   — basculer plein écran / fenêtré
      Échap — quitter
    """

    def __init__(self, config: WindowConfig) -> None:
        pygame.init()
        self._windowed_size = (config.width, config.height)
        self._fullscreen = config.fullscreen
        self._screen = self._create_surface()
        pygame.display.set_caption(config.title)
        self._clock = pygame.time.Clock()

    # ------------------------------------------------------------------
    # Interne

    def _create_surface(self) -> pygame.Surface:
        if self._fullscreen:
            return pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        return pygame.display.set_mode(self._windowed_size, pygame.RESIZABLE)

    def _toggle_fullscreen(self) -> None:
        self._fullscreen = not self._fullscreen
        self._screen = self._create_surface()

    # ------------------------------------------------------------------
    # Interface Display

    def show(self, frame: np.ndarray) -> None:
        """Convertit BGR → RGB, adapte à la taille de la fenêtre et affiche."""
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        w, h = self._screen.get_size()
        surface = pygame.image.frombuffer(rgb.tobytes(), (rgb.shape[1], rgb.shape[0]), "RGB")
        scaled = pygame.transform.scale(surface, (w, h))
        self._screen.blit(scaled, (0, 0))
        pygame.display.flip()
        self._clock.tick(60)

    def handle_events(self) -> bool:
        """Retourne False si l'utilisateur ferme la fenêtre ou appuie sur Échap."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                if event.key == pygame.K_F11:
                    self._toggle_fullscreen()
        return True

    def close(self) -> None:
        pygame.quit()

    def __enter__(self) -> PygameDisplay:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
