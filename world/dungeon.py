import pygame as pg
from .tileset import WALL, FLOOR

def make_map(cols: int, rows: int, rng):
    grid = [[WALL for _ in range(cols)] for _ in range(rows)]
    rooms: list[pg.Rect] = []
    max_rooms = 14
    min_size, max_size = 4, 8

    for _ in range(max_rooms):
        w = rng.randint(min_size, max_size)
        h = rng.randint(min_size, max_size)
        x = rng.randint(1, cols - w - 2)
        y = rng.randint(1, rows - h - 2)
        room = pg.Rect(x, y, w, h)
        if any(room.colliderect(r) for r in rooms):
            continue
        carve_room(grid, room)
        if rooms:
            carve_tunnel(grid, rooms[-1].center, room.center, rng)
        rooms.append(room)

    start = (rooms[0].centerx, int(rooms[0].centery)) if rooms else (cols // 2, rows // 2)
    far   = (rooms[-1].centerx, int(rooms[-1].centery)) if rooms else (cols // 2, rows // 2)
    start = (int(start[0]), int(start[1]))
    far   = (int(far[0]), int(far[1]))
    return grid, start, far, rooms

def carve_room(m, rect: pg.Rect):
    for y in range(rect.top, rect.bottom):
        for x in range(rect.left, rect.right):
            m[y][x] = FLOOR

def carve_tunnel(m, a, b, rng):
    ax, ay = a
    bx, by = b
    if rng.random() < 0.5:
        carve_h(m, ax, bx, ay)
        carve_v(m, ay, by, bx)
    else:
        carve_v(m, ay, by, ax)
        carve_h(m, ax, bx, by)

def carve_h(m, x1, x2, y):
    for x in range(min(x1, x2), max(x1, x2) + 1):
        m[y][x] = FLOOR

def carve_v(m, y1, y2, x):
    for y in range(min(y1, y2), max(y1, y2) + 1):
        m[y][x] = FLOOR