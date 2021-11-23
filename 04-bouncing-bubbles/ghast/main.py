import sys
from dataclasses import dataclass
from pathlib import Path
from random import gauss, uniform, randint
from typing import List, Optional

import pygame

# This line tells python how to handle the relative imports
# when you run this file directly. Don't modify this line.
__package__ = "04-bouncing-bubbles." + Path(__file__).absolute().parent.name

# To import the modules in yourname/, you need to use relative imports,
# otherwise your project will not be compatible with the showcase.
from .utils import *

BACKGROUND = 0x0F1012
NB_BUBBLES = 10
MAX_RADIUS = 150
FRICTION = 0.999
WALL_CORRECTION_FACTOR = 0.5

FORCE_STAY_INSIDE_PARENT = True

CORRECTION_FACTORS = [10, 5, 2.5, 1, 0.5]
MAX_CHILDREN = [5, 3, 2, 1]


class Bubble:
    MAX_VELOCITY = 5

    def __init__(self, r: float, xy: pygame.Vector2, color=None, parent: 'Bubble' = None):
        self.r = r
        self.xy = xy

        self.parent = parent
        if self.parent is not None:
            self.parent._add_child(self)
        self.depth = 0 if self.parent is None else self.parent.depth + 1

        # Set a random direction and a speed of around 3.
        self.v_xy = pygame.Vector2() if parent is None else pygame.Vector2(parent.v_xy)

        motion = pygame.Vector2()
        motion.from_polar((gauss(3, 0.5), uniform(0, 360)))
        self.v_xy += motion / (5 * self.depth + 1)

        # Pick a random color with high saturation and value.
        if color is None:
            if self.parent is not None:
                self.color = self.parent.color.lerp((255, 255, 255), max(0, min(1, gauss(0.25, 0.15))))
            else:
                self.color = pygame.Color(0)
                self.color.hsva = uniform(0, 360), 80, 80, 100
        else:
            self.color = color

        self.children = []

    def _add_child(self, bubble):
        self.children.append(bubble)

    @property
    def mass(self):
        return self.r ** 2

    def draw(self, screen: pygame.Surface, constrain_inside_circle=None):
        xy_to_use = pygame.Vector2(self.xy)

        if FORCE_STAY_INSIDE_PARENT and constrain_inside_circle is not None:
            # trick to force children to stay within parent (while drawing)~
            c_xy, c_r = constrain_inside_circle
            extruding = (xy_to_use - c_xy).magnitude() + self.r - c_r
            if extruding > 0:
                xy_to_use += extruding * ((c_xy - xy_to_use).normalize())

        for c in self.children:
            c.draw(screen, constrain_inside_circle=(xy_to_use, self.r))
        pygame.draw.circle(screen, self.color, xy_to_use, self.r, width=1)

    def move_away_from_mouse(self, mouse_pos: pygame.Vector2):
        """Apply a force on the bubble to move away from the mouse."""
        bubble_to_mouse = mouse_pos - self.xy
        distance_to_mouse = bubble_to_mouse.length()
        if 0 < distance_to_mouse < 200:
            strength = chrange(distance_to_mouse, (0, 200), (1, 0), power=2)
            self.v_xy -= bubble_to_mouse.normalize() * strength
        for c in self.children:
            c.move_away_from_mouse(mouse_pos)

    def move(self):
        """Move the bubble according to its velocity."""
        # We first limit the velocity to not get bubbles that go faster than what we can enjoy.
        if self.v_xy.length() > self.MAX_VELOCITY:
            self.v_xy.scale_to_length(self.MAX_VELOCITY)

        self.xy += self.v_xy
        debug.vector(self.v_xy, self.v_xy, scale=10)

        for c in self.children:
            c.move()

        self.v_xy *= FRICTION

    def collide_borders(self):
        if self.parent is None:
            # top-level bubble, bounce off screen borders
            if self.xy[0] - self.r < 0:
                self.v_xy[0] -= (self.xy[0] - self.r) * WALL_CORRECTION_FACTOR
            elif self.xy[0] + self.r >= SIZE[0]:
                self.v_xy[0] -= (self.xy[0] + self.r - SIZE[0]) * WALL_CORRECTION_FACTOR

            if self.xy[1] - self.r < 0:
                self.v_xy[1] -= (self.xy[1] - self.r) * WALL_CORRECTION_FACTOR
            elif self.xy[1] + self.r >= SIZE[1] and self.v_xy[1] > 0:
                self.v_xy[1] -= (self.xy[1] + self.r - SIZE[1]) * WALL_CORRECTION_FACTOR
        else:
            extruding = (self.xy - self.parent.xy).magnitude() + self.r - self.parent.r
            if extruding > 0:
                # push child towards parent
                pcnt_child_extruding = min(1.0, extruding / self.r)
                self.v_xy += CORRECTION_FACTORS[self.depth] * pcnt_child_extruding * (self.parent.xy - self.xy).normalize()

                # push parent towards child
                pcnt_parent_extruding = min(1.0, extruding / self.parent.r)
                self.parent.v_xy += CORRECTION_FACTORS[self.depth] * pcnt_parent_extruding * (self.xy - self.parent.xy).normalize()

        for c in self.children:
            c.collide_borders()

    def all_child_collisions(self):
        for i, c1 in enumerate(self.children):
            for c2 in self.children[i + 1:]:
                coll = c1.collide(c2)
                if coll is not None:
                    yield coll
            for sub_collision in c1.all_child_collisions():
                yield sub_collision

    def collide(self, other: "Bubble") -> Optional["Collision"]:
        """Get the collision data if there is a collision with the other Bubble"""
        if 0 < self.xy.distance_to(other.xy) < self.r + other.r:
            return Collision(first=self,
                             second=other,
                             center=(self.xy + other.xy) / 2,
                             normal=(self.xy - other.xy).rotate(90).normalize())
        else:
            return None


# The second challenge contains two parts.
# The first one is to generate a list of all the collisions
# between bubbles.
# The data for a collision is stored into the Collision class below,
# and is generated by the Bubble.collide method above.
# The second part is then to process those collision data, and resolve them.

@dataclass
class Collision:
    """
    The data of a collision consist of four attributes.

    [first] and [second] are the the two objects that collided.
    [center] is the collision point, that is, the point from which you
        would like to push both circles away from. It corresponds to the center
        of the overlapping area of the two moving circles, which is also the
        midpoint between the two centers.
    [normal] is the axis along which the two circles should bounce. That is,
        if two bubbles move horizontally they bounce against the vertical axis,
        so normal would be a vertical vector.
    """

    first: "Bubble"
    second: "Bubble"
    center: pygame.Vector2
    normal: pygame.Vector2

    def resolve(self):
        """Apply a force on both colliding object to help them move out of collision."""
        xy1 = self.first.xy
        xy2 = self.second.xy
        depth = self.first.depth  # both must have the same depth

        # bit of a hack here to avoid mass calculations - use the overlap distance's ratio to the bubble's radius
        # to scale the impulse, meaning larger bubbles will tend to get pushed less.
        overlap = (self.first.r + self.second.r) - xy1.distance_to(xy2)
        pcnt_overlap_1 = min(1.0, overlap / self.first.r)
        pcnt_overlap_2 = min(1.0, overlap / self.second.r)

        correction1 = CORRECTION_FACTORS[depth] * pcnt_overlap_1 * (xy1 - xy2).normalize()
        correction2 = CORRECTION_FACTORS[depth] * pcnt_overlap_2 * (xy2 - xy1).normalize()

        self.first.v_xy += correction1
        self.second.v_xy += correction2


def gen_bubble(xy=None, depth=0, max_radius=MAX_RADIUS, parent=None):
    r = randint(1 + max_radius // 3, max_radius)
    n_children = 0 if depth >= len(MAX_CHILDREN) else randint(0, MAX_CHILDREN[depth])

    if xy is not None:
        pass
    elif parent is None:
        xy = pygame.Vector2(randint(r, SIZE[0] - r), randint(r, SIZE[1] - r))
    else:
        offs = pygame.Vector2(1, 0).rotate(randint(0, 360))
        offs.scale_to_length(parent.r - r)
        xy = parent.xy + offs

    res = Bubble(r, xy, parent=parent)
    if n_children > 0:
        child_max_radius = int(0.9 * r // (n_children))
        if child_max_radius >= 15:
            for _ in range(n_children):
                gen_bubble(depth=depth + 1, max_radius=child_max_radius, parent=res)

    return res


# The world is a list of bubbles.
class World(List[Bubble]):
    def __init__(self, nb):
        super().__init__([gen_bubble() for _ in range(nb)])

    def logic(self, mouse_position: pygame.Vector2):
        """Handles the collision and evolution of all the objects."""

        # Second part of the ambitious challenge is to make the algorithm that solves the collisions.
        # A part of it is already provided so that you can focus on the important part.

        # We start by moving the bubbles and do the collisions with the static objects, the walls.
        for bubble in self:
            bubble.move()
            bubble.collide_borders()
            bubble.move_away_from_mouse(mouse_position)

        # Then we check each pair of bubbles to collect all collisions.
        collisions = []
        for i, b1 in enumerate(self):
            for b2 in self[i + 1:]:
                collision = b1.collide(b2)
                if collision is not None:
                    collisions.append(collision)
            for c in b1.all_child_collisions():
                collisions.append(c)

        # And finally we resolve them all at once, so that it doesn't impact the detection of collision.
        for collision in collisions:
            collision.resolve()

    def draw(self, screen):
        for bubble in self:
            bubble.draw(screen)


def mainloop():
    pygame.init()

    world = World(NB_BUBBLES)

    mouse_position = pygame.Vector2()

    fps_counter = FpsCounter(60, Bubbles=world)
    while True:
        screen, events = yield
        for event in events:
            if event.type == pygame.QUIT:
                return
            elif event.type == pygame.MOUSEMOTION:
                mouse_position.xy = event.pos
            elif event.type == pygame.MOUSEBUTTONDOWN:
                world.append(gen_bubble(xy=event.pos))
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    world = World(NB_BUBBLES)  # reset

            debug.handle_event(event)
            fps_counter.handle_event(event)

        # Handle the collisions
        world.logic(mouse_position)
        fps_counter.logic()

        # Drawing the screen
        screen.fill(BACKGROUND)
        world.draw(screen)
        fps_counter.draw(screen)
        debug.draw(screen)


# ---- Recommended: don't modify anything below this line ---- #
if __name__ == "__main__":
    try:
        # Note: your editor might say that this is an error, but it's not.
        # Most editors can't understand that we are messing with the path.
        import wclib
    except ImportError:
        # wclib may not be in the path because of the architecture
        # of all the challenges and the fact that there are many
        # way to run them (through the showcase, or on their own)
        ROOT_FOLDER = Path(__file__).absolute().parent.parent.parent
        sys.path.append(str(ROOT_FOLDER))
        import wclib

    wclib.run(mainloop())
