"""
Typing part pg particle_system - required to run particle_system.py
"""
from __future__ import annotations
from typing import TypedDict, Tuple, Union


# Union[Tuple[float, float], Tuple[float, float, float], Tuple[float, float, float, float]]
# Union[float, Tuple[float, float]]
# Union[int, Tuple[int, int]]
# Tuple[float, float, float, float]
class _NeededParticleTemplate(TypedDict):
    size: Union[Tuple[float, float], Tuple[float, float, float], Tuple[float, float, float, float]]
    life_time: Union[int, Tuple[int, int]]


class _NotImportantParticleTemplate(TypedDict, total=False):
    size_change: Union[Tuple[float, float], Tuple[float, float, float], Tuple[float, float, float, float]]
    rotation: Union[float, Tuple[float, float]]
    rotation_speed: Union[float, Tuple[float, float]]
    bounding_box: Tuple[float, float, float, float]
    speed: Union[float, Tuple[float, float]]
    moving_angle: Union[float, Tuple[float, float]]


class ParticleTemplate(_NeededParticleTemplate, _NotImportantParticleTemplate):
    pass


particle_template_filler: _NotImportantParticleTemplate = _NotImportantParticleTemplate(
    size_change=(0, 0),
    rotation=0,
    rotation_speed=0,
    speed=0,
    moving_angle=0
)


class SpawnerTemplate(TypedDict):
    spawn_pos: Union[Tuple[float, float], Tuple[float, float, float], Tuple[float, float, float, float]]
    spawn_delay: Union[int, Tuple[int, int]]
    limit: Union[int, Tuple[int, int]]
