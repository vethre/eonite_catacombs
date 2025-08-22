from __future__ import annotations

from game.inventory import Inventory

class Actor:
    # XY | Name | HP | ATK | DF
    def __init__(self, x: int, y: int, *, name: str, hp: int, atk: int, df: int):
        self.x, self.y = x, y
        self.name = name
        self.max_hp = hp
        self.hp = hp
        self.atk = atk
        self.df = df
        self.inv = Inventory()
        # AI:
        self.aggro = False
        self.last_known_player: tuple[int, int] | None = None

    @property
    def pos(self) -> tuple[int, int]:
        return self.x, self.y
    
    @property
    def alive(self) -> bool:
        return self.hp > 0
    
    def move_by(self, dx: int, dy: int):
        self.x += dx
        self.y += dy

    def distance2(self, other: "Actor") -> int:
        return abs(self.x - other.x) + abs(self.y - other.y)
    
    def take_damage(self, dmg: int) -> bool:
        # If dead returns TRUE
        self.hp = max(0, self.hp - dmg)
        return self.hp == 0