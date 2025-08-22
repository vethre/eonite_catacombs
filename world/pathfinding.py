import tcod
import numpy as np
from world.tileset import FLOOR

class Pathfinder:
    def __init__(self, grid):
        self.grid = grid
        self._make_graph()

    def _make_graph(self):
        h = len(self.grid)
        w = len(self.grid[0])
        # matrix: 1.0 = can, 0 = wall
        cost = np.zeros((h, w), dtype=np.float32)
        for y in range(h):
            for x in range(w):
                cost[y][x] = 1.0 if self.grid[y][x] == FLOOR else 0.0
        self.astar = tcod.path.AStar(cost, diagonal=False)

    def rebuild_if_needed(self, grid):
        if grid is not self.grid:
            self.grid = grid
            self._make_graph()

    def next_step(self, sx, sy, tx, ty):
        path = self.astar.get_path(sy, sx, ty, tx) # tcod: (row, col) = (y,x)
        if len(path) >= 2:
            ny, nx = path[1]
            return nx, ny
        return sx, sy