"""
File for particle system
"""
from __future__ import annotations

from builtins import super
from typing import Callable, TypeVar as _TypeVar, Type, cast, overload, Union, Tuple, Literal
import random as rd

import pygame as pg

try:
    # noinspection PyPackages
    from . import particle_system_template as pst
except ImportError:
    import particle_system_template as pst


class _FixedGetAttr:
    def __getattribute__(self, item: str):
        data = super().__getattribute__(item)

        if item.startswith("__") and item.endswith("__"):
            return data

        try:
            data = data.__get__(self, self.__class__)
        except AttributeError:
            pass
        return data


class BaseDynamicSurface(pg.Surface):
    # noinspection PyMissingConstructor
    def __init__(self, source_surface: pg.Surface, *arg_configs, **kwarg_configs):
        self.source_surface = source_surface
        self.arg_configs = arg_configs
        self.kwarg_configs = kwarg_configs
        self.__names__ = {"source_surface", "arg_configs", "kwarg_configs", "tick", "map_self_to_new"}

    def __getattribute__(self, item: str):
        if item.startswith("__") and item.endswith("__"):
            return object.__getattribute__(self, item)
        elif item in self.__names__:
            return object.__getattribute__(self, item)
        else:
            return getattr(self.source_surface, item)

    def tick(self):
        pass

    def map_self_to_new(self, surface: pg.Surface | None = None):
        return self.__cls__(
            surface if surface else self.source_surface, *self.arg_configs, **self.kwarg_configs
        )


class BaseParticleObject(_FixedGetAttr, pg.sprite.Sprite):
    def __init__(self, surface: pg.Surface | BaseDynamicSurface, size: pg.Vector2, position: pg.Vector2,
                 rotation: float, bounding_box: pg.Rect, life_time: int):
        super().__init__()
        self.source_surface = surface
        self.size = size
        self.position = position
        self.rotation = rotation
        self.source_rect = bounding_box
        self.life_time = life_time

        self._smooth_scale = True

    @property
    def alive(self):
        return self.life_time > 0

    @property
    def surface(self):
        copy = self.source_surface.copy()

        if self._smooth_scale:
            copy = pg.transform.smoothscale(copy, self.tuple_size)
        else:
            copy = pg.transform.scale(copy, self.tuple_size)

        copy = pg.transform.rotate(copy, self.rotation)

        if isinstance(self.source_surface, BaseDynamicSurface):
            copy = self.source_surface.map_self_to_new(copy)

        return copy

    @property
    def image(self):
        return self.surface

    @property
    def rect(self):
        copy = self.source_rect.copy()
        copy.topleft = pg.Vector2(copy.topleft) + self.position
        return copy

    @property
    def tuple_size(self):
        return int(self.size.x), int(self.size.y)

    def update(self, *args, **kwargs) -> None:
        if not self.alive:
            self.kill()

        self.tick()

    def tick(self):
        pass


class DynamicParticle(BaseParticleObject):
    def __init__(
            self,
            surface: pg.Surface | BaseDynamicSurface, size: pg.Vector2,
            position: pg.Vector2, rotation: float,
            bounding_box: pg.Rect, life_time: int,
            speed: pg.Vector2,
            rotation_speed: float,
            scale_change: pg.Vector2
    ):

        super().__init__(surface, size, position, rotation, bounding_box, life_time)

        self.speed = speed
        self.rotation_speed = rotation_speed
        self.scale_change = scale_change

    def tick(self):
        if not self.alive:
            return

        self.life_time -= 1

        self.__change("position", self.speed)
        self.__change("rotation", self.rotation_speed)
        self.__change("size", self.scale_change)

        if isinstance(self.surface, BaseDynamicSurface):
            self.surface.tick()

    _T = _TypeVar("_T", bound=object)

    def __change(self, name: str, by: Callable[[_T], _T] | _T):
        self.__change_value(name, getattr(self, name, None), by)

    def __change_value(self, name: str, data: _T, by: Callable[[_T], _T] | _T):
        if getattr(by, "__call__", False):
            setattr(self, name, by(data))
        else:
            try:
                setattr(self, name, data + by)
            except TypeError:
                pass


class RandomPos:
    def __init__(self, center: pg.Vector2, pos_range: float | pg.Rect):
        self.center = center
        self.pos_range = pos_range
        self.__names__ = {"center", "pos_range", "get"}

    def __get__(self, instance, owner):
        return self.get()

    def __getattribute__(self, item: str):
        if item.startswith("__") and item.endswith("__"):
            try:
                return super().__getattribute__(item)
            except ValueError:
                val = self.get()
                return getattr(val, item)
        elif item in self.__names__:
            return super().__getattribute__(item)
        else:
            val = self.get()
            return getattr(val, item)

    def get(self):
        if isinstance(self.pos_range, (float, int)):
            offset = pg.Vector2(1, 0)
            offset.rotate(rd.randint(0, 360))
            offset *= rd.randint(0, int(self.pos_range))
            return self.center + offset

        x = rd.randint(0, self.pos_range.w)
        y = rd.randint(0, self.pos_range.h)

        pos = pg.Vector2(x, y)
        pos += pg.Vector2(self.pos_range.topleft)

        return pos


class RandomFloat:
    # noinspection PyInitNewSignature
    def __init__(self, smallest: float, biggest: float):
        self.smallest = smallest
        self.biggest = biggest
        self.__names__ = {"smallest", "biggest", "get", "move_left", "move_right", "move_center"}

    def __get__(self, instance, owner):
        return self.get()

    def __getattribute__(self, item: str):
        if item.startswith("__") and item.endswith("__"):
            try:
                return super().__getattribute__(item)
            except ValueError:
                val = self.get()
                return getattr(val, item)
        elif item in self.__names__:
            return super().__getattribute__(item)
        else:
            val = self.get()
            return getattr(val, item)

    def get(self):
        random = rd.random()
        diff = self.biggest - self.smallest
        random *= diff
        random += self.smallest
        return random

    def move_left(self, to: float):
        diff = self.biggest - self.smallest
        self.smallest = to
        self.biggest = to + diff

    def move_right(self, to: float):
        diff = self.biggest - self.smallest
        self.biggest = to
        self.smallest = to - diff

    def move_center(self, to: float):
        diff = self.biggest - self.smallest
        half = diff / 2
        self.smallest = to - half
        self.biggest = to + half


class RandomInt(RandomFloat):
    def get(self):
        ret = super(RandomInt, self).get()
        return int(ret)


class RemotePos(RandomPos):
    # noinspection PyMissingConstructor
    def __init__(self, obj: object, attr: str, op: str = "x"):
        self.obj = obj
        self.attr = attr
        self.op = op
        self.__names__ = {"obj", "attr", "op", "get"}

    def get(self):
        return eval(self.op, {}, {"x": pg.Vector2(getattr(self.obj, self.attr))})


class RemoteFloat(RandomFloat):
    # noinspection PyMissingConstructor
    def __init__(self, obj: object, attr: str, op: str = "x"):
        self.obj = obj
        self.attr = attr
        self.op = op
        self.__names__ = {"obj", "attr", "op", "get"}

    def get(self):
        return eval(self.op, {}, {"x": float(getattr(self.obj, self.attr))})


class RemoteInt(RemoteFloat):
    def get(self):
        return int(super(RemoteInt, self).get())


class ParticleObjectInfo(_FixedGetAttr):
    def __init__(self,
                 surface: pg.Surface | BaseDynamicSurface,
                 size: pg.Vector2 | RandomPos,
                 size_change: pg.Vector2 | RandomPos,
                 rotation: float | RandomFloat,
                 rotation_speed: float | RandomFloat,
                 life_time: int | RandomInt,
                 bounding_box: pg.Rect,
                 speed: float | RandomFloat,
                 moving_angle: float | RandomFloat,
                 particle_class: Type[DynamicParticle] | None = None
                 ):
        self.surface = surface
        self.size = size
        self.size_change = size_change
        self.rotation = rotation
        self.rotation_speed = rotation_speed
        self.life_time = life_time
        self.bounding_box = bounding_box
        self.speed = speed
        self.angle = moving_angle
        self.particle_class = particle_class if particle_class is not None else DynamicParticle


class ParticleSpawnerInfo(_FixedGetAttr):
    def __init__(
            self,
            spawn_pos: pg.Vector2 | RandomPos,
            spawn_delay: int | RandomInt,
            object_info: ParticleObjectInfo,
            limit: int = -1,
            burst_function: Callable[[int], int] | None = None
    ):
        self.spawn_pos = spawn_pos
        self.spawn_delay = spawn_delay
        self.object_info = object_info
        self.limit = limit
        self.burst_function = burst_function

    def generate(self):
        info = self.object_info
        speed = pg.Vector2(1, 0).rotate(info.angle) * info.speed
        obj = self.object_info.particle_class(
            info.surface, info.size, self.spawn_pos, info.rotation, info.bounding_box,
            info.life_time, speed, info.rotation_speed, info.size_change
        )
        return obj


class BaseParticleSpawner(pg.sprite.Group):
    def __init__(self, info: ParticleSpawnerInfo):
        self.info = info
        self.active = True
        self.next_spawn = 0
        self.spawn_count = 0
        super().__init__()

    def add(self, *sprites: pg.Sprite) -> None:
        if len(self) < self.info.limit:
            super(BaseParticleSpawner, self).add(*sprites)

    def spawn(self):
        if self.info.burst_function:
            # noinspection PyBroadException
            try:
                value = self.info.burst_function(self.spawn_count)

                for _ in range(value):
                    self.add(self.info.generate())
            except Exception:
                self.info.burst_function = None
                self.spawn()
        else:
            self.add(self.info.generate())
        self.spawn_count += 1

    def update(self, *args, **kwargs) -> None:
        if self.active:
            if self.next_spawn <= 0:
                self.spawn()
                self.next_spawn += self.info.spawn_delay
            self.next_spawn -= 1
        super(BaseParticleSpawner, self).update(*args, **kwargs)


@overload
def _convert_to_valid(
        data: Union[Tuple[float, float], Tuple[float, float, float], Tuple[float, float, float, float]],
        mode: Literal["p", "pos", "v", "vector2", "Vector2"]
) -> pg.Vector2 | RandomPos: ...


@overload
def _convert_to_valid(data: Union[float, Tuple[float, float]], mode: Literal["f", "float"]) -> float | RandomFloat: ...


@overload
def _convert_to_valid(data: Union[int, Tuple[int, int]], mode: Literal["i", "int"]) -> int | RandomInt: ...


@overload
def _convert_to_valid(data: Tuple[float, float, float, float], mode: Literal["r", "rect", "Rect"]) -> pg.Rect: ...


def _convert_to_valid(data, mode):
    if mode in {"p", "pos", "v", "vector2", "Vector2"}:
        data = cast(Union[Tuple[float, float], Tuple[float, float, float], Tuple[float, float, float, float]], data)
        if len(data) == 2:
            return pg.Vector2(data)
        elif len(data) == 3:
            return RandomPos(pg.Vector2(data[:2]), data[2])
        else:
            return RandomPos(pg.Vector2(data[:2]), pg.Rect(data))
    elif mode in {"f", "float"}:
        data = cast(Union[float, Tuple[float, float]], data)
        if isinstance(data, float):
            return data
        elif isinstance(data, int):
            return float(data)
        return RandomFloat(*data)
    elif mode in {"i", "int"}:
        data = cast(Union[int, Tuple[int, int]], data)
        if isinstance(data, int):
            return data
        return RandomInt(*data)
    elif mode in {"r", "rect", "Rect"}:
        data = cast(Tuple[float, float, float, float], data)
        return pg.Rect(data)
    else:
        raise TypeError("mode argument not in valid options")


def _fix_particle_template(template: pst.ParticleTemplate):
    translating = {
        "size": "v", "life_time": "i", "size_change": "p", "rotation": "f", "rotation_speed": "f",
        "bounding_box": "r", "speed": "f", "moving_angle": "f"
    }
    new = {}
    for el in template:
        # noinspection PyTypeChecker,PyTypedDict
        new[el] = _convert_to_valid(template[el], translating[el])
    return new


def load_particle_info(
        surface: pg.Surface, template: pst.ParticleTemplate,
        particle_class: Type[DynamicParticle] | None = None
):
    particle_class = particle_class if particle_class is not None else DynamicParticle
    full_template = pst.particle_template_filler.copy()
    full_template.update(dict(template))
    full_template = cast(pst.ParticleTemplate, full_template)
    fixed = _fix_particle_template(full_template)

    if "bounding_box" not in fixed:
        fixed["bounding_box"] = surface.get_rect()

    return ParticleObjectInfo(surface=surface, particle_class=particle_class, **fixed)


def load_spawner_info(
        template: pst.SpawnerTemplate,
        object_info: ParticleObjectInfo,
        burst_function: Callable[[int], int] | None = None
):
    spawn_pos = _convert_to_valid(template['spawn_pos'], "p")
    spawn_delay = _convert_to_valid(template['spawn_delay'], "i")
    limit = _convert_to_valid(template['limit'], "i")
    return ParticleSpawnerInfo(spawn_pos, spawn_delay, object_info, limit, burst_function)


def load_particle_spawner(
        particle_template: pst.ParticleTemplate,
        surface: pg.Surface,
        spawner_template: pst.SpawnerTemplate,
        particle_class: Type[DynamicParticle] | None = None,
        burst_function: Callable[[int], int] | None = None,
        spawner_class: Type[BaseParticleSpawner] | None = None
):
    spawner_class = spawner_class if spawner_class is not None else BaseParticleSpawner
    particle_info = load_particle_info(surface, particle_template, particle_class)
    return spawner_class(load_spawner_info(spawner_template, particle_info, burst_function))
