from __future__ import print_function
import random
from tile2D import tile2D
from map2DPathFinder import pathFinder

class map2D(object):
    lastID = 0
    def __init__(self):
        self.grid = None
        self.pathFinder = pathFinder(self)
        map2D.lastID+=1
        self.uid = map2D.lastID+0
    def isAdjacent(self,x,y,x2,y2):
        return (abs(y-y2)<=1 and abs(x-x2)<=1)
    def generateEmptyMap(self, sizeX, sizeY, tile=tile2D("-",True,1)):
        self.grid = list()
        for y in range(0,sizeY):
            self.grid.append(list())
            for x in range(0,sizeX):
                self.grid[y].append(tile.copy())
    def withinBounds(self, x,y):
        return (0<=y<len(self.grid) and 0<=x<len(self.grid[y]))
    def isPassable(self,x,y):
        if(self.withinBounds(x,y)):
            return self.grid[y][x].isPassable()
        else:
            return None
    def toFile(self, name):
        with open(name, 'w') as f:
            for y in self.grid:
                for x in y:
                    f.write(x.icon)
                f.write('\n')

    def fromFile(self,name,tiles):
        self.grid=list()
        lastY=-1
        tilesLen=len(tiles)
        with open(name, 'r') as f:
            for y in f:
                self.grid.append(list())
                lastY+=1
                for x in y:
                    for i in range(0,tilesLen):
                        if(tiles[i].icon==x):
                            self.grid[lastY].append(tiles[i].copy())
                            break
    def setTileAt(self, x,y,tile,copyTile=True):
        if(self.withinBounds(x,y)):
            if(copyTile):
                self.grid[y][x] = tile.copy()
            else:
                self.grid[y][x] = tile
            return True
        else:
            return None
    def getCost(self, x,y):
        if(self.withinBounds(x,y)):
            return self.grid[y][x].getCost()
        else:
            return None
    def generateMap(self, sizeX, sizeY, weightedTiles):
        self.generateEmptyMap(sizeX, sizeY)
        for y in range(0,sizeY):
            for x in range(0,sizeX):
                self.grid[y][x] = random.choice(weightedTiles)
    def printMap(self):
        print("width [",len(self.grid),"], height [",len(self.grid[0]),"]",sep="")
        for y in self.grid:
            for x in y:
                print(x.icon,end="")
            print()
        print()
    def findPath(self, startX, startY, endX, endY):
        if(self.withinBounds(startX,startY) and self.withinBounds(endX,endY) and self.isPassable(startX,startY) and self.isPassable(endX,endY)):
            return self.pathFinder.findPath(startX, startY, endX, endY)
        else:
            return None
    def printPathMap(self, path):
        if(isinstance(path,list)):
            self.pathFinder.printPathMap(path)
            return True
        else:
            return False
