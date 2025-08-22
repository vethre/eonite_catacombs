from __future__ import annotations
import json, os
from dataclasses import dataclass
from typing import Dict, List, Any, Tuple
from core.events import LOG

@dataclass(frozen=True)
class ItemDef:
    id: str
    name: str
    kind: str
    effect: str
    value: int | None = None
    radius: int | None = None
    damage: int | None = None

class ItemDB:
    def __init__(self):
        self._defs: Dict[str, ItemDef] = {}

    def load_from(self, path: str):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for it in data:
            d = ItemDef(**it)
            self._defs[d.id] = d

    def get(self, item_id: str) -> ItemDef:
        return self._defs[item_id]
    
# ------------- use-effects --------------

def use_item(item: ItemDef, ctx: "GameCtx") -> bool:
    # return True if the item was used successfully
    if item.effect == "heal":
        val = item.value or 0
        before = ctx.player.hp
        ctx.player.hp = min(ctx.player.max_hp, ctx.player.hp + val)
        healed = ctx.player.hp - before
        if healed > 0:
            LOG.add(f"Ти відновив {healed} HP. Used: {item.name}")
            return True
        else:
            LOG.add(f"Не вдалося відновити HP. Used: {item.name}")
            return False
        
    if item.effect == "bomb":
        dmg = item.damage or 0
        r = item.radius or 1
        px, py = ctx.player.x, ctx.player.y
        hits = 0
        for en in list(ctx.enemies):
            if abs(en.x - px) + abs(en.y - py) <= r:
                en.take_damage(dmg)
                hits += 1
                if en.hp <= 0:
                    LOG.add(f"Ворог знищений! Used: {item.name}")
                    ctx.enemies.remove(en)
        LOG.add(f"Вибух завдав {hits} вражим шкоди. Radius: {r}")
        # little shine: seen+
        reveal_circle(ctx.seen, px, py, r+1)
        return True
    
    if item.effect == "flare":
        r = item.radius or 6
        px, py = ctx.player.x, ctx.player.y
        reveal_circle(ctx.seen, px, py, r)
        LOG.add(f"Світляк освітлює все у радіусі {r}.")
        return True

    LOG.add("Цей предмет поки нічого не робить…")
    return False

def reveal_circle(seen: List[List[bool]], cx: int, cy: int, r: int):
    h = len(seen)
    w = len(seen[0])
    r2 = r * r
    for y in range(max(0, cy-r), min(h, cy+r+1)):
        for x in range(max(0, cx-r), min(w, cx+r+1)):
            if (x-cx)*(x-cx) + (y-cy)*(y-cy) <= r2:
                seen[y][x] = True

# game context (min interface)
class GameCtx:
    def __init__(self, player, enemies, seen):
        self.player = player
        self.enemies = enemies
        self.seen = seen