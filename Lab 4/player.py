import math
import pygame


class Puller:
    """Represents a puller character anchor on either side of the rope."""

    MAX_LEAN_DEG = 28

    def __init__(self, x, y, color, label, back_dir=-1):
        """back_dir: -1 if 'backwards' is screen-left (player), +1 if screen-right."""
        self.x = x
        self.y = y
        self.color = color
        self.label = label
        self.back_dir = back_dir
        self.lean = 0.3          # 0 = upright, 1 = leaning fully back
        self.font = pygame.font.SysFont(None, 24)

    def update_lean(self, target, kick=0.0):
        """Ease toward the target lean; `kick` adds a quick jerk when the puller pulls."""
        self.lean += (target - self.lean) * 0.15
        self.lean = max(0.0, min(1.0, self.lean + kick))

    def _rot(self, px, py, pivot, angle):
        dx, dy = px - pivot[0], py - pivot[1]
        c, s = math.cos(angle), math.sin(angle)
        return (pivot[0] + dx * c - dy * s, pivot[1] + dx * s + dy * c)

    def render(self, surface):
        """Draw avatar (tilted about its feet) and label."""
        pivot = (self.x, self.y + 35)
        # A positive angle tips the top of the body to screen-right, so multiply by back_dir.
        angle = math.radians(self.MAX_LEAN_DEG) * self.lean * self.back_dir

        # Body: rotated rectangle
        x0, x1, y0, y1 = self.x - 20, self.x + 20, self.y - 35, self.y + 35
        corners = [self._rot(px, py, pivot, angle)
                   for px, py in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))]
        pygame.draw.polygon(surface, self.color, corners)

        # Arm reaching toward the rope
        shoulder = self._rot(self.x, self.y - 25, pivot, angle)
        grip_x = self.x - self.back_dir * 45
        pygame.draw.line(surface, (240, 210, 180), shoulder, (grip_x, self.y - 5), 6)

        # Head
        head = self._rot(self.x, self.y - 50, pivot, angle)
        pygame.draw.circle(surface, (240, 210, 180), (int(head[0]), int(head[1])), 16)

        # Name / control tag (stays upright)
        label_surf = self.font.render(self.label, True, (240, 240, 240))
        surface.blit(label_surf, (self.x - label_surf.get_width() // 2, self.y + 45))
