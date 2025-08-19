import pygame as pg
from core.events import LOG
from core.settings import UI_FONT

def draw_hud(screen: pg.Surface, text: str, y: int = 8):
    font = pg.font.SysFont(UI_FONT, 18)
    screen.blit(font.render(text, True, (220, 220, 220)), (8, y))
    # Log under text
    oy = y + 26
    for line in LOG.lines[-6:]:
        screen.blit(font.render(line, True, (180, 190, 200)), (8, oy))
        oy += 20