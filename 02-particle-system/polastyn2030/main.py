import sys
from pathlib import Path

try:
    import wclib
except ImportError:
    # wclib may not be in the path because of the architecture
    # of all the challenges and the fact that there are many
    # way to run them (through the showcase, or on their own)

    ROOT_FOLDER = Path(__file__).parent.parent.parent
    sys.path.append(str(ROOT_FOLDER))
    import wclib

# This line tells python how to handle the relative imports
# when you run this file directly.
__package__ = "02-particle-system." + Path(__file__).parent.name

# ---- Recommended: don't modify anything above this line ---- #

# Metadata about your submission
__author__ = "polastyn#7640"  # Put yours!
__achievements__ = [  # Uncomment the ones you've done
    # "Casual",
    # "Ambitious",
    "Adventurous",
]

# To import the modules in yourname/, you need to use relative imports,
# otherwise your project will not be compatible with the showcase.
# noinspection PyPackages
from .objects import *
# noinspection PyPackages
from .particle_system import load_particle_spawner as load
# noinspection PyPackages
from .particle_system_template import ParticleTemplate, SpawnerTemplate
# noinspection PyPackages
from . import particle_system as par

BACKGROUND = 0x0F1012


def mainloop():
    pygame.init()

    player = Player((SIZE[0] / 2, SIZE[1] / 2), (0, 0))
    # The state is just a collection of all the objects in the game
    state = State(player, FpsCounter(60), *Asteroid.generate_many())
    image = pygame.Surface((10, 10))
    image.fill((255, 255, 255))
    spawner = load(
        ParticleTemplate(life_time=10, size=(5, 5), speed=(10, 20)),
        image, SpawnerTemplate(spawn_pos=(30, 30, 30), spawn_delay=0, limit=10)
    )
    spawner.info.spawn_pos = par.RemotePos(player, "center")
    spawner_angle = par.RandomFloat(-10, 10)
    spawner.info.object_info.angle = spawner_angle

    while True:
        screen, events = yield
        for event in events:
            if event.type == pygame.QUIT:
                return
            else:
                state.handle_event(event)

        # Note: the logic for collisions is in the Asteroids class.
        # This may seem arbitrary, but the only collisions that we consider
        # are with asteroids.
        state.logic()
        spawner_angle.move_center(-player.rotation+90)
        spawner.update()

        screen.fill(BACKGROUND)
        spawner.draw(screen)
        state.draw(screen)


if __name__ == "__main__":
    wclib.run(mainloop())
