import json
import random
from typing import List, Tuple, Dict
from game.actor import Actor

def load_enemy_defs(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return {e["id"]: e for e in json.load(f)}

def spawn_enemies(grid, rooms, rng: random.Random, *, count: int, level: int = 1, defs_path: str = "data/enemies.json"):
    """Спавнимо ворогів за вагою залежно від рівня."""
    enemies: list[Actor] = []
    if len(rooms) <= 1:
        return enemies
    defs = load_enemy_defs(defs_path)

    # ваги типів (нарощуємо складність)
    w_runner = max(1, 3 + level)         # щури часто
    w_brute  = max(1, 1 + level // 2)    # танки з'являються поступово
    w_shoot  = max(1, 0 + level // 2)    # стрільці після 2-го

    bag = (["rat_runner"] * w_runner) + (["brute"] * w_brute) + (["shooter"] * w_shoot)

    usable_rooms = rooms[1:].copy()
    rng.shuffle(usable_rooms)

    for room in usable_rooms[:count]:
        x, y = int(room.centerx), int(room.centery)
        kind = rng.choice(bag)
        d = defs[kind]
        enemies.append(Actor(
            x, y,
            name=d["name"], hp=d["hp"], atk=d["atk"], df=d["df"],
            kind=kind,
            speed_steps=d.get("speed_steps", 1),
            move_cooldown=d.get("move_cooldown", 0),
            ranged=d.get("ranged", False),
            range=d.get("range", 0),
            shoot_cooldown=d.get("shoot_cooldown", 0),
        ))
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

def spawn_terminals(rooms, rng: random.Random, lore_path: str, count: int = 2) -> Dict[Tuple[int,int], str]:
    with open(lore_path, "r", encoding="utf-8") as f:
        lore = json.load(f)
    pool = [e["text"] for e in lore]
    rng.shuffle(pool)

    spots: Dict[Tuple[int,int], str] = {}
    use_rooms = rooms[1:].copy()
    rng.shuffle(use_rooms)
    for r in use_rooms[:count]:
        x, y = int(r.centerx), int(r.centery)
        if pool:
            spots[(x,y)] = pool.pop()
    return spots

def pick_stairs_room(rooms, rng: random.Random) -> Tuple[int,int]:
    if len(rooms) >= 2:
        r = rooms[-1]
        return int(r.centerx), int(r.centery)
    r = rooms[0]
    return int(r.centerx), int(r.centery)