from game.inventory import Inventory

class GameState:
    def __init__(self):
        self.player_x = 10
        self.player_y = 10
        self.inventory = Inventory()
        self.messages = []
        self.hp = 10