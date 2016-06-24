class tile2D(object):
    lastID=0
    def __init__(self, icon,passable,cost):
        self.icon = icon
        self.passable = passable
        self.cost = cost
        tile2D.lastID+=1
        self.id = tile2D.lastID+0
    def isPassable(self):
        return self.passable
    def getCost(self):
        return self.cost
    def copy(self):
        return tile2D(self.icon,self.passable,self.cost)
        #return copy.deepcopy(self)
