import time
from collections import deque
from functools import lru_cache
from pathlib import Path
from typing import Tuple, Sized

import pygame

from wclib.constants import SIZE, ROOT_DIR

__all__ = [
    "SIZE",
    "SUBMISSION_DIR",
    "ASSETS",
    "SCREEN",
    "load_image",
    "text",
    "chrange",
    "FpsCounter",
    "debug",
]

SUBMISSION_DIR = Path(__file__).parent
ASSETS = SUBMISSION_DIR.parent / "assets"
SCREEN = pygame.Rect(0, 0, *SIZE)


@lru_cache()
def load_image(name: str, scale=1, alpha=True, base: Path = ASSETS):
    """Load an image from the global assets folder given its name.

    If [base] is given, load a n image from this folder instead.
    For instance you can pass SUBMISSION_DIR to load an image from your own directory.

    If [scale] is not one, scales the images in both directions by the given factor.

    The function automatically calls convert_alpha() but if transparency is not needed,
    one can set [alpha] to False to .convert() the image instead.

    The results are cached, so this function returns the same surface every time it
    is called with the same arguments. If you want to modify the returned surface,
    .copy() it first.
    """

    image = pygame.image.load(base / f"{name}.png")
    if scale != 1:
        new_size = int(image.get_width() * scale), int(image.get_height() * scale)
        image = pygame.transform.scale(image, new_size)

    if alpha:
        return image.convert_alpha()
    else:
        return image.convert()


@lru_cache()
def font(size=20, name=None):
    """
    Load a font from its name in the wclib/assets folder.

    If a Path object is given as the name, this path will be used instead.
    This way, you can use custom fonts that are inside your own folder.
    Results are cached.
    """

    name = name or "regular"
    if isinstance(name, Path):
        path = name
    else:
        path = ROOT_DIR / "wclib" / "assets" / (name + ".ttf")
    return pygame.font.Font(path, size)


@lru_cache(5000)
def text(txt, color, size=20, font_name=None):
    """Render a text on a surface. Results are cached."""
    return font(size, font_name).render(str(txt), True, color)


def chrange(
    x: float,
    initial_range: Tuple[float, float],
    target_range: Tuple[float, float],
    power=1,
    flipped=False,
):
    """Change the range of a number by mapping the initial_range to target_range using a linear transformation."""
    normalised = (x - initial_range[0]) / (initial_range[1] - initial_range[0])
    normalised **= power
    if flipped:
        normalised = 1 - normalised
    return normalised * (target_range[1] - target_range[0]) + target_range[0]


class FpsCounter:
    """
    A wrapper around pygame.time.Clock that shows the FPS on screen.

    It can also show the lengths of different collections (nb of objects/particles...).

    Controls:
     - [F] Toggles the display of FPS
     - [U] Toggles the capping of FPS
    """

    Z = 1000
    REMEMBER = 30

    def __init__(self, fps, **counters: Sized):
        """
        Show and manage the FPS of the game.

        Args:
            fps: the desired number of frames per second.
            **counters: pairs of labels and collections
                whose size will be displayed.
        """

        self.hidden = False
        self.cap_fps = True
        self.target_fps = fps
        self.clock = pygame.time.Clock()
        self.frame_starts = deque([time.time()], maxlen=self.REMEMBER)
        self.counters = counters

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_f:
                self.hidden = not self.hidden
            elif event.key == pygame.K_u:
                self.cap_fps = not self.cap_fps

    def logic(self, **kwargs):
        # Passing 0 to tick() removes the cap on FPS.
        self.clock.tick(self.target_fps * self.cap_fps)

        self.frame_starts.append(time.time())

    @property
    def current_fps(self):
        if len(self.frame_starts) <= 1:
            return 0
        seconds = self.frame_starts[-1] - self.frame_starts[0]
        return (len(self.frame_starts) - 1) / seconds

    def draw(self, screen):
        if self.hidden:
            return

        color = "#89C4F4"
        t = text(f"FPS: {int(self.current_fps)}", color)
        r = screen.blit(t, t.get_rect(topleft=(15, 15)))

        """for label, collection in self.counters.items():
            t = text(f"{label}: {len(collection)}", color)
            r = screen.blit(t, r.bottomleft)"""


class Debug:
    """
    This class helps with graphical debuging.
    It allows to draw points, vectors, rectangles and text
    on top of the window at any moment of the execution.

    You can use this from any function to visualise vectors,
    intermediates computations and anything that you would like to know
    the value without printing it.
    It is

    All debug drawing disapear after one frame, except the texts
    for which the last [texts_to_keep] stay on the screen so that there
    is sufficient time to read them.

    All debug methods return their arguments so that can be chained.
    For instance, you can write:

    >>> debug = Debug()
    >>> pos += debug.vector(velocity, pos)

    Which is equivalent to:

    >>> pos += velocity
    But also draws the [velocity] vector centered at [pos] so that you see it.
    """

    def __init__(self, texts_to_keep=20):
        self.texts_to_keep = texts_to_keep

        self.points = []
        self.vectors = []
        self.rects = []
        self.texts = []
        self.nb_txt_this_frame = 0

        # Backup to restore if the game is paused,
        # this way, anotations are not lost when objects
        # are not updated anymore.
        self.lasts = [[], [], [], []]

        self.enabled = False
        self.paused = False

    def point(self, x, y, color="red"):
        """Draw a point on the screen."""
        if self.enabled:
            self.points.append((x, y, color))
        return x, y

    def vector(self, vec, anchor, color="red", scale=1):
        """Draw a vector centered at [anchor] on the next frame.
        It can be useful to [scale] if the expected length is too small or too large."""
        if self.enabled:
            self.vectors.append((pygame.Vector2(anchor), pygame.Vector2(vec) * scale, color))
        return vec

    def rectangle(self, rect, color="red"):
        """Draw a rectangle on the next frame."""
        if self.enabled:
            self.rects.append((rect, color))
        return rect

    def text(self, *obj):
        """Draw a text on the screen until there too many texts."""
        if self.enabled:
            self.texts.append(obj)
            self.nb_txt_this_frame += 1

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_d:
            self.enabled = not self.enabled

    def draw(self, screen: pygame.Surface):
        if not self.enabled:
            return

        if self.paused:
            self.points, self.vectors, self.rects, self.texts = self.lasts

        for (x, y, color) in self.points:
            pygame.draw.circle(screen, color, (x, y), 1)

        for (anchor, vec, color) in self.vectors:
            pygame.draw.line(screen, color, anchor, anchor + vec)

        for rect, color in self.rects:
            pygame.draw.rect(screen, color, rect, 1)

        y = SIZE[1] - 15
        for i, obj in enumerate(self.texts):
            color = "white" if len(self.texts) - i - 1 >= self.nb_txt_this_frame else "yellow"
            s = text(" ".join(map(str, obj)), color)
            r = screen.blit(s, s.get_rect(bottomleft=(15, y)))
            y = r.top

        # Clear everything for the next frame.
        self.lasts = [self.points, self.vectors, self.rects, self.texts]
        self.points = []
        self.vectors = []
        self.rects = []
        self.texts = self.texts[-self.texts_to_keep :]
        if not self.paused:
            self.nb_txt_this_frame = 0


# Global debug instance, accessible from everywhere.
debug = Debug()
