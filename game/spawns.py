import random
from typing import List, Tuple
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

def spawn_items(rooms, rng: random.Random, pool: list[str], *, per_room_chance: float = 0.5):
    # return NEW[dict]{(x,y): item_id} on the floor
    drops = {}
    for i, room in enumerate(rooms):
        if i == 0:
            continue
        if rng.random() < per_room_chance:
            x, y = int(room.centerx), int(room.centery)
            if (x,y) not in drops:
                drops[(x,y)] = rng.choice(pool)
    return drops