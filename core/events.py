# Logging method of events (for HUD | debug)
class MessageLog:
    def __init__(self, cap: int = 6):
        self.cap = cap
        self.lines: list[str] = []

    def add(self, text: str):
        self.lines.append(text)
        if len(self.lines) > self.cap:
            self.lines = self.lines[-self.cap:]

LOG = MessageLog()
        