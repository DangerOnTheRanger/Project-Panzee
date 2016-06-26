from __future__ import print_function
#from map2D import map2D
import time
from tile2D import tile2D

class pathFinder(object):
    statusRunning=0
    statusFoundPath=1
    statusNoPath=2
    modeGrid=0
    modeDiagonals=1
    modeGridAndDiagonals=2
    def __init__(self, map, cost=1):
        self.map = map
        self.grid = None
    def initiateGrid(self):
        self.grid = list()
        for y in range(0,len(self.map.grid)):
            self.grid.append(list())
            for x in range(0,len(self.map.grid[y])):
                self.grid[y].append(None)
    def getGridDis(self, x,y, x2,y2):
        return (abs(y-y2)+abs(x-x2))
    def getTerrianCostInLine(self, x,y, x2,y2):
        cost=0
        while(not (x==x2 and y==y2)):
            if(x<x2):
                x+=1
            elif(x>x2):
                x-=1
            if(y<y2):
                y+=1
            elif(y>y2):
                y-=1
            cost+=self.map.getCost(x,y)
        return cost

    def getTerrianCostAndDiagonalDisInLine(self, x,y, x2,y2):
        cost=0
        while(not (x==x2 and y==y2)):
            if(x<x2):
                x+=1
            elif(x>x2):
                x-=1
            if(y<y2):
                y+=1
            elif(y>y2):
                y-=1
            cost+=self.map.getCost(x,y)+1
        return cost

    def getDiagnolDis(self, x,y, x2,y2):
        cost=0
        while(not (x==x2 and y==y2)):
            if(x<x2):
                x+=1
            elif(x>x2):
                x-=1
            if(y<y2):
                y+=1
            elif(y>y2):
                y-=1
            cost+=1
        return cost

    def getTotalCost(self,x,y,x2,y2,moves,mode):
        if(mode==pathFinder.modeGrid):
            return self.getGridDis(x,y,x2,y2)+self.getTerrianCostInLine(x,y,x2,y2)
        elif(mode==pathFinder.modeDiagonals):
            return self.getDiagnolDis(x,y,x2,y2)+self.getTerrianCostAndDiagonalDisInLine(x,y,x2,y2)
        elif(mode==pathFinder.modeGridAndDiagonals):
            return self.getGridDis(x,y,x2,y2)+self.getDiagnolDis(x,y,x2,y2)
    def withinBounds(self, x,y):
        return (0<=y<len(self.grid) and 0<=x<len(self.grid[y]))
    def isOpen(self,x,y,x2,y2,moves):
        if(self.map.isPassable(x,y) and self.withinBounds(x,y)):
            return ((self.grid[y][x]==None or moves<self.grid[y][x]))
        else:
            return None

    def findPath(self, startX, startY, endX, endY, mode):
        self.initiateGrid()
        x=startX+0
        y=startY+0
        path = list()
        dirs = None
        status = 0
        lastPath=-1
        deadEnd=0
        tc = self.getTotalCost(x,y,endX,endY,0,mode)
        #Run
        while(status==pathFinder.statusRunning):
            if(deadEnd==1):
                if(lastPath<=0):
                    status = pathFinder.statusNoPath
                else:
                    path.pop()
                    lastPath-=1
                    deadEnd=2
                    x = path[lastPath][0]
                    y = path[lastPath][1]
            else:
                if(deadEnd==2):
                    deadEnd=0
                else:
                    path.append([x+0,y+0])
                    lastPath+=1
                self.grid[y][x]=lastPath+0
                #self.printPathMap(path)
                #time.sleep(0.5)
                if(x==endX and y==endY):
                    status = pathFinder.statusFoundPath
                else:
                    dirs=list()
                    # Grid
                    if(mode == pathFinder.modeGrid or mode == pathFinder.modeGridAndDiagonals):
                        up = [x+0,y+1,None,None]
                        if(lastPath>0 and up[0] == path[lastPath-1][0] and up[1] == path[lastPath-1][1]):
                            up[2] = lastPath
                        else:
                            up[2] = lastPath+1
                        up[3] = self.getTotalCost(up[0],up[1],endX,endY,up[2],mode)
                        if(self.isOpen(up[0],up[1],endX,endY,up[2])==True):
                            #print("Up:",up[3])
                            #print("UP")
                            dirs.append(up)

                        right = [x+1,y,None,None]
                        if(lastPath>0 and right[0] == path[lastPath-1][0] and right[1] == path[lastPath-1][1]):
                            right[2] = lastPath
                        else:
                            right[2] = lastPath+1
                        right[3] = self.getTotalCost(right[0],right[1],endX,endY,right[2], mode)
                        if(self.isOpen(right[0],right[1],endX,endY,right[2])==True):
                            #print("Right:",right[3])
                            #print("RIGHT")
                            dirs.append(right)

                        down = [x+0,y-1,None,None]
                        if(lastPath>0 and down[0] == path[lastPath-1][0] and down[1] == path[lastPath-1][1]):
                            down[2] = lastPath
                        else:
                            down[2] = lastPath+1
                        down[3] = self.getTotalCost(down[0],down[1],endX,endY,down[2], mode)
                        if(self.isOpen(down[0],down[1],endX,endY,down[2])==True):
                            #print("Down:",down[3])
                            #print("DOWN")
                            dirs.append(down)

                        left = [x-1,y+0,None,None]
                        if(lastPath>0 and left[0] == path[lastPath-1][0] and left[1] == path[lastPath-1][1]):
                            left[2] = lastPath
                        else:
                            left[2] = lastPath+1
                        left[3] = self.getTotalCost(left[0],left[1],endX,endY,left[2], mode)
                        if(self.isOpen(left[0],left[1],endX,endY,left[2])==True):
                            #print("Left:",left[3])
                            #print("LEFT")
                            dirs.append(left)

                    # Diagonals
                    if(mode == pathFinder.modeDiagonals or mode == pathFinder.modeGridAndDiagonals):
                        upRight = [x+1,y+1,None,None]
                        if(lastPath>0 and upRight[0] == path[lastPath-1][0] and upRight[1] == path[lastPath-1][1]):
                            upRight[2]= lastPath
                        else:
                            upRight[2]= lastPath+1
                        upRight[3] = self.getTotalCost(upRight[0],upRight[1],endX,endY,upRight[2], mode)
                        if(self.isOpen(upRight[0],upRight[1],endX,endY,upRight[2])==True):
                            #print("upRight:",upRight[3])
                            #print("UP RIGHT")
                            dirs.append(upRight)

                        rightDown = [x+1,y-1,None,None]
                        if(lastPath>0 and rightDown[0] == path[lastPath-1][0] and rightDown[1] == path[lastPath-1][1]):
                            rightDown[2] = lastPath
                        else:
                            rightDown[2] = lastPath+1
                        rightDown[3] = self.getTotalCost(rightDown[0],rightDown[1],endX,endY,rightDown[2], mode)
                        if(self.isOpen(rightDown[0],rightDown[1],endX,endY,rightDown[2])==True):
                            #print("RIGHT DOWN")
                            dirs.append(rightDown)

                        downLeft = [x-1,y-1,None,None]
                        if(lastPath>0 and downLeft[0] == path[lastPath-1][0] and downLeft[1] == path[lastPath-1][1]):
                            downLeft[2] = lastPath
                        else:
                            downLeft[2] = lastPath+1
                        downLeft[3] = self.getTotalCost(downLeft[0],downLeft[1],endX,endY,downLeft[2], mode)
                        if(self.isOpen(downLeft[0],downLeft[1],endX,endY,downLeft[2])==True):
                            #print("DOWN LEFT")
                            dirs.append(downLeft)

                        leftUp = [x-1,y+1,None,None]
                        if(lastPath>0 and leftUp[0] == path[lastPath-1][0] and leftUp[1] == path[lastPath-1][1]):
                            leftUp[2] = lastPath
                        else:
                            leftUp[2] = lastPath+1
                        leftUp[3] = self.getTotalCost(leftUp[0],leftUp[1],endX,endY,leftUp[2], mode)
                        if(self.isOpen(leftUp[0],leftUp[1],endX,endY,leftUp[2])==True):
                            #print("LEFT UP")
                            dirs.append(leftUp)

                    if(len(dirs)<=0):
                        deadEnd=1
                    else:
                        temp = dirs[0]
                        for i in dirs:
                            if(i[0]==endX and i[1]==endY):
                                temp=i
                                statues = pathFinder.statusFoundPath
                                break
                            elif(i[3] < temp[3]):
                                temp=i
                        if(i[0] == path[lastPath-1][0] and i[1] == path[lastPath-1][1]):
                            deadEnd=1
                        else:
                            x = temp[0]+0
                            y = temp[1]+0
        if(status==pathFinder.statusFoundPath):
            path.pop(0)
            return path
        elif(status==pathFinder.statusNoPath):
            return None
        else:
            return "ERROR"
    def getPrintCostAtTile(self,x,y):
        if(self.withinBounds(x,y)):
            for y2 in range(0,len(self.map.grid)):
                for x2 in range(0,len(self.map.grid[y2])):
                    if(x==x2 and y==y2):
                        print("@",end="")
                    else:
                        print(self.map.grid[y2][x2].icon,end="")
                print()
            print()
            print("tile [",x,",",y,"], total cost = [",self.grid[y][x],"]",sep="")

    def getTerrianCostInPath(self, path):
        cost=0
        for y in path:
            cost+=self.map.getCost(y[0],y[1])
        return cost

    def printPathMap(self, path):
        temp=False
        #print(path)
        for y in range(0,len(self.map.grid)):
            for x in range(0,len(self.map.grid[y])):
                for i in path:
                    if(x==i[0] and y==i[1]):
                        temp=True
                if(temp):
                    print("@",end="")
                    temp=False
                else:
                    print(self.map.grid[y][x].icon,end="")
            print()
        print()
