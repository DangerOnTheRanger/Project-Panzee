Currently it's just testing/debugging, and hasn't been intigrated into the project yet.
It currently finds the fastest path every time.
A* algorithm

# How to use
run test.py

#Keys
1 - set tile to empty (white)
2 - set tile to start (blue)
3 - set tile to goal (red)
enter - run path finder with debugging enabled
tab - run path finder with debugging disabled
k - kills the path finder
s - saves current map to a specified file
l - loads a map from a specified file
c - clears the map, set's all tiles to empty/passible (white) and removes start and goal.
e - erases/reverts trails, [debugging highlighted tiles, fastest path highlighted trail/tiles]
i - (Doesn't work) new clean map with specified paramiters  
b - "bi" directional path finding (not really bi-directional. meant to find, in witch direction the fastest path is found, from start to goal, or goal to start)
t - benchmark test of pathfinding, 100 cycles, and saves to file "benchmark.txt"
r - swaps start and goal location.
escape - exits program, and kills the path finder if running

#Mouse
left - set tile to full/not passable (green)
right - set tile to empty (white)

#Tile, Types
white - empty tile
green - full/not passable tile
blue - start tile
red - goal/end tile
purple - debugging, this tile is/has been examined
black - fastest path from start to goal
