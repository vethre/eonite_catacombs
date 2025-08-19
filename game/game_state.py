from enum import Enum

class GameState(Enum):
    MENU    = 0
    RUN     = 1
    DEAD    = 2
    WIN     = 3