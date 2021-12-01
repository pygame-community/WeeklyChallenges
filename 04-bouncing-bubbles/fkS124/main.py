import math
import sys
from dataclasses import dataclass
from pathlib import Path
from random import gauss, uniform, randint, random
from typing import List, Optional
from math import cos, sin, pi
from copy import copy
import numpy as np
from itertools import combinations

import pygame

# This line tells python how to handle the relative imports
# when you run this file directly. Don't modify this line.
__package__ = "04-bouncing-bubbles." + Path(__file__).absolute().parent.name

# To import the modules in yourname/, you need to use relative imports,
# otherwise your project will not be compatible with the showcase.
from .utils import *

BACKGROUND = 0x0F1012
NB_BUBBLES = 20


class Bubble:

    def __init__(self, x, y, vx, vy, radius, color):

        self.pos = np.array((x, y))
        self.vel = np.array((vx, vy))
        self.radius = radius
        self.color = color

    @property
    def x(self):
        return self.pos[0]

    @x.setter
    def x(self, value):
        self.pos[0] = value

    @property
    def y(self):
        return self.pos[1]

    @y.setter
    def y(self, value):
        self.pos[1] = value

    @property
    def vx(self):
        return self.vel[0]

    @vx.setter
    def vx(self, value):
        self.vel[0] = value

    @property
    def vy(self):
        return self.vel[1]

    @vy.setter
    def vy(self, value):
        self.vel[1] = value

    def overlaps(self, other):
        return np.hypot(*(self.pos- other.pos)) <= self.radius + other.radius

    def draw(self, DISPLAY):
        pygame.draw.circle(DISPLAY, self.color, (self.pos[0], self.pos[1]), self.radius)

    def move(self):
        self.pos += self.vel

        if self.x - self.radius + self.vx < 0:
            self.vx = -self.vx

        if self.x + self.radius + self.vx > SIZE[0]:
            self.vx = -self.vx

        if self.y - self.radius + self.vy < 0:
            self.vy = -self.vy

        if self.y + self.radius + self.vy > SIZE[1]:
            self.vy = -self.vy


class Sim:

    def __init__(self, n):

        def get_random_color():
            return (randint(0, 255), randint(0, 255), randint(0, 255))

        self.bubbles = []
        self.n = n

        for i in range(n):
            rad = int(gauss(40, 10))
            # Try to find a random initial position for this particle.
            while True:
                # Choose x, y so that the Particle is entirely inside the
                # domain of the simulation.
                x, y = self.fail_safe_pos(rad)
                # Choose a random velocity (within some reasonable range of
                # values) for the Particle.
                vx, vy = gauss(1, 1), gauss(1, 1)
                bubble = Bubble(x, y, vx, vy, rad, get_random_color())
                # Check that the Particle doesn't overlap one that's already
                # been placed.
                for p2 in self.bubbles:
                    if p2.overlaps(bubble):
                        break
                else:
                    self.bubbles.append(bubble)
                    break

    def fail_safe_pos(self, rad):
        x, y = random() * SIZE[0], random() * SIZE[1]
        if x < rad:
            x += float(rad)
        elif x > SIZE[0] - rad:
            x -= float(rad)
        if y < rad:
            y += float(rad)
        elif y > SIZE[1]-rad:
            y -= float(rad)
        return x, y

    def handle_collisions(self):

        def change_vel(b1:Bubble, b2:Bubble):

            m1, m2 = b1.radius**2, b2.radius**2
            M = m1 + m2
            p1, p2 = b1.pos, b2.pos
            d = np.linalg.norm(p1-p2)**2
            v1, v2 = b1.vel, b2.vel
            u1 = v1 - 2 * m2 / M * np.dot(v1 - v2, p1 - p2) / d * (p1 - p2)
            u2 = v2 - 2 * m1 / M * np.dot(v2 - v1, p2 - p1) / d * (p2 - p1)
            b1.vel = u1
            b2.vel = u2

            b1.move()
            b2.move()

        for i, j in combinations(range(self.n), 2):
            if self.bubbles[i].overlaps(self.bubbles[j]):
                change_vel(self.bubbles[i], self.bubbles[j])

    def logic(self):

        for bubble in self.bubbles:
            bubble.move()
        self.handle_collisions()

    def draw(self, DISPLAY):

        for bubble in self.bubbles:
            bubble.draw(DISPLAY)

def mainloop():
    pygame.init()

    world = Sim(NB_BUBBLES)

    mouse_position = pygame.Vector2()

    fps_counter = FpsCounter(60, Bubbles=world)
    while True:
        screen, events = yield
        for event in events:
            if event.type == pygame.QUIT:
                return
            # TODO : if possible add a function to add some bubbles
            debug.handle_event(event)
            fps_counter.handle_event(event)

        # Handle the collisions
        world.logic()
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
