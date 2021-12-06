import math
import sys
from dataclasses import dataclass
from pathlib import Path
from random import gauss, uniform, randint
from typing import List, Optional

import pygame

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

# This line tells python how to handle the relative imports
# when you run this file directly. Don't modify this line.
__package__ = "04-bouncing-bubbles." + Path(__file__).absolute().parent.name

# To import the modules in yourname/, you need to use relative imports,
# otherwise your project will not be compatible with the showcase.
from .utils import *

BACKGROUND = 0x0F1012
NB_BUBBLES = 2


class Bubble:
    MAX_VELOCITY = 5

    def __init__(self, position: pygame.Vector2 = None, size: float = 3, parent: 'Bubble' = None):
        self.size = size
        self.parent = parent
        # self.radius = int(gauss(25, 5))
        self.radius = randint(int(20 * size), int(40 * size))
        self.radius = int(40 * size)

        if position is None:
            # Default position is random.
            self.position = pygame.Vector2(
                randint(self.radius, SIZE[0] - self.radius),
                randint(self.radius, SIZE[1] - self.radius),
            )
        else:
            self.position = position if self.parent is None else self.parent.position

        # Set a random direction and a speed of around 3.
        self.velocity = pygame.Vector2()
        self.velocity.from_polar((gauss(3, 0.5), uniform(0, 360)))
        # self.velocity.x, self.velocity.y = 100, 100

        # Pick a random color with high saturation and value.
        self.color = pygame.Color(0)
        self.color.hsva = uniform(0, 360), 80, 80, 100

    @property
    def mass(self):
        return self.radius ** 2

    def draw(self, screen: pygame.Surface):
        pygame.draw.circle(screen, self.color, self.position, self.radius, 5)

    def move_away_from_mouse(self, mouse_pos: pygame.Vector2):
        if self.parent is not None:
            return
        """Apply a force on the bubble to move away from the mouse."""
        bubble_to_mouse = mouse_pos - self.position
        distance_to_mouse = bubble_to_mouse.length()
        if 0 < distance_to_mouse < 200:
            strength = chrange(distance_to_mouse, (0, 200), (1, 0), power=2)
            self.velocity -= bubble_to_mouse.normalize() * strength

    def move(self):
        """Move the bubble according to its velocity."""
        # We first limit the velocity to not get bubbles that go faster than what we can enjoy.
        if self.velocity.length() > self.MAX_VELOCITY:
            self.velocity.scale_to_length(self.MAX_VELOCITY)

        self.position += self.velocity
        debug.vector(self.velocity, self.position, scale=10)

    def collide_borders(self):
        # The first challenge is to make the bubbles bounce against the border.
        # Hover that doesn't mean that a bubble must always be completely inside of the screen:
        # If for instance it spawned on the edge, we don't want it to teleport so that it fits the screen,
        # we want everything to be *smooooth*.
        #
        # To be sure it is smooth, a good rule is to never modify self.position directly,
        # but instead modify self.velocity when needed.
        #
        # The second golden principle is to be lazy and not do anything if the collision will
        # resolve itself naturally in a few frames, that is, if the bubble is already moving
        # away from the wall.

        # TODO: handle collisions for each of the four edges.

        # this is done to make smooth collisions
        # for rough collisions a simple way is to use self.velocity.x *= -1

        if self.position.x - self.radius < 0:
            self.velocity.x += -(self.position.x - self.radius) / (self.radius // 5)
        if self.position.x + self.radius > SIZE[0]:
            self.velocity.x -= -(SIZE[0] - self.position.x - self.radius) / (self.radius // 5)

        if self.position.y - self.radius < 0:
            self.velocity.y += -(self.position.y - self.radius) / (self.radius // 5)
        if self.position.y + self.radius > SIZE[1]:
            self.velocity.y -= -(SIZE[1] - self.position.y - self.radius) / (self.radius // 5)

        if not "self-resolving collision with left wall":
            self.velocity.x *= -1
        ...

        # Remove this. It is only a placeholder to keep the bubble inside the screen
        # self.position.x %= SIZE[0]
        # self.position.y %= SIZE[1]

    def collide(self, other: "Bubble") -> Optional["Collision"]:
        """Get the collision data if there is a collision with the other Bubble"""
        # distance = self.get_distance((other.position.x, other.position.y), (self.position.x, self.position.y))
        distance = self.position.distance_to(other.position)

        # recursively checks if a bubble has another bubble as eventual parent or not
        def get_parent(bubble: Bubble, parent):
            if bubble.parent == parent:
                return True
            if bubble.parent is not None:
                if get_parent(bubble.parent, parent):
                    return True
            return False

        if self.parent is other or other.parent is self:
            if debug.enabled:
                print(distance)
            if distance >= abs(other.radius - self.radius):
                midpoint = pygame.Vector2(self.position.x / 2 + other.position.x / 2, self.position.y / 2 + other.position.y / 2)
                return Collision(self, other, midpoint, distance)
        else:
            if not get_parent(self, other) and not get_parent(other, self):
                if distance <= self.radius + other.radius:
                    midpoint = pygame.Vector2(self.position.x / 2 + other.position.x / 2, self.position.y / 2 + other.position.y / 2)
                    return Collision(self, other, midpoint, distance)
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
    # normal: pygame.Vector2
    distance: float

    def resolve(self):
        """Apply a force on both colliding object to help them move out of collision."""

        # The second part of the Ambitious challenge is to resolve the collisions that we have collected.
        # (See below in World.logic for how all this is put together).

        # TODO: Resolve the collision.

        # self.second.velocity += pygame.Vector2(-self.first.mass,-self.first.mass)
        # self.first.velocity += pygame.Vector2(-self.second.mass,-self.second.mass)

        # impart velocity from 2nd to first
        difference1 = (self.first.position - self.second.position)
        difference2 = (self.second.position - self.first.position)

        if self.distance != 0:
            difference1.normalize_ip()
            difference2.normalize_ip()

        if self.first.parent is self.second or self.second.parent is self.first:
            difference1 *= -1
            difference2 *= -1
            if self.first.parent is self.second:
                difference2 *= 0.5
            else:
                difference1 *= 0.5

        difference1 *= self.second.radius * 0.15
        difference2 *= self.first.radius * 0.15

        self.first.velocity += difference1
        self.second.velocity += difference2

        # Resolving a collision, here, means to modify the velocity of the two bubbles
        # so that they move out of collision. Not necessarly in one frame, but if
        # they move away from each other for say 2-5 frames, the collision will be resolved.

        # To do so, add a force to the velocity of each bubble to help the two bubbles to separate.
        # The separating force is perpendicular to the normal, similarly to how bubbles bounce
        # against a wall: only the part of the velocity perpendicular to the wall is reflected.
        # Keep in mind that one bubble an have multiple collisions at the same time.
        # You may need to define extra methods.
        # If you have troubles handling the mass of the particles, start by assuming they
        # have a mass of 1, and then upgrade your code to take the mass into account.

        ...


# The world is a list of bubbles.
class World(List[Bubble]):
    def __init__(self, nb):
        nb = 3
        super().__init__(Bubble(size=randint(2, 3)) for _ in range(nb))
        # self.append(Bubble(size=2, parent=self[0]))
        self.append(Bubble(size=0.5, parent=self[0]))
        self.append(Bubble(size=0.5, parent=self[0]))
        # self.generate_bubbles(4, 6)

    def generate_bubbles(self, size, qty):
        class LocalBubble:
            # local bubble class contains data to form a new bubble
            # this data is used to recursively generate new bubbles once all local bubbles have been generated
            def __init__(self, bubble_size):
                self.size = bubble_size
                self.bubbles = []
                self.generate_bubbles()

            def generate_bubbles(self):
                for _ in range(2 if self.size < 3 else 1):
                    if self.size >= 2:
                        self.bubbles.append(LocalBubble(bubble_size=self.size - 1.5))
                        # self.bubbles.append(LocalBubble(bubble_size=self.size - randint(1, self.size - 2)))

        bubbles = []
        for _ in range(qty):
            bubbles.append(LocalBubble(size))

        def return_bubbles(bubble_list, parent_bubble=None, list_to_add=()):
            for i in bubble_list:
                temp = Bubble(size=i.size, parent=parent_bubble)
                return_bubbles(i.bubbles, parent_bubble=temp, list_to_add=list_to_add)
                list_to_add.append(temp)

        return_bubbles(bubbles, list_to_add=self)

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
                if collision:
                    collisions.append(collision)

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
                world.generate_bubbles(5, 1)
                # world.append(Bubble(event.pos))
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
    wclib.run(mainloop())
