import sys
from pathlib import Path
from random import gauss, uniform, randint
from typing import List, Optional

import math

import pygame
import pygame.gfxdraw

# This line tells python how to handle the relative imports
# when you run this file directly. Don't modify this line.
__package__ = "04-bouncing-bubbles." + Path(__file__).absolute().parent.name

# To import the modules in yourname/, you need to use relative imports,
# otherwise your project will not be compatible with the showcase.
from .utils import *

BACKGROUND = 0x0F1012
NB_BUBBLES = 10


class Bubble:
    AVERAGE_RECURSIVITY = 1
    RECURSIVITY_RANDOMNESS = 1
    MAX_RECURSIVITY = 2
    AVERAGE_RADIUS = 80
    RADIUS_RANDOMNESS = 5
    BOUNCE_VELOCITY = 0.5

    def __init__(
        self,
        position: Optional[pygame.Vector2] = None,
        parent: "Bubble" = None,
    ):
        self.depth = (parent.depth if parent else 0) + 1
        self.parent = parent
        self.radius = abs(int(gauss(self.AVERAGE_RADIUS, self.RADIUS_RANDOMNESS))) + 1
        self.bounce = 0
        if parent:
            self.radius = abs(
                int(
                    parent.radius // 3 + randint(
                        -self.RADIUS_RANDOMNESS//self.depth, self.RADIUS_RANDOMNESS//self.depth
                    )
                )
            ) + 1
        self.inner = (
            World(
                abs(int(gauss(self.AVERAGE_RECURSIVITY, self.RECURSIVITY_RANDOMNESS))),
                self,
            )
            if self.depth <= self.MAX_RECURSIVITY
            else None
        )
        self.size = 2 * (parent.radius * 2,) if parent else SIZE

        if position is None:
            # Default position is random.
            self.position = pygame.Vector2(
                randint(
                    self.radius,
                    (self.size[0] if not parent else 2 * parent.radius) - self.radius,
                ),
                randint(self.radius, (self.size[1]) - self.radius),
            )
        else:
            self.position = position

        # Set a random direction and a speed of around World.HEAT.
        self.velocity = pygame.Vector2()
        self.velocity.from_polar((gauss(World.HEAT, 0.5), uniform(0, 360)))

        # Pick a random color with high saturation and value.
        self.color = pygame.Color(0)
        self.color.hsva = uniform(0, 360), 80, 100, 100

        self.to_resolve: Optional[Collision] = None

    @property
    def mass(self) -> float:
        return 1 if not self.radius else self.radius ** 2

    @property
    def temperature(self):
        return self.velocity.length()

    @property
    def absolute_position(self):
        if self.parent:
            return (
                self.position
                + self.parent.absolute_position
                - pygame.Vector2(self.parent.radius)
            )
        else:
            return self.position

    def draw(self, screen: pygame.Surface):
        pygame.gfxdraw.circle(
            screen,
            int(self.absolute_position.x),
            int(self.absolute_position.y),
            int(self.radius + 3*math.sin(self.bounce)) if self.radius + self.bounce > 1 else 1,
            self.color,
        )
        if self.inner:
            for bubble in self.inner:
                bubble.draw(screen)

    def move_away_from_mouse(self, mouse_pos: pygame.Vector2):
        """Apply a force on the bubble to move away from the mouse."""
        bubble_to_mouse = mouse_pos - self.position
        distance_to_mouse = bubble_to_mouse.length()
        if 0 < distance_to_mouse < 200:
            strength = chrange(distance_to_mouse, (0, 200), (World.HEAT, 0), power=2)
            self.velocity -= bubble_to_mouse.normalize() * strength

    def move(self, paused=False):
        """Move the bubble according to its velocity."""
        # We first limit the velocity to not get bubbles that go faster than what we can enjoy.
        if self.velocity.length() > (
            World.HEAT - self.depth if self.velocity.length() > 0 else 1
        ):
            self.velocity.scale_to_length(World.HEAT)

        if paused:
            return

        self.bounce += self.BOUNCE_VELOCITY
        self.position += self.velocity
        debug.vector(self.velocity, self.absolute_position, scale=10)

        if self.inner:
            for bubble in self.inner:
                bubble.move(paused)

    def collide_borders(self):
        if self.radius > self.position.x and self.velocity.x < 0:
            self.velocity.x *= -1
            self.velocity.x += 1 + World.HEAT
            self.velocity.scale_to_length(self.velocity.length() - World.FRICTION)
        elif self.position.x > self.size[0] - self.radius and self.velocity.x > 0:
            self.velocity.x *= -1
            self.velocity.x -= 1 + World.HEAT
            self.velocity.scale_to_length(self.velocity.length() - World.FRICTION)
        if self.radius > self.position.y and self.velocity.y < 0:
            self.velocity.y *= -1
            self.velocity.y += 1 + World.HEAT
            self.velocity.scale_to_length(self.velocity.length() - World.FRICTION)
        elif self.position.y > self.size[1] - self.radius and self.velocity.y > 0:
            self.velocity.y *= -1
            self.velocity.y -= 1 + World.HEAT
            self.velocity.scale_to_length(self.velocity.length() - World.FRICTION)
        if self.depth > 1:
            if (
                self.position.distance_to(pygame.Vector2(self.size[0] / 2))
                + self.radius
                > self.size[0] / 2
            ):
                self.velocity += pygame.Vector2(self.size)/2 - self.position
                self.velocity.scale_to_length(self.velocity.length() + World.HEAT - World.FRICTION)
        if self.inner:
            for bubble in self.inner:
                bubble.collide_borders()

    def collide(self, other: "Bubble"):
        """Get the collision data if there is a collision with the other Bubble"""
        if self.radius + other.radius > (self.position - other.position).length():
            self.to_resolve = Collision(self, other)
        if self.inner:
            self.inner.collide_bubbles()

    def resolve_collision(self):
        if self.to_resolve:
            self.to_resolve.resolve()
            self.to_resolve = None
        if self.inner:
            for bubble in self.inner:
                bubble.resolve_collision()


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

    def __init__(
        self,
        first: "Bubble",
        second: "Bubble",
    ):
        self.first = first
        self.second = second

    def resolve(self):
        """Apply a force on both colliding object to help them move out of collision."""

        self.first.velocity += (
            -2
            * self.second.mass
            / (self.first.mass + self.second.mass)
            * (self.first.velocity - self.second.velocity).dot(
                (self.first.position - self.second.position)
            )
            / (self.first.position - self.second.position).length_squared()
            * (self.first.position - self.second.position)
        )
        # self.first.velocity = self.first.velocity - 2 * self.second.mass / (
        #     self.first.mass + self.second.mass
        # ) * (self.first.velocity - self.second.velocity).dot(
        #     (self.first.position - self.second.position)
        # ) / (
        #     self.first.position - self.second.position
        # ).length_squared() * (
        #     self.first.position - self.second.position
        # )

        self.first.velocity = (
            self.first.velocity
            + (self.second.position - self.first.position).normalize()
            * (
                (self.second.position - self.first.position).length()
                - (self.first.radius + self.second.radius)
            )
        ).normalize() * (self.first.velocity.length())

        self.second.velocity += (
            -2
            * self.first.mass
            / (self.second.mass + self.first.mass)
            * (self.second.velocity - self.first.velocity).dot(
                (self.second.position - self.first.position)
            )
            / (self.second.position - self.first.position).length_squared()
            * (self.second.position - self.first.position)
        )
        # self.second.velocity = self.second.velocity - 2 * self.first.mass / (
        #     self.second.mass + self.first.mass
        # ) * (self.second.velocity - self.first.velocity).dot(
        #     (self.second.position - self.first.position)
        # ) / (
        #     self.second.position - self.first.position
        # ).length_squared() * (
        #     self.second.position - self.first.position
        # )

        self.second.velocity = (
            self.second.velocity
            + (self.first.position - self.second.position).normalize()
            * (
                (self.first.position - self.second.position).length()
                - (self.second.radius + self.first.radius)
            )
        ).normalize() * (self.second.velocity.length())


# The world is a list of bubbles.
class World(List[Bubble]):
    FRICTION = 1
    HEAT = 3

    def __init__(self, nb, parent=None):
        super().__init__(Bubble(parent=parent) for _ in range(nb))

    def logic(self, mouse_position: pygame.Vector2, paused=False):
        """Handles the collision and evolution of all the objects."""
        for bubble in self:
            bubble.move(paused)
            bubble.collide_borders()
            bubble.move_away_from_mouse(mouse_position)

        self.collide_bubbles()
        for bubble in self:
            bubble.resolve_collision()

    def collide_bubbles(self):
        for i, b1 in enumerate(self):
            for b2 in self[i + 1 :]:
                b1.collide(b2)

    def draw(self, screen):
        for bubble in self:
            bubble.draw(screen)

    @property
    def temperature(self):
        return int(sum((bubble.temperature for bubble in self)))

    @property
    def interaction(self):
        return len(self) * (len(self) + 1) // 2 + sum(
            bubble.inner.interaction for bubble in self if bubble.inner
        )


def mainloop():
    """
    Controls:
    [→]: increase FRICTION
    [←]: decrease FRICTION
    [↑]: increase HEAT
    [↓]: decrease HEAT
    [P]: pause
    """
    pygame.init()

    world = World(NB_BUBBLES)
    mouse_position = pygame.Vector2()
    fps_counter = FpsCounter(60, Bubbles=world)

    show_parameters = True
    paused = False

    while True:
        screen, events = yield
        for event in events:
            if event.type == pygame.QUIT:
                return
            elif event.type == pygame.MOUSEMOTION:
                mouse_position.xy = event.pos
            elif event.type == pygame.MOUSEBUTTONDOWN:
                world.append(Bubble(event.pos, parent=None))
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_h:
                    show_parameters = not show_parameters
                elif event.key == pygame.K_UP:
                    World.HEAT += 1
                    if World.HEAT > 100:
                        World.HEAT = 100
                elif event.key == pygame.K_DOWN:
                    World.HEAT -= 1
                    if World.HEAT <= 1:
                        World.HEAT = 1
                    if World.FRICTION > World.HEAT:
                        World.FRICTION = World.HEAT
                elif event.key == pygame.K_RIGHT:
                    World.FRICTION += 1
                    if World.FRICTION > World.HEAT:
                        World.FRICTION = World.HEAT
                elif event.key == pygame.K_LEFT:
                    World.FRICTION -= 1
                    if World.FRICTION < 0:
                        World.FRICTION = 0
                elif event.key == pygame.K_p:
                    paused = not paused

            debug.handle_event(event)
            fps_counter.handle_event(event)

        # Handle the collisions
        world.logic(mouse_position, paused)
        fps_counter.logic()

        # Drawing the screen
        screen.fill(BACKGROUND)
        pygame.draw.circle(
            screen, (50 + 2 * World.HEAT, 10, 10), pygame.mouse.get_pos(), 50
        )
        world.draw(screen)
        fps_counter.draw(screen)
        if show_parameters:
            color = "#89C4F4"
            t = text(f"WALL HEAT: {World.HEAT}", color)
            r = screen.blit(t, t.get_rect(topright=(SIZE[0] - 15, 15)))
            t = text(f"FRICTION: {World.FRICTION}", color)
            r = screen.blit(t, t.get_rect(topright=(SIZE[0] - 15, r.bottom)))
            t = text(f"TEMPERATURE: {world.temperature}", color)
            r = screen.blit(t, t.get_rect(topright=(SIZE[0] - 15, r.bottom)))
            t = text(f"INTERACTIONS: {world.interaction}", color)
            r = screen.blit(t, t.get_rect(topright=(SIZE[0] - 15, r.bottom)))
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
