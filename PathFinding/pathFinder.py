import window
from time import sleep

class tile():
    def __init__(self, x,y, pathFinder):
        self.x = x
        self.y = y
        self.gScore = float('inf')
        self.fScore = float('inf')
        self.neighbors = []
        self.cameFrom=None # The fastest way to this tile (1 tile, not path)
        self.isOpen = False # is in the "open set"
        self.isClosed = False # is in the "closed set"
        self.pathFinder = pathFinder
        self.updateNeighbors()

    def updateNeighbors(self):
        temp = [self.x+0,self.y+1]
        if(self.pathFinder.withinBounds(temp)): # UP
            self.neighbors.append(temp)
        temp = [self.x-1,self.y+0]
        if(self.pathFinder.withinBounds(temp)): # RIGHT
            self.neighbors.append(temp)
        temp = [self.x+0,self.y-1]
        if(self.pathFinder.withinBounds(temp)): # DOWN
            self.neighbors.append(temp)
        temp = [self.x+1,self.y+0]
        if(self.pathFinder.withinBounds(temp)): # LEFT
            self.neighbors.append(temp)


class path_finder(object):
    def __init__(self, grid):
        self.grid = grid
        self.killSwitch = False
        self.path = None
        self.tiles=[]

    def kill(self):
        self.killSwitch=True

    def getDis(self, start, goal):
        return (abs(start[1]-goal[1])+abs(start[0]-goal[0]))

    def withinBounds(self, loc):
        return (loc[1] >= 0 and
                loc[0] >= 0 and
                loc[1] < len(self.grid) and
                loc[0] < len(self.grid[loc[1]]) and
                self.grid[loc[1]][loc[0]].is_passible())

    def isIn(self, list, tile):
        for y in list:
            if(tile[0]==y[0][0] and tile[1]==y[0][1]):
                return True
        return False

    def getFromTiles(self, loc):
        for temp in self.tiles:
            if(temp.x==loc[0] and temp.y==loc[1]):
                return temp
        return None

    def countOpenTiles(self):
        num=0
        for x in self.tiles:
            if(x.isOpen):
                num+=1
        return num

    def isClosed(self, x,y):
        for temp in self.tiles:
            if(temp.x == x and
                temp.y == y):
                return temp.isClosed
        return None

    def isOpen(self, x,y):
        for temp in self.tiles:
            if(temp.x == x and
                temp.y == y):
                return temp.isOpen
        return None

    def is_in_tiles(self, x,y):
        for temp in self.tiles:
            if(temp.y==y and temp.x==x):
                return temp
        return None

    def get_tile_with_lowest_fscore(self):
        temp2 = None
        for temp in self.tiles:
            if(temp.isOpen and not temp.isClosed and (temp2 == None or temp.fScore<temp2.fScore)):
                temp2 = temp
        return temp2

    def showPath(self):
        for temp in self.path:
            self.grid[temp[1]][temp[0]].set_black()

    def reconstruct_path(self, current, start):
        total_path = []
        total_path.append([current.x,current.y])
        while (self.killSwitch==False):
            if(current.cameFrom!=None):
                current = current.cameFrom
                total_path.append([current.x,current.y])
                if(current.x==start[0] and current.y==start[1]):
                    break
        total_path.pop()
        total_path.reverse()
        #print(total_path, len(total_path))
        self.path = total_path

    def findPath(self, start, goal, debug):
        temp = tile(start[0],start[1],self)
        temp.gScore=0
        temp.fScore=self.getDis([start[0],start[1]],[goal[0],goal[1]])
        temp.isOpen=True
        self.tiles.append(temp)
        while(self.countOpenTiles()>0 and self.killSwitch==False):
            current = self.get_tile_with_lowest_fscore()
            if(debug):
                self.grid[current.y][current.x].set_active()
                sleep(.04)
            if(current.x == goal[0] and
               current.y == goal[1]):
                return self.reconstruct_path(current,start)
                #raise Exception("NOT FINISHED, But path found, needs reconstructing though...")
            current.isOpen=False
            current.isClosed=True
            for temp in current.neighbors:
                temp2 = self.is_in_tiles(temp[0],temp[1])
                tentative_gScore = current.gScore + self.getDis([current.x,current.y], [temp[0],temp[1]])
                if(temp2==None):
                    temp2 = tile(temp[0],temp[1],self)
                    temp2.isOpen=True
                    self.tiles.append(temp2)
                else:
                    if(self.isClosed(temp[0],temp[1])):
                        continue
                    if(not temp2.isOpen): # Discover a new node
                        temp2.isOpen=True
                    elif(tentative_gScore >= temp2.gScore):
                        continue
                # This path is the best until now. Record it!
                temp2.cameFrom = current
                temp2.gScore = tentative_gScore
                temp2.fScore = temp2.gScore + self.getDis([temp2.x,temp2.y],[goal[0],goal[1]])
        return None
