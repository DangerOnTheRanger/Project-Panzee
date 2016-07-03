try:
    # for Python2
    from Tkinter import *   ## notice capitalized T in Tkinter
except ImportError:
    # for Python3
    from tkinter import *   ## notice here too

from pathFinder import path_finder
import threading
import time

class Cell():
    FILLED_COLOR_BG = "green"
    EMPTY_COLOR_BG = "white"
    FILLED_COLOR_BORDER = "green"
    EMPTY_COLOR_BORDER = "black"
    START_COLOR = "blue"
    GOAL_COLOR = "red"
    ACTIVE_COLOR = "purple"

    def __init__(self, master, x, y, size):
        """ Constructor of the object called by Cell(...) """
        self.master = master
        self.abs = x
        self.ord = y
        self.size= size
        self.fill= Cell.EMPTY_COLOR_BG
        self.active=False

    '''def _switch(self):
        """ Switch if the cell is filled or not. """
        self.fill= not self.fill'''

    def set_black(self):
        self.fill = Cell.EMPTY_COLOR_BORDER
        self.draw()

    def set_green(self):
        """ Switch if the cell is filled or not. """
        self.fill= Cell.FILLED_COLOR_BG

    def set_white(self):
        """ Switch if the cell is filled or not. """
        self.fill=Cell.EMPTY_COLOR_BG

    def set_start(self):
        self.fill=Cell.START_COLOR

    def set_goal(self):
        self.fill=Cell.GOAL_COLOR

    def set_active(self):
        if(self.active):
            self.fill=self.fill2
        else:
            self.fill2=self.fill
            self.fill=Cell.ACTIVE_COLOR
        self.draw()

    def is_passible(self):
        return (self.fill!=Cell.FILLED_COLOR_BG)

    def draw(self):
        """ order to the cell to draw its representation on the canvas """
        if self.master != None :
            fill = self.fill
            #fill = Cell.FILLED_COLOR_BG
            outline = Cell.EMPTY_COLOR_BORDER

            #if not self.fill:
            #    fill = Cell.EMPTY_COLOR_BG
            #    outline = Cell.EMPTY_COLOR_BORDER

            xmin = self.abs * self.size
            xmax = xmin + self.size
            ymin = self.ord * self.size
            ymax = ymin + self.size

            self.master.create_rectangle(xmin, ymin, xmax, ymax, fill = fill, outline = outline)

class CellGrid(Canvas):
    def __init__(self,master, rowNumber, columnNumber, cellSize, *args, **kwargs):
        Canvas.__init__(self, master, width = cellSize * columnNumber , height = cellSize * rowNumber, *args, **kwargs)
        self.start=None
        self.goal=None
        self.cellSize = cellSize
        self.thread=None

        self.grid = []
        for row in range(rowNumber):

            line = []
            for column in range(columnNumber):
                line.append(Cell(self, column, row, cellSize))

            self.grid.append(line)

        self.bind("<KeyRelease>", self.key)
        #bind click action
        self.bind("<Button-1>", self.handleMouseClick)

        #bind click action
        self.bind("<Button-3>", self.handleMouseClick2)

        #bind moving while clicking
        self.bind("<B1-Motion>", self.handleMouseMotion)

        #bind moving while clicking
        self.bind("<B3-Motion>", self.handleMouseMotion2)



        #bind release button action - clear the memory of midified cells.
        #self.bind("<ButtonRelease-1>", lambda event: self.switched.clear())

        #bind release button action - clear the memory of midified cells.
        #self.bind("<ButtonRelease-3>", lambda event: self.switched.clear())

        #Needed to accept keys
        self.focus_set()

        self.draw()



    def draw(self):
        for row in self.grid:
            for cell in row:
                cell.draw()

    def _eventCoords(self, event):
        row = int(event.y / self.cellSize)
        column = int(event.x / self.cellSize)
        return row, column

    def findPath(self,debug=False):
        self.pf = path_finder(self.grid)
        if(debug):
            self.pf.findPath(self.start,self.goal,True)
            if(self.pf.path):
                print("DONE! in <Timer disabled, debug mode ON> with moves ", len(self.pf.path), ", ", self.pf.path)
            else:
                print("No Path Found! in <Timer disabled, debug mode ON> ")
        else:
            timer = time.time()
            self.pf.findPath(self.start,self.goal,False)
            timer2 = time.time()
            if(self.pf.path):
                print("Found Path! in <", (timer2-timer), "> with moves ", len(self.pf.path), ", ", self.pf.path)
            else:
                print("No Path found! in <", (timer2-timer), ">")

        if(self.pf.path):
            self.pf.showPath()


    def key(self, event):
        row, column = self._eventCoords(event)
        if(column<len(self.grid) and row<len(self.grid[column])):
            if(event.char=='1'):
                if([column,row]==self.start):
                    self.start=None
                elif([column,row]==self.goal):
                    self.goal=None
                cell = self.grid[row][column]
                cell.set_white()
                cell.draw()
            elif(event.char=='2'):
                if(self.start!=None):
                    self.grid[self.start[1]][self.start[0]].set_white()
                    self.grid[self.start[1]][self.start[0]].draw()
                self.start = [column,row]
                cell = self.grid[row][column]
                cell.set_start()
                cell.draw()
            elif(event.char=='3'):
                if(self.goal!=None):
                    self.grid[self.goal[1]][self.goal[0]].set_white()
                    self.grid[self.goal[1]][self.goal[0]].draw()
                self.goal = [column,row]
                cell = self.grid[row][column]
                cell.set_goal()
                cell.draw()
            elif(event.char=='\x1b'):
                if(self.thread!=None and self.thread.isAlive()):
                    self.pf.kill()
                    self.thread.join(1)

                exit(0)
            elif(event.char=='\r'):
                if(self.start!=None and self.goal!=None and (self.thread==None or not self.thread.isAlive())):
                    self.thread = threading.Thread(target=self.findPath, args=([True]))
                    self.thread.start()
            elif(event.char=='\t'):
                if(self.start!=None and self.goal!=None and (self.thread==None or not self.thread.isAlive())):
                    self.thread = threading.Thread(target=self.findPath, args=([False]))
                    self.thread.start()
            elif(event.char=='c'):
                for y in self.grid:
                    for x in y:
                        if(x.active):
                            x.set_active()
                        x.set_white()
                        x.draw()
            elif(event.char=='k'):
                self.pf.kill()
                self.thread.join(1)
            else:
                print(repr(event.char))
        #print "pressed", repr(event.char),row, column

    def handleMouseClick(self, event):
        row, column = self._eventCoords(event)
        if(column<len(self.grid) and row<len(self.grid[column])):
            cell = self.grid[row][column]
            cell.set_green()
            cell.draw()

    def handleMouseClick2(self, event):
        row, column = self._eventCoords(event)
        if(column<len(self.grid) and row<len(self.grid[column])):
            cell = self.grid[row][column]
            cell.set_white()
            cell.draw()

    def handleMouseMotion(self, event):
        row, column = self._eventCoords(event)
        if(column<len(self.grid) and row<len(self.grid[column])):
            cell = self.grid[row][column]

            cell.set_green()
            cell.draw()

    def handleMouseMotion2(self, event):
        row, column = self._eventCoords(event)
        if(column<len(self.grid) and row<len(self.grid[column])):
            cell = self.grid[row][column]

            cell.set_white()
            cell.draw()
