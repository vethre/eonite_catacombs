import pygame

def draw_inventory(screen, inventory, font, selected_index=0):
    screen.fill((20, 20, 20))
    y = 40
    items = inventory.list_items()

    if not items:
        text = font.render("Inventory is empty", True, (200, 200, 200))
        screen.blit(text, (40, y))
    else:
        for i, (item_id, count) in enumerate(items):
            color = (255, 255, 0) if i == selected_index else (200, 200, 200)
            text = font.render(f"{item_id}: x{count}", True, color)
            screen.blit(text, (40, y))
            y += 30

def draw_center_text(screen: pygame.Surface, lines, color=(230, 230, 230)):
    W, H = screen.get_size()
    font_big = pygame.font.SysFont("Consolas", 42)
    font = pygame.font.SysFont("Consolas", 22)
    y = H//2 - (len(lines)*28)//2
    for i, (text, big) in enumerate(lines):
        f = font_big if big else font
        img = f.render(text, True, color)
        x = (W - img.get_width()) // 2
        screen.blit(img, (x, y))
        y += 36 if big else 28

def draw_dead(screen: pygame.Surface):
    draw_center_text(screen, [
        ("Ти загинув", True),
        ("R — перезапустити забіг", False),
        ("ESC — вийти", False),
    ], (230,120,120))

def draw_win(screen: pygame.Surface):
    draw_center_text(screen, [
        ("Перемога!", True),
        ("R — новий забіг", False),
        ("ESC — вийти", False),
    ], (140,220,180))