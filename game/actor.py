from __future__ import annotations
from .inventory import Inventory

class Actor:
    def __init__(self, x: int, y: int, *, name: str, hp: int, atk: int, df: int,
                 kind: str | None = None,
                 speed_steps: int = 1,      # скільки клітин за хід (для runner)
                 move_cooldown: int = 0,    # ходить раз на N ходів (для brute)
                 ranged: bool = False,
                 range: int = 0,
                 shoot_cooldown: int = 0):
        self.x, self.y = x, y
        self.name = name
        self.max_hp = hp
        self.hp = hp
        self.atk = atk
        self.df = df
        self.inv = Inventory()
        # AI
        self.kind = kind or name
        self.aggro = False
        self.last_known_player: tuple[int,int] | None = None
        # рух/темп
        self.speed_steps = max(1, int(speed_steps))
        self.move_cooldown = int(move_cooldown)
        self._move_cd_timer = 0
        # дальній бій
        self.ranged = ranged
        self.range = int(range)
        self.shoot_cooldown = int(shoot_cooldown)
        self._shoot_cd_timer = 0
        # статуси
        self.status: list[dict] = []   # напр: {"id":"poison","ticks":3,"dmg":1}

    @property
    def pos(self): return self.x, self.y
    @property
    def alive(self): return self.hp > 0

    def move_by(self, dx: int, dy: int):
        self.x += dx; self.y += dy

    def distance2(self, other: "Actor") -> int:
        return abs(self.x - other.x) + abs(self.y - other.y)

    def take_damage(self, dmg: int) -> bool:
        self.hp = max(0, self.hp - dmg)
        return self.hp == 0

    # ---- статуси ----
    def add_status(self, sid: str, ticks: int, **kwargs):
        self.status.append({"id": sid, "ticks": int(ticks), **kwargs})

    def tick_statuses(self, log_prefix: str = ""):
        """Повертає True, якщо юніт помер від статусів."""
        alive = True
        new_list = []
        for st in self.status:
            st["ticks"] -= 1
            if st["id"] == "poison":
                dmg = int(st.get("dmg", 1))
                died = self.take_damage(dmg)
                from core.events import LOG
                LOG.add(f"{log_prefix}{self.name} страждає від отрути ({dmg}). [{self.hp}/{self.max_hp}]")
                if died:
                    alive = False
            if st["ticks"] > 0:
                new_list.append(st)
        self.status = new_list
        return not alive

    # ---- таймери ----
    def ready_to_move(self) -> bool:
        if self._move_cd_timer <= 0:
            self._move_cd_timer = self.move_cooldown
            return True
        self._move_cd_timer -= 1
        return False

    def ready_to_shoot(self) -> bool:
        if self._shoot_cd_timer <= 0:
            self._shoot_cd_timer = self.shoot_cooldown
            return True
        return False

    def cool_shoot(self):
        if self._shoot_cd_timer > 0:
            self._shoot_cd_timer -= 1
