from functools import lru_cache
from pathlib import Path
from random import uniform

import pygame

from wclib.constants import SIZE, ROOT_DIR

__all__ = [
    "SIZE",
    "SUBMISSION_DIR",
    "ASSETS",
    "SCREEN",
    "load_image",
    "rotate_image",
    "clamp",
    "random_in_rect",
    "from_polar",
    "clamp_vector",
    "text",
]

SUBMISSION_DIR = Path(__file__).parent
ASSETS = SUBMISSION_DIR.parent / "assets"
SCREEN = pygame.Rect(0, 0, *SIZE)


@lru_cache()
def load_image(name: str, scale=1, alpha=True):
    """Load a image from the disk and caches the results."""
    image = pygame.image.load(ASSETS / f"{name}.png")
    if scale != 1:
        new_size = image.get_width() * scale, image.get_height() * scale
        image = pygame.transform.scale(image, new_size)
    if alpha:
        return image.convert_alpha()
    else:
        return image.convert()


@lru_cache()
def rotate_image(surf, angle: int):
    """Rotate function that caches its results for performance."""
    return pygame.transform.rotate(surf, angle)


def clamp(value, mini, maxi):
    """Clamp value between mini and maxi"""
    if value < mini:
        return mini
    elif maxi < value:
        return maxi
    else:
        return value


def random_in_rect(rect):
    """Return a random point uniformly in a rectangle."""
    rect = pygame.Rect(rect)
    return pygame.Vector2(uniform(rect.left, rect.right), uniform(rect.top, rect.bottom))


def from_polar(rho, theta):
    """Create a Vector2 from its polar representation."""
    v = pygame.Vector2()
    v.from_polar((rho, theta))
    return v


def clamp_vector(v: pygame.Vector2, max_length):
    """Ensure that a vector has a magnitude less than max_length."""
    if v.length() > max_length:
        return v.normalize() * max_length
    return v


@lru_cache()
def font(size=20, name=None):
    """
    Load a font from its name in the wclib/assets folder.

    If a Path object is given as the name, this path will be used instead.
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
