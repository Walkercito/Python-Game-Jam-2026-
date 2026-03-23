import pygame

from core.config.constants import FPS, TITLE
from core.config.game_settings import settings
from core.gui import FONT_PATH
from core.scene import SceneManager
from core.scenes.main_menu import MainMenu


class Engine:
    def __init__(self) -> None:
        pygame.init()
        pygame.mixer.init()
        self.screen = settings.apply_display_mode()
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.running = True
        self.scene_manager = SceneManager()
        self.scene_manager.push(MainMenu(self.scene_manager))
        settings.consume_dirty()
        self._fps_font = pygame.font.Font(FONT_PATH, 14)

    def run(self) -> None:
        while self.running:
            dt = self.clock.get_time() / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    break
                self.scene_manager.handle_event(event)

            if settings.consume_dirty():
                self.screen = pygame.display.get_surface()
                self.scene_manager.notify_resize(*settings.screen_size)

            self.scene_manager.update(dt)
            self.scene_manager.draw(self.screen)

            if settings.show_fps:
                fps_text = self._fps_font.render(
                    f"{self.clock.get_fps():.0f} FPS", True, (200, 200, 200)
                )
                self.screen.blit(fps_text, (8, 8))

            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()
