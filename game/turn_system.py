from enum import Enum

class Turn(Enum):
    PLAYER = 0
    ENEMIES = 1

class TurnSystem:
    def __init__(self):
        self.turn = Turn.PLAYER

    def end_player(self):
        self.turn = Turn.ENEMIES

    def end_enemies(self):
        self.turn = Turn.PLAYER

    @property
    def player_turn(self) -> bool:
        return self.turn is Turn.PLAYER