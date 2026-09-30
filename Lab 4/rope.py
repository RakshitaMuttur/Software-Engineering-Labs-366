import math
import pygame


class Rope:
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.center_y = screen_height // 2
        self.center_x = screen_width // 2
        self.marker_x = screen_width // 2

        self.left_win_x = 180
        self.right_win_x = screen_width - 180
        self.pull_step = 12

        # Task 3: tension state (0.0 = slack, 1.0 = fully taut)
        self.pulse = 0.0

    # ------------------------------------------------------------------ pulling
    def pull_left(self, strength=1.0):
        self.marker_x -= int(self.pull_step * strength)
        self.pulse = min(1.0, self.pulse + 0.35)

    def pull_right(self, strength=1.0):
        self.marker_x += int(self.pull_step * strength)
        self.pulse = min(1.0, self.pulse + 0.35)

    def check_winner(self):
        if self.marker_x <= self.left_win_x:
            return "PLAYER"
        if self.marker_x >= self.right_win_x:
            return "COMPUTER"
        return None

    def reset(self):
        self.marker_x = self.screen_width // 2
        self.pulse = 0.0

    # ------------------------------------------------------------------ tension
    def progress(self):
        """Signed progress of the flag: +1 = at player's goal, -1 = at computer's goal."""
        half = self.center_x - self.left_win_x
        return max(-1.0, min(1.0, (self.center_x - self.marker_x) / half))

    def tension(self):
        """0..1 - rises the further the flag is from center and right after each pull."""
        return min(1.0, abs(self.progress()) * 0.7 + self.pulse * 0.5)

    def update(self):
        self.pulse = max(0.0, self.pulse - 0.03)

    def _rope_y(self, x, t_ms, tension):
        """Vertical offset of the rope at x: sag when slack, vibration when taut."""
        left, right = 60, self.screen_width - 60
        u = (x - left) / (right - left)                     # 0..1 along rope
        sag = (1.0 - tension) * 14 * math.sin(math.pi * u)  # slack rope droops
        amp = max(0.0, tension - 0.45) * 9                  # only vibrates when tense
        vib = amp * math.sin(u * 24 + t_ms * 0.04) * math.sin(math.pi * u)
        return self.center_y + sag + vib

    # ------------------------------------------------------------------- render
    def render(self, surface, t_ms=0):
        tension = self.tension()

        # Rope drawn as a polyline so it can sag / vibrate
        points = [
            (x, self._rope_y(x, t_ms, tension))
            for x in range(60, self.screen_width - 60 + 1, 8)
        ]
        # colour shifts from tan to reddish as it tightens
        rope_col = (
            180 + int(50 * tension),
            140 - int(50 * tension),
            90 - int(40 * tension),
        )
        pygame.draw.lines(surface, rope_col, False, points, 10)

        pygame.draw.line(
            surface, (50, 200, 50),
            (self.left_win_x, self.center_y - 40),
            (self.left_win_x, self.center_y + 40), 4,
        )
        pygame.draw.line(
            surface, (200, 50, 50),
            (self.right_win_x, self.center_y - 40),
            (self.right_win_x, self.center_y + 40), 4,
        )
        pygame.draw.line(
            surface, (120, 120, 120),
            (self.center_x, self.center_y - 20),
            (self.center_x, self.center_y + 20), 2,
        )

        # Flag rides on the rope
        fy = int(self._rope_y(self.marker_x, t_ms, tension))
        flag_rect = pygame.Rect(int(self.marker_x) - 12, fy - 24, 24, 48)
        pygame.draw.rect(surface, (230, 40, 40), flag_rect, border_radius=4)
        pygame.draw.rect(surface, (255, 255, 255), flag_rect, width=2, border_radius=4)
