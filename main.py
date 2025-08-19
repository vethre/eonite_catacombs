# M0
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

# Game (Spawns, Actors, Turns)
from game.actor import Actor
from game.turn_system import TurnSystem
from game.spawns import spawn_enemies
from game.combat import attack

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
    # true if passed
    nx, ny = player.x + dx, player.y + dy
    if not passable(grid, nx, ny):
        return False
    enemy = blocked_by_enemy(enemies, nx, ny)
    if enemy:
        # bump-attack
        killed = attack(player, enemy)
        if killed:
            enemies.remove(enemy)
        ts.end_player()
        return True
    # just move
    player.move_by(dx, dy)
    ts.end_player()
    return True

def enemies_turn(player: Actor, enemies, grid, ts: TurnSystem):
    for e in list(enemies):
        if not e.alive:
            enemies.remove(e)
            continue
        # if nearby — attack
        if e.distance2(player) == 1:
            killed = attack(e, player)
            if killed:
                LOG.add("Ти загинув. Натисни Esc, щоб вийти.")
                # here we can change the game state to DEAD
            continue
        # otherwise: step closer using Manhattan distance, no pathfinding (simple AI)
        dx = 1 if player.x > e.x else -1 if player.x < e.x else 0
        dy = 1 if player.y > e.y else -1 if player.y < e.y else 0
        # try x and y (shuffle a bit for unpredictability)
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
    pg.display.set_caption("Eonite Catacombs — M1")
    clock = pg.time.Clock()

    rng = rng_from_seed(seed)
    grid, (sx, sy), _, rooms = make_map(COLS, ROWS, rng)

    player = Actor(sx, sy, name="Ти", hp=12, atk=4, df=1)
    enemies = spawn_enemies(grid, rooms, rng, count=4)

    ts = TurnSystem()
    seen = [[False for _ in range(COLS)] for _ in range(ROWS)]
    LOG.add("Welcome to the Catacombs. Arrows - movement, ESC - exit")

    running = True
    while running:
        clock.tick(FPS)

        # input only on player's turn
        for e in pg.event.get():
            if e.type == pg.QUIT:
                running = False
            elif e.type == pg.KEYDOWN and ts.player_turn:
                dx = dy = 0
                if e.key in (pg.K_ESCAPE,):
                    running = False
                elif e.key in (pg.K_LEFT, pg.K_a):   dx = -1
                elif e.key in (pg.K_RIGHT, pg.K_d):  dx =  1
                elif e.key in (pg.K_UP, pg.K_w):     dy = -1
                elif e.key in (pg.K_DOWN, pg.K_s):   dy =  1
                elif e.key in (pg.K_PERIOD, pg.K_COMMA):  # waiting the move
                    ts.end_player()

                if dx or dy:
                    try_player_move(player, dx, dy, grid, enemies, ts)

        # if player turn was spent — enemies move
        if not ts.player_turn:
            enemies_turn(player, enemies, grid, ts)

        # FOV + seen
        fov = compute_fov(grid, player.x, player.y, FOV_RADIUS)
        for y in range(ROWS):
            for x in range(COLS):
                if fov[y][x]:
                    seen[y][x] = True

        # render
        screen.fill((0,0,0))
        draw_map(screen, grid, seen, fov)

        # enemies
        for en in enemies:
            col = COLOR_ENEMY if fov[en.y][en.x] else (80, 40, 40)
            draw_cell(screen, en.x, en.y, col)

        # player
        draw_cell(screen, player.x, player.y, COLOR_PLAYER)

        hp_text = f"HP:{player.hp}/{player.max_hp}"
        draw_hud(screen, f"SEED:{seed}  POS:{player.x},{player.y}  MAP:{COLS}x{ROWS}  {hp_text}")
        pg.display.flip()

    pg.quit()
    sys.exit()

if __name__ == "__main__":
    main()