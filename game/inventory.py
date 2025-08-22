class Inventory:
    def __init__(self):
        self.items = {} # {"heal": 2, ...}

    def add(self, item_id: str, amount: int = 1):
        self.items[item_id] = self.items.get(item_id, 0) + amount

    def remove(self, item_id: str, amount: int = 1):
        if item_id in self.items:
            self.items[item_id] -= amount
            if self.items[item_id] <= 0:
                del self.items[item_id]

    def has(self, item_id: str) -> bool:
        return item_id in self.items
    
    def list_items(self):
        return [(item_id, count) for item_id, count in self.items.items()]