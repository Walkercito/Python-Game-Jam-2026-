import pygame

from core.camera import SplitScreen
from core.config.constants import P1_KEYS, PLAYER_SCALE
from core.hud import ZoneAnnouncement
from core.map_loader import TMXMap
from core.network import GameClient, GameServer
from core.player import Player
from core.scene import Scene, SceneManager
from core.vfx import VFXAnimation, load_vfx_frames

BASE_MAP_SCALE = 4.0


class NetworkGameplay(Scene):
    def __init__(
        self,
        manager: SceneManager,
        client: GameClient,
        server: GameServer | None,
        is_host: bool,
    ) -> None:
        super().__init__(manager)
        self.client = client
        self.server = server
        self.is_host = is_host

        self.map = TMXMap("assets/tiled/tutorial_001.tmx")
        spawn_x = self.map.offset[0] + self.map.scaled_size[0] // 2
        spawn_y = self.map.offset[1] + self.map.scaled_size[1] // 2

        # Local player always uses WASD
        local_char = "green" if self.client.my_slot == 0 else "orange"
        remote_char = "orange" if self.client.my_slot == 0 else "green"
        local_outline = (255, 80, 80) if self.client.my_slot == 0 else (80, 130, 255)
        remote_outline = (80, 130, 255) if self.client.my_slot == 0 else (255, 80, 80)

        self.local_player = Player(
            spawn_x, spawn_y, keys=P1_KEYS, outline_color=local_outline, character=local_char
        )
        self.remote_player = Player(
            spawn_x, spawn_y, keys=P1_KEYS, outline_color=remote_outline, character=remote_char
        )

        self._sync_player_scale(self.local_player)
        self._sync_player_scale(self.remote_player)

        self.landing_frames = load_vfx_frames("assets/vfx/landing", scale=self.map.scale)
        self.vfx_list: list[VFXAnimation] = []
        self.split_screen = SplitScreen()
        self.zone_announcement = ZoneAnnouncement("Zone One", "Tutorial Valley")

    def _sync_player_scale(self, player: Player) -> None:
        new_scale = PLAYER_SCALE * (self.map.scale / BASE_MAP_SCALE)
        if abs(new_scale - player.current_scale) > 0.01:
            player.rescale(new_scale)

    def on_resize(self, width: int, height: int) -> None:
        old_scale = self.map.scale
        old_offset = self.map.offset
        self.map.rescale((width, height))

        for p in [self.local_player, self.remote_player]:
            rel_x = (p.pos.x - old_offset[0]) / old_scale
            rel_y = (p.pos.y - old_offset[1]) / old_scale
            p.pos.x = rel_x * self.map.scale + self.map.offset[0]
            p.pos.y = rel_y * self.map.scale + self.map.offset[1]
            p.rect.x = int(p.pos.x)
            p.rect.y = int(p.pos.y)
            self._sync_player_scale(p)

        self.landing_frames = load_vfx_frames("assets/vfx/landing", scale=self.map.scale)
        self.vfx_list.clear()

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            from core.scenes.pause import Pause

            self.manager.push(Pause(self.manager))

    def _send_local_state(self) -> None:
        self.client.send_state(
            {
                "x": self.local_player.pos.x,
                "y": self.local_player.pos.y,
                "vx": self.local_player.velocity.x,
                "vy": self.local_player.velocity.y,
                "state": self.local_player.state,
                "facing": self.local_player.facing_right,
                "on_ground": self.local_player.on_ground,
            }
        )

    def _apply_remote_state(self) -> None:
        rs = self.client.remote_state
        if not rs:
            return

        self.remote_player.pos.x = rs.get("x", self.remote_player.pos.x)
        self.remote_player.pos.y = rs.get("y", self.remote_player.pos.y)
        self.remote_player.velocity.x = rs.get("vx", 0)
        self.remote_player.velocity.y = rs.get("vy", 0)
        self.remote_player.rect.x = int(self.remote_player.pos.x)
        self.remote_player.rect.y = int(self.remote_player.pos.y)
        self.remote_player.facing_right = rs.get("facing", True)
        self.remote_player.on_ground = rs.get("on_ground", False)
        self.remote_player.state = rs.get("state", "idle")

    def update(self, dt: float) -> None:
        self.client.pump()

        if self.client.was_connected and not self.client.connected:
            from core.scenes.disconnected import Disconnected

            self.manager.replace(Disconnected(self.manager, "Connection to host lost"))
            return

        # Local player uses physics
        self.local_player.update(dt, self.map.collision_rects, self.map.water_rects)

        # Remote player gets network state (only if connected)
        if self.client.has_remote_player:
            self._apply_remote_state()
            self.remote_player._animate(dt)

        # Send local state
        self._send_local_state()

        # Landing VFX for local player
        if self.local_player.just_landed and self.landing_frames and not self.local_player.in_water:
            self.vfx_list.append(
                VFXAnimation(
                    self.landing_frames,
                    self.local_player.rect.centerx,
                    self.local_player.rect.bottom,
                )
            )

        for vfx in self.vfx_list:
            vfx.update(dt)
        self.vfx_list = [v for v in self.vfx_list if not v.finished]

        # Split-screen only when remote player is present
        if self.client.has_remote_player:
            self.split_screen.update(dt, self.local_player.rect, self.remote_player.rect)

        if self.zone_announcement and not self.zone_announcement.finished:
            self.zone_announcement.update(dt)

    def _draw_world(
        self,
        surface: pygame.Surface,
        cam_offset: tuple[int, int],
        view_size: tuple[int, int],
    ) -> None:
        surface.fill((14, 7, 27))
        self.map.draw(surface, cam_offset)
        self.local_player.draw(surface, cam_offset)
        if self.client.has_remote_player:
            self.remote_player.draw(surface, cam_offset)
        for vfx in self.vfx_list:
            vfx.draw(surface, cam_offset)

    def draw(self, surface: pygame.Surface) -> None:
        if self.client.has_remote_player:
            self.split_screen.render(
                surface, self._draw_world, self.local_player.rect, self.remote_player.rect
            )
        else:
            # Solo mode — no split, single camera
            sw, sh = surface.get_size()
            self.split_screen.shared_cam.follow_rect(self.local_player.rect, sw, sh)
            self.split_screen.shared_cam.update(1 / 60)
            self._draw_world(surface, self.split_screen.shared_cam.offset, (sw, sh))

        if self.zone_announcement and not self.zone_announcement.finished:
            self.zone_announcement.draw(surface)
