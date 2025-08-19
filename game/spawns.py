import random
from game.actor import Actor

def spawn_enemies(grid, rooms, rng: random.Random, *, count: int = 4):
    enemies: list[Actor] = []
    if len(rooms) <= 1:
        return enemies
    
    usable_rooms = rooms[1:] # don't spawn at the beggining room
    rng.shuffle(usable_rooms)

    for room in usable_rooms[:count]:
        x, y = int(room.centerx), int(room.centery)
        enemies.append(Actor(x, y, name="Bat", hp=6, atk=3, df=0))
    return enemies