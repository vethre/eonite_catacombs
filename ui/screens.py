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