import pygame as pg
from core.events import LOG
from core.settings import UI_FONT

def draw_hud(screen: pg.Surface, text: str, inv_slots: list[str] = None, y: int = 8):
    font = pg.font.SysFont(UI_FONT, 18)
    screen.blit(font.render(text, True, (220,220,220)), (8, y))
    oy = y + 26
    for line in LOG.lines[-6:]:
        screen.blit(font.render(line, True, (180, 190, 200)), (8, oy))
        oy += 20
    if inv_slots is not None:
        inv_text = " | ".join(f"{i+1}:{sid}" for i, sid in enumerate(inv_slots))
        if not inv_text: inv_text = "(інвентар порожній)"
        screen.blit(font.render(f"[Інвентар] {inv_text}", True, (210,210,210)), (8, oy+8))
