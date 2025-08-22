# main.py — Eonite Catacombs M2.1
import sys
import pygame as pg

# Core
from core.settings import *
from core.rng import rng_from_seed
from core.events import LOG

# World
from world.dungeon import make_map
from world.fov import compute_fov
from world.tileset import WALL, FLOOR

# UI
from ui.hud import draw_hud

# Game
from game.actor import Actor
from game.turn_system import TurnSystem
from game.spawns import spawn_enemies, spawn_items
from game.combat import attack
from game.items import ItemDB, use_item, GameCtx
from game.game_state import GameState


def draw_cell(screen, x, y, color):
    pg.draw.rect(screen, color, pg.Rect(x*TILE, y*TILE, TILE, TILE))


def draw_map(screen, grid, seen, fov):
    for y in range(ROWS):
        for x in range(COLS):
            cell = grid[y][x]
            if fov[y][x]:
                color = COLOR_WALL if cell == WALL else COLOR_FLOOR
            elif seen[y][x]:
                color = COLOR_MEMO if cell == WALL else (20,22,28)
            else:
                color = (0,0,0)
            draw_cell(screen, x, y, color)


def blocked_by_enemy(enemies, x, y):
    for e in enemies:
        if e.alive and e.x == x and e.y == y:
            return e
    return None


def passable(grid, x, y):
    return 0 <= x < COLS and 0 <= y < ROWS and grid[y][x] == FLOOR


def try_player_move(player: Actor, dx: int, dy: int, grid, enemies, ts: TurnSystem) -> bool:
    nx, ny = player.x + dx, player.y + dy
    if not passable(grid, nx, ny):
        return False
    enemy = blocked_by_enemy(enemies, nx, ny)
    if enemy:
        killed = attack(player, enemy)
        if killed:
            enemies.remove(enemy)
        ts.end_player()
        return True
    player.move_by(dx, dy)
    ts.end_player()
    return True


def enemies_turn(player: Actor, enemies, grid, ts: TurnSystem):
    for e in list(enemies):
        if not e.alive:
            enemies.remove(e)
            continue
        if e.distance2(player) == 1:
            killed = attack(e, player)
            if killed:
                LOG.add("Ти загинув. Натисни Esc, щоб вийти.")
            continue
        dx = 1 if player.x > e.x else -1 if player.x < e.x else 0
        dy = 1 if player.y > e.y else -1 if player.y < e.y else 0
        opts = []
        if dx: opts.append((e.x + dx, e.y))
        if dy: opts.append((e.x, e.y + dy))
        for nx, ny in opts:
            if passable(grid, nx, ny) and not blocked_by_enemy(enemies, nx, ny) and (nx, ny) != (player.x, player.y):
                e.x, e.y = nx, ny
                break
    ts.end_enemies()


def main(seed: str | None = DEFAULT_SEED):
    pg.init()
    screen = pg.display.set_mode((W, H))
    pg.display.set_caption("Eonite Catacombs — M2.1")
    clock = pg.time.Clock()

    state = GameState()
    mode = "game"  # або "inventory"
    selected_index = 0

    rng = rng_from_seed(seed)
    item_db = ItemDB()
    item_db.load_from("data/items.json")

    grid, (sx, sy), _, rooms = make_map(COLS, ROWS, rng)
    ground_items = spawn_items(rooms, rng, pool=["medkit","bomb","flare"], per_room_chance=0.7)

    player = Actor(sx, sy, name="Ти", hp=12, atk=4, df=1)
    enemies = spawn_enemies(grid, rooms, rng, count=4)

    ts = TurnSystem()
    seen = [[False for _ in range(COLS)] for _ in range(ROWS)]
    LOG.add("Welcome to the Catacombs. Arrows - movement, ESC - exit, I - inventory")

    running = True
    while running:
        clock.tick(FPS)

        for e in pg.event.get():
            if e.type == pg.QUIT:
                running = False

            elif e.type == pg.KEYDOWN:
                # ---------- GAME MODE ----------
                if mode == "game" and ts.player_turn:
                    dx = dy = 0
                    if e.key in (pg.K_ESCAPE,):
                        running = False
                    elif e.key in (pg.K_LEFT, pg.K_a):   dx = -1
                    elif e.key in (pg.K_RIGHT, pg.K_d):  dx =  1
                    elif e.key in (pg.K_UP, pg.K_w):     dy = -1
                    elif e.key in (pg.K_DOWN, pg.K_s):   dy =  1
                    elif e.key in (pg.K_PERIOD, pg.K_COMMA):
                        ts.end_player()
                    elif e.key in (pg.K_g,):
                        key = (player.x, player.y)
                        iid = ground_items.pop(key, None)  # <— або віддає item_id, або None
                        if iid is None:
                            LOG.add("Тут нічого підбирати.")
                        else:
                            if hasattr(player, "inv"):
                                player.inv.add(iid, 1)
                            LOG.add(f"Ти підібрав {item_db.get(iid).name}.")
                            ts.end_player()
                    elif pg.K_1 <= e.key <= pg.K_6:
                        idx = e.key - pg.K_1  # 0..5
                        items_list = player.inv.list_items()  # [(item_id, count), ...]
                        if idx < len(items_list):
                            iid, _ = items_list[idx]
                            item = item_db.get(iid)
                            ctx = GameCtx(player, enemies, seen)
                            consumed = use_item(item, ctx)
                            if consumed:
                                player.inv.remove(iid, 1)
                        else:
                            LOG.add("Тут порожньо.")
                        ts.end_player()

                    elif e.key == pg.K_i:
                        mode = "inventory"
                        selected_index = 0

                    if dx or dy:
                        try_player_move(player, dx, dy, grid, enemies, ts)

                # ---------- INVENTORY MODE ----------
                elif mode == "inventory":
                    items_list = player.inv.list_items()  # [(item_id, count), ...]
                    if e.key in (pg.K_ESCAPE, pg.K_i):
                        mode = "game"
                    elif e.key == pg.K_DOWN:
                        if items_list:
                            selected_index = (selected_index + 1) % len(items_list)
                    elif e.key == pg.K_UP:
                        if items_list:
                            selected_index = (selected_index - 1) % len(items_list)
                    elif e.key == pg.K_RETURN:
                        if items_list:
                            iid, _ = items_list[selected_index]
                            item = item_db.get(iid)
                            ctx = GameCtx(player, enemies, seen)
                            consumed = use_item(item, ctx)
                            if consumed:
                                player.inv.remove(iid, 1)  # зменшуємо кількість
                                # підстроїти курсор, якщо список скоротився
                                items_list = player.inv.list_items()
                                if selected_index >= len(items_list):
                                    selected_index = max(0, len(items_list) - 1)
                            ts.end_player()
                            mode = "game"

        if not ts.player_turn:
            enemies_turn(player, enemies, grid, ts)

        fov = compute_fov(grid, player.x, player.y, FOV_RADIUS)
        for y in range(ROWS):
            for x in range(COLS):
                if fov[y][x]:
                    seen[y][x] = True

        # ---------- RENDER ----------
        if mode == "game":
            screen.fill((0,0,0))
            draw_map(screen, grid, seen, fov)

            for en in enemies:
                col = COLOR_ENEMY if fov[en.y][en.x] else (80, 40, 40)
                draw_cell(screen, en.x, en.y, col)

            # items on ground
            for (ix, iy), iid in ground_items.items():
                if fov[iy][ix]:
                    pg.draw.rect(screen, (240, 210, 90), pg.Rect(ix*TILE+8, iy*TILE+8, TILE-16, TILE-16))

            draw_cell(screen, player.x, player.y, COLOR_PLAYER)

            hp_text = f"HP:{player.hp}/{player.max_hp}"
            draw_hud(screen,
                     f"SEED:{seed} POS:{player.x},{player.y} MAP:{COLS}x{ROWS} {hp_text}")

        elif mode == "inventory":
            screen.fill((20,20,20))
            font = pg.font.SysFont("Consolas", 20)
            y = 60
            items_list = player.inv.list_items()
            if not items_list:
                screen.blit(font.render("Інвентар порожній", True, (220,220,220)), (40, y))
            else:
                for i, (iid, count) in enumerate(items_list):
                    item = item_db.get(iid)
                    color = (255,255,0) if i == selected_index else (220,220,220)
                    text = f"{i+1}. {item.name} x{count}"
                    screen.blit(font.render(text, True, color), (40, y))
                    y += 28
            screen.blit(font.render("↑↓ вибір, Enter — використати, Esc/I — назад",
                                    True, (160,160,160)), (40, y+40))

        pg.display.flip()

    pg.quit()
    sys.exit()


if __name__ == "__main__":
    main()
