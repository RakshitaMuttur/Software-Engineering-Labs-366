import random
import pygame
from game.rope import Rope
from game.player import Puller

SUDDEN_DEATH_MS = 45_000      # Task 4
SURGE_THRESHOLD = 0.5         # Task 2: fraction of the way to the player's goal
PLAYER_PULL_STRENGTH = 1.1   # each keystroke pulls a bit harder than a computer tick


class GameEngine:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.rope = Rope(width, height)
        self.player = Puller(90, height // 2, (50, 120, 220), "PLAYER (A/D)", back_dir=-1)
        self.computer = Puller(width - 90, height // 2, (220, 80, 50), "COMPUTER", back_dir=1)

        self.last_key = None
        self.winner = None
        self.game_state = "PLAYING"

        self.base_cooldown = 180
        self.computer_pull_cooldown = self.base_cooldown
        self.computer_strength_boost = 1.0
        self.panic = False
        self.last_computer_pull = pygame.time.get_ticks()

        self.match_start = pygame.time.get_ticks()
        self.elapsed_ms = 0
        self.sudden_death = False

        self.font_big = pygame.font.SysFont(None, 48)
        self.font_small = pygame.font.SysFont(None, 26)

    # ------------------------------------------------------------------ input
    def handle_event(self, event):
        if self.game_state != "PLAYING":
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                self.reset()
            return

        # Task 1 FIX: the old is_pull_locked flag was only cleared on KEYUP of
        # last_key, so overlapping key presses froze input forever. Alternation
        # (event.key != last_key) alone is the debounce now - no lock needed.
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_a, pygame.K_d):
            if event.key != self.last_key:
                self.rope.pull_left(PLAYER_PULL_STRENGTH * self._pull_multiplier())
                self.last_key = event.key
                self.player.update_lean(self.player.lean, kick=0.12)

    def _pull_multiplier(self):
        return 2.0 if self.sudden_death else 1.0     # Task 4

    # ----------------------------------------------------------------- update
    def update(self):
        if self.game_state != "PLAYING":
            return

        now = pygame.time.get_ticks()
        self.elapsed_ms = now - self.match_start
        if not self.sudden_death and self.elapsed_ms >= SUDDEN_DEATH_MS:
            self.sudden_death = True

        # Task 2: panic surge when the flag is dragged toward the player's goal
        self.panic = self.rope.progress() >= SURGE_THRESHOLD
        if self.panic:
            severity = (self.rope.progress() - SURGE_THRESHOLD) / (1 - SURGE_THRESHOLD)
            self.computer_pull_cooldown = int(self.base_cooldown * (0.9 - 0.1 * severity))
            self.computer_strength_boost = 1.05 + 0.1 * severity
        else:
            self.computer_pull_cooldown = self.base_cooldown
            self.computer_strength_boost = 1.0

        if now - self.last_computer_pull >= self.computer_pull_cooldown:
            computer_variance = random.uniform(0.7, 1.2)
            self.rope.pull_right(
                computer_variance * self.computer_strength_boost * self._pull_multiplier()
            )
            self.last_computer_pull = now
            self.computer.update_lean(self.computer.lean, kick=0.12)

        # Task 3: lean toward whoever has momentum, and ease rope tension
        m = self.rope.progress()                      # +1 player winning, -1 computer winning
        self.player.update_lean(max(0.0, min(1.0, 0.4 + 0.6 * m)))
        self.computer.update_lean(max(0.0, min(1.0, 0.4 - 0.6 * m)))
        self.rope.update()

        result = self.rope.check_winner()
        if result:
            self.winner = result
            self.game_state = "GAME_OVER"

    def reset(self):
        self.rope.reset()
        self.last_key = None
        self.winner = None
        self.game_state = "PLAYING"
        self.computer_pull_cooldown = self.base_cooldown
        self.computer_strength_boost = 1.0
        self.panic = False
        self.sudden_death = False
        self.elapsed_ms = 0
        self.player.lean = self.computer.lean = 0.3
        now = pygame.time.get_ticks()
        self.last_computer_pull = now
        self.match_start = now

    # ----------------------------------------------------------------- render
    def render(self, screen):
        screen.fill((30, 32, 36))

        mud_rect = pygame.Rect(self.width // 2 - 120, self.height // 2 - 80, 240, 160)
        pygame.draw.rect(screen, (45, 38, 30), mud_rect, border_radius=12)

        self.rope.render(screen, pygame.time.get_ticks())
        self.player.render(screen)
        self.computer.render(screen)

        # Task 4: match timer at the top
        secs = self.elapsed_ms / 1000
        timer_col = (255, 90, 90) if self.sudden_death else (240, 240, 240)
        timer_surf = self.font_big.render(f"TIME {secs:05.1f}s", True, timer_col)
        screen.blit(timer_surf, (self.width // 2 - timer_surf.get_width() // 2, 8))

        inst_surf = self.font_small.render(
            "Alternate [A] and [D] keys rapidly to pull!", True, (210, 210, 210)
        )
        screen.blit(inst_surf, (self.width // 2 - inst_surf.get_width() // 2, 56))

        if self.sudden_death and (pygame.time.get_ticks() // 300) % 2 == 0:
            sd = self.font_small.render("SUDDEN DEATH - PULLS x2!", True, (255, 70, 70))
            screen.blit(sd, (self.width // 2 - sd.get_width() // 2, 82))
        elif self.panic and self.game_state == "PLAYING":
            pn = self.font_small.render("COMPUTER PANIC SURGE!", True, (255, 170, 60))
            screen.blit(pn, (self.width // 2 - pn.get_width() // 2, 82))

        if self.game_state == "GAME_OVER":
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))

            win_text = f"{self.winner} WINS!"
            color = (80, 220, 80) if self.winner == "PLAYER" else (240, 80, 80)
            text_surf = self.font_big.render(win_text, True, color)
            screen.blit(
                text_surf,
                (self.width // 2 - text_surf.get_width() // 2, self.height // 2 - 50)
            )

            restart_surf = self.font_small.render(
                "Press [R] to Play Again", True, (240, 240, 240)
            )
            screen.blit(
                restart_surf,
                (self.width // 2 - restart_surf.get_width() // 2, self.height // 2 + 10)
            )