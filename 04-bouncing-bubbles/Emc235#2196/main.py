import sys
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
NB_BUBBLES = 50


class Bubble:
    MAX_VELOCITY = 7

    def __init__(self, position=None):
        self.radius = int(gauss(25, 5))

        if position is None:
            # Default position is random.
            self.position = pygame.math.Vector2(
                randint(self.radius + 1, SIZE[0] - self.radius - 1),
                randint(self.radius + 1, SIZE[1] - self.radius - 1),
            )
        else:
            self.position = pygame.math.Vector2(
                min(max(position[0], self.radius + 1), SIZE[0] - self.radius - 1),
                min(max(position[1], self.radius + 1), SIZE[1] - self.radius - 1)
            )
            self.position = pygame.math.Vector2(position)

        # Set a random direction and a speed of around 3.
        self.velocity = pygame.Vector2()
        self.velocity.from_polar((gauss(3, 0.5), uniform(0, 360)))

        # Pick a random color with high saturation and value.
        self.color = pygame.Color(0)
        self.color.hsva = uniform(0, 360), 80, 80, 100

    @property
    def mass(self):
        return self.radius ** 2

    def draw(self, screen: pygame.Surface):
        pygame.draw.circle(screen, self.color, self.position, self.radius)

    def move_away_from_mouse(self, mouse_pos: pygame.Vector2):
        bubble_to_mouse = mouse_pos - self.position
        distance_to_mouse = bubble_to_mouse.length()
        if 0 < distance_to_mouse < 200:
            self.velocity -= bubble_to_mouse.normalize() * chrange(distance_to_mouse, (0, 200), (1, 0), power=2)

    def move(self):
        """Move the bubble according to its velocity."""
        # We first limit the velocity to not get bubbles that go faster than what we can enjoy.
        if self.velocity.length() > self.MAX_VELOCITY:
            self.velocity.scale_to_length(self.MAX_VELOCITY)
        self.position += debug.vector(self.velocity, self.position, scale=10)

    def collide_borders(self):
        if self.position.x < self.radius:
            if self.velocity.x < 0:  self.velocity.x *= -1
            else: self.velocity.x += 1
        if self.position.x > SIZE[0] - self.radius:
            if self.velocity.x > 0:  self.velocity.x *= -1
            else: self.velocity.x -= 1
        if self.position.y < self.radius:
            if self.velocity.y < 0:  self.velocity.y *= -1
            else: self.velocity.y += 1
        if self.position.y > SIZE[1] - self.radius:
            if self.velocity.y > 0:  self.velocity.y *= -1
            else: self.velocity.y -= 1

        # Remove this. It is only a placeholder to keep the bubble inside the screen
        # self.position.x %= SIZE[0]  # cool way to do world wrapping!
        # self.position.y %= SIZE[1]  # cool way to do world wrapping!

    def collide(self, other: "Bubble") -> Optional["Collision"]:
        """Get the collision data if there is a collision with the other Bubble"""
        if self is not other and (self.position - other.position).magnitude() < self.radius + other.radius:
            return Collision(self, other)


class Collision:
    def __init__(self, b1, b2) -> None:
        self.b1: Bubble = b1
        self.b2: Bubble = b2

    def resolve(self) -> None:
        # i mean... why not
        b1, b2 = self.b1, self.b2
        dX = b1.position - b2.position
        offset = (dX.magnitude() - (b1.radius + b2.radius)) / 2
        b1.position += -1 * dX/dX.magnitude() * offset
        b2.position +=  dX/dX.magnitude() * offset
        M = b1.mass + b2.mass
        b1.velocity += (
            (-2 * b2.mass / M)
            * (b1.velocity - b2.velocity).dot(b1.position - b2.position)
            / dX.magnitude_squared() * (b1.position - b2.position)
        )
        b2.velocity += (
            (-2 * b1.mass / M)
            * (b2.velocity - b1.velocity).dot(b2.position - b1.position)
            / dX.magnitude_squared() * (b2.position - b1.position)
        )


# The world is a list of bubbles.
class World(List[Bubble]):
    def __init__(self, nb):
        super().__init__(Bubble() for _ in range(nb))

    def logic(self, mouse_position: pygame.Vector2):
        """Handles the collision and evolution of all the objects."""

        # Second part of the ambitious challenge is to make the algorithm that solves the collisions.
        # A part of it is already provided so that you can focus on the important part.

        # We start by moving the bubbles and do the collisions with the static objects, the walls.
        for bubble in self:
            bubble.move()
            bubble.collide_borders()
            bubble.move_away_from_mouse(mouse_position)

        for cl in [b1.collide(b2) for i, b1 in enumerate(self) for b2 in self]:
            if cl: cl.resolve()

    def draw(self, screen):
        for bubble in self:
            bubble.draw(screen)


def mainloop():
    pygame.init()

    world = World(NB_BUBBLES)
    mouse_position = pygame.math.Vector2(pygame.mouse.get_pos())

    fps_counter = FpsCounter(60, Bubbles=world)
    while True:
        screen, events = yield
        for event in events:
            if event.type == pygame.QUIT:
                return
            elif event.type == pygame.MOUSEMOTION:
                mouse_position.xy = event.pos
            elif event.type == pygame.MOUSEBUTTONDOWN:
                world.append(Bubble(event.pos))
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
