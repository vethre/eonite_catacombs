import tcod
from tcod import libtcodpy
from .tileset import FLOOR

def compute_fov(grid, px, py, radius: int):
    h = len(grid)
    w = len(grid[0])
    transparent = [[grid[y][x] == FLOOR for x in range(w)] for y in range(h)]
    fov = tcod.map.compute_fov(transparent, (py, px), radius=radius, algorithm=libtcodpy.FOV_RESTRICTIVE)
    return fov # boolean [<y, x>]