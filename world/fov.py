import tcod
from tcod import libtcodpy
from .tileset import FLOOR

def compute_fov(grid, px, py, radius: int):
    h = len(grid)
    w = len(grid[0])
    transparent = [[grid[y][x] == FLOOR for x in range(w)] for y in range(h)]
    fov = tcod.map.compute_fov(transparent, (py, px), radius=radius, algorithm=libtcodpy.FOV_RESTRICTIVE)
    return fov # boolean [<y, x>]

def can_see(grid, ax, ay, bx, by, radius: int) -> bool:
    fov = compute_fov(grid, ax, ay, radius)
    # fov - [y][x]
    if 0 <= by < len(fov) and 0 <= bx < len(fov[0]):
        return bool(fov[by][bx])
    return False