# main.py — Eonite Catacombs M2.1
import sys
import pygame as pg

# Core
from core.settings import *
from core.rng import rng_from_seed
from core.events import LOG

# World
from world.dungeon import make_map
from world.pathfinding import Pathfinder
from world.fov import compute_fov, can_see
from world.tileset import WALL, FLOOR

# UI
from ui.hud import draw_hud

# Game
from game.actor import Actor
from game.turn_system import TurnSystem
from game.spawns import spawn_enemies, spawn_items, spawn_terminals, pick_stairs_room
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


def enemies_turn(player: Actor, enemies, grid, ts: TurnSystem, pathfinder: Pathfinder):
    from core.settings import AGGRO_RADIUS, MAX_ENEMY_STEPS
    for e in list(enemies):
        if not e.alive:
            enemies.remove(e)
            continue

        # якщо бачить гравця — «агриться» і запам'ятовує позицію
        if can_see(grid, e.x, e.y, player.x, player.y, radius=AGGRO_RADIUS):
            e.aggro = True
            e.last_known_player = (player.x, player.y)

        # якщо поруч — атака
        if e.distance2(player) == 1:
            from game.combat import attack
            killed = attack(e, player)
            if killed:
                from core.events import LOG
                LOG.add("Ти загинув. Натисни Esc, щоб вийти.")
            continue

        # якщо агрований і знає останню позицію — крок за A*
        moved = False
        if e.aggro and e.last_known_player:
            tx, ty = e.last_known_player
            for _ in range(MAX_ENEMY_STEPS):
                nx, ny = pathfinder.next_step(e.x, e.y, tx, ty)
                # якщо шлях не рухає — стоп
                if (nx, ny) == (e.x, e.y):
                    break
                # не наступати на інших ворогів/гравця
                if (nx, ny) == (player.x, player.y):
                    break
                if any( (o is not e) and o.alive and (o.x, o.y)==(nx, ny) for o in enemies ):
                    break
                e.x, e.y = nx, ny
                moved = True
                # якщо дійшли до точки — скинемо пам'ять
                if (e.x, e.y) == (tx, ty):
                    e.last_known_player = None
                    break

        # якщо не рухався і не бачить — легкий «тупцювання» або стоїть
        if not moved and not e.aggro:
            # маленький шанс посунутися вбік, якщо клітинка прохідна
            import random
            for _ in range(2):
                dx, dy = random.choice([(1,0),(-1,0),(0,1),(0,-1)])
                nx, ny = e.x+dx, e.y+dy
                if 0 <= nx < COLS and 0 <= ny < ROWS and grid[ny][nx] == FLOOR:
                    # не ліземо в інших
                    if (nx, ny) != (player.x, player.y) and not any((o is not e) and (o.x,o.y)==(nx,ny) for o in enemies):
                        e.x, e.y = nx, ny
                        break

    ts.end_enemies()
# --------------------------------------------------------------------------------------
def main(seed: str | None = DEFAULT_SEED):
    pg.init()
    screen = pg.display.set_mode((W, H))
    pg.display.set_caption("Eonite Catacombs — M3+M4")
    clock = pg.time.Clock()

    # стани
    state = GameState()               # зараз майже не юзаємо, але хай живе
    mode = "game"                     # або "inventory"
    selected_index = 0

    # контент
    rng = rng_from_seed(seed)
    item_db = ItemDB()
    item_db.load_from("data/items.json")

    # прогрес
    level = 1
    collected_lore = []

    # об'єкти рівня (заповнимо в build_level)
    grid = rooms = None
    sx = sy = 0
    ground_items = {}     # {(x,y): item_id}
    terminals = {}        # {(x,y): lore_text}
    stairs = (0, 0)
    seen = []
    player = None
    enemies = []
    pathfinder = None

    def build_level():
        """Генерація/перегенерація рівня + оновлення pathfinder."""
        nonlocal grid, rooms, sx, sy, ground_items, terminals, stairs, seen, pathfinder, player, enemies

        grid, (sx, sy), _, rooms = make_map(COLS, ROWS, rng)

        if player is None:
            player = Actor(sx, sy, name="Ти", hp=12, atk=4, df=1)
        else:
            player.x, player.y = sx, sy   # переносимо координати, стати зберігаємо

        enemies = spawn_enemies(grid, rooms, rng, count=4 + level // 2)
        ground_items = spawn_items(rooms, rng, pool=["medkit", "bomb", "flare"], per_room_chance=0.6)
        terminals = spawn_terminals(rooms, rng, "data/lore.json", count=1 + level // 2)
        stairs = pick_stairs_room(rooms, rng)

        # пам'ять/видимість
        nonlocal seen
        seen = [[False for _ in range(COLS)] for _ in range(ROWS)]

        # оновити A*
        nonlocal pathfinder
        pathfinder = Pathfinder(grid)

    # перший рівень
    build_level()
    ts = TurnSystem()
    LOG.add("Welcome to the Catacombs. Arrows/WASD — рух, G — пікап, I — інвентар, E — дія, 1..6 — швидке юзання.")

    # ----------------------------------------------------------------------------------
    # Головний цикл
    running = True
    while running:
        clock.tick(FPS)

        for ev in pg.event.get():
            if ev.type == pg.QUIT:
                running = False

            elif ev.type == pg.KEYDOWN:
                # ---------------- GAME MODE ----------------
                if mode == "game" and ts.player_turn:
                    dx = dy = 0
                    if ev.key in (pg.K_ESCAPE,):
                        running = False

                    elif ev.key in (pg.K_LEFT, pg.K_a):   dx = -1
                    elif ev.key in (pg.K_RIGHT, pg.K_d):  dx =  1
                    elif ev.key in (pg.K_UP, pg.K_w):     dy = -1
                    elif ev.key in (pg.K_DOWN, pg.K_s):   dy =  1

                    elif ev.key in (pg.K_PERIOD, pg.K_COMMA):  # пропустити хід
                        ts.end_player()

                    elif ev.key == pg.K_g:  # пікап з підлоги (атомарно)
                        pos = (player.x, player.y)
                        iid = ground_items.pop(pos, None)
                        if iid is None:
                            LOG.add("Тут нічого підбирати.")
                        else:
                            player.inv.add(iid, 1)
                            LOG.add(f"Ти підібрав {item_db.get(iid).name}.")
                            ts.end_player()

                    elif ev.key == pg.K_e:  # дія: термінал / сходи
                        pos = (player.x, player.y)
                        text = terminals.pop(pos, None)
                        if text:
                            LOG.add(f"[Термінал] {text}")
                            collected_lore.append(text)
                            ts.end_player()
                        elif pos == stairs:
                            level += 1
                            LOG.add(f"Ти спускаєшся на рівень {level}…")
                            build_level()
                            ts.end_player()
                        else:
                            LOG.add("Нема з чим взаємодіяти.")

                    elif pg.K_1 <= ev.key <= pg.K_6:  # швидке використання інвентаря по індексу
                        idx = ev.key - pg.K_1  # 0..5
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

                    elif ev.key == pg.K_i:
                        mode = "inventory"
                        selected_index = 0

                    # рух/атака, якщо натиснуті стрілки/wasd
                    if dx or dy:
                        try_player_move(player, dx, dy, grid, enemies, ts)

                # ---------------- INVENTORY MODE ----------------
                elif mode == "inventory":
                    items_list = player.inv.list_items()  # [(item_id, count), ...]
                    if ev.key in (pg.K_ESCAPE, pg.K_i):
                        mode = "game"
                    elif ev.key == pg.K_DOWN and items_list:
                        selected_index = (selected_index + 1) % len(items_list)
                    elif ev.key == pg.K_UP and items_list:
                        selected_index = (selected_index - 1) % len(items_list)
                    elif ev.key == pg.K_RETURN and items_list:
                        iid, _ = items_list[selected_index]
                        item = item_db.get(iid)
                        ctx = GameCtx(player, enemies, seen)
                        consumed = use_item(item, ctx)
                        if consumed:
                            player.inv.remove(iid, 1)
                            items_list = player.inv.list_items()
                            if selected_index >= len(items_list):
                                selected_index = max(0, len(items_list) - 1)
                        ts.end_player()
                        mode = "game"

        # Хід ворогів після твого
        if not ts.player_turn:
            enemies_turn(player, enemies, grid, ts, pathfinder)

        # FOV + "seen"
        fov = compute_fov(grid, player.x, player.y, FOV_RADIUS)
        for y in range(ROWS):
            for x in range(COLS):
                if fov[y][x]:
                    seen[y][x] = True

        # ---------------- RENDER ----------------
        if mode == "game":
            screen.fill((0, 0, 0))
            draw_map(screen, grid, seen, fov)

            # термінали
            for (ix, iy), _ in terminals.items():
                if fov[iy][ix]:
                    pg.draw.rect(screen, COLOR_TERMINAL, pg.Rect(ix*TILE+8, iy*TILE+8, TILE-16, TILE-16))

            # сходи
            sx_, sy_ = stairs
            if fov[sy_][sx_]:
                pg.draw.rect(screen, COLOR_STAIRS, pg.Rect(sx_*TILE+6, sy_*TILE+6, TILE-12, TILE-12))

            # предмети на підлозі
            for (ix, iy), iid in ground_items.items():
                if fov[iy][ix]:
                    pg.draw.rect(screen, (240, 210, 90), pg.Rect(ix*TILE+8, iy*TILE+8, TILE-16, TILE-16))

            # вороги
            for en in enemies:
                col = COLOR_ENEMY if fov[en.y][en.x] else (80, 40, 40)
                draw_cell(screen, en.x, en.y, col)

            # гравець
            draw_cell(screen, player.x, player.y, COLOR_PLAYER)

            # HUD
            hp_text = f"HP:{player.hp}/{player.max_hp}  LVL:{level}"
            draw_hud(
                screen,
                f"SEED:{seed} POS:{player.x},{player.y} MAP:{COLS}x{ROWS} {hp_text}  [I] інв [G] пікап [E] дія [1..6] швидко"
            )

        elif mode == "inventory":
            screen.fill((20, 20, 20))
            font = pg.font.SysFont("Consolas", 20)
            y = 60
            items_list = player.inv.list_items()
            if not items_list:
                screen.blit(font.render("Інвентар порожній", True, (220, 220, 220)), (40, y))
            else:
                for i, (iid, count) in enumerate(items_list):
                    item = item_db.get(iid)
                    color = (255, 255, 0) if i == selected_index else (220, 220, 220)
                    text = f"{i+1}. {item.name} x{count}"
                    screen.blit(font.render(text, True, color), (40, y))
                    y += 28
            screen.blit(font.render("↑↓ вибір, Enter — використати, Esc/I — назад",
                                    True, (160, 160, 160)), (40, y+40))

        pg.display.flip()

    pg.quit()
    sys.exit()

if __name__ == "__main__":
    main()
