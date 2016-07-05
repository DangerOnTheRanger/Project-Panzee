try:
    # for Python2
    from Tkinter import *   ## notice capitalized T in Tkinter
except ImportError:
    # for Python3
    from tkinter import *   ## notice here too

import tkMessageBox
import Tkinter
import tkFileDialog

from pathFinder import path_finder
import threading
import time

class windowChangeGrid():
    def __int__(self):
        self.toplevel = None
        self.running = False
        self.returnData = None

    def ask(self):
        if(True):
            self.toplevel = Toplevel()
            self.label1 = Label(self.toplevel, text="set width", height=0, width=100)
            self.label1.pack()
            self.e = Entry(self.toplevel)
            self.e.pack()
            self.e.delete(0,END)
            self.e.insert(0, 20)
            self.label2 = Label(self.toplevel, text="set height", height=0, width=100)
            self.label2.pack()
            self.e2 = Entry(self.toplevel)
            self.e2.pack()
            self.e2.delete(0,END)
            self.e2.insert(0, 20)
            self.label3 = Label(self.toplevel, text="set cellSize", height=0, width=100)
            self.label3.pack()
            self.e3 = Entry(self.toplevel)
            self.e3.pack()
            self.e3.delete(0,END)
            self.e3.insert(0, 40)
            self.enter = Button(self.toplevel, text="Enter", width=20, command=self.funcEnter)
            self.enter.pack()
            self.quit = Button(self.toplevel, text="Quit", width=20, command=self.funcQuit)
            self.quit.pack()
            self.returnData=None
            self.toplevel.mainloop()
            self.toplevel.destroy()
            self.running=False
            return self.returnData

    def funcEnter(self):
        self.response=1
        try:
            width = self.e.getint()
            height = self.e2.getint()
            cellSize = self.e3.getint()
            self.returnData = [width,height,cellSize]
            #self.toplevel.quit()
            self.toplevel.destroy()
        except:
            self.returnData = None
            tkMessageBox.showerror(
                "ERROR: ChangeGrid",
                "ERROR: Value(s) not intager\n"
            )
            print("ERROR:", sys.exc_info()[0])
            raise

    def funcQuit(self):
        self.returnData = None
        self.toplevel.destroy()


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
        if(self.fill==Cell.GOAL_COLOR or self.fill==Cell.START_COLOR):
            return
        self.fill = Cell.EMPTY_COLOR_BORDER
        self.draw()

    def set_green(self):
        """ Switch if the cell is filled or not. """
        self.fill= Cell.FILLED_COLOR_BG
        self.draw()

    def set_white(self):
        """ Switch if the cell is filled or not. """
        self.fill=Cell.EMPTY_COLOR_BG
        self.draw()

    def set_start(self):
        self.fill=Cell.START_COLOR
        self.draw()

    def set_goal(self):
        self.fill=Cell.GOAL_COLOR
        self.draw()

    def set_active(self):
        if(self.fill==Cell.GOAL_COLOR or self.fill==Cell.START_COLOR):
            return
        if(self.active):
            self.fill=self.fill2
            self.active=False
        else:
            self.fill2=self.fill
            self.fill=Cell.ACTIVE_COLOR
            self.active=True
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
        self.windowChangeGridInstance = windowChangeGrid()

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

    def findPath(self,showPath=False,showSearchedTiles=False, showTime=False, debugSleep=0):
        self.pf = path_finder(self.grid)
        if(showTime==True):
            timer = time.time()
            self.pf.findPath(self.start,self.goal,showSearchedTiles, debugSleep)
            timer2 = time.time()
            if(self.pf.path):
                print("Found path in ["+str(timer2-timer)+"], with moves ["+str(len(self.pf.path))+"]\n")
                if(showPath):
                    self.pf.showPath()
        elif(showTime==None):
            timer = time.time()
            self.pf.findPath(self.start,self.goal,showSearchedTiles, debugSleep)
            timer2 = time.time()
            if(showPath and self.pf.path):
                self.pf.showPath()
            return (timer2 - timer)
        else:
            self.pf.findPath(self.start,self.goal,showSearchedTiles, debugSleep)
            if(showPath and self.pf.path):
                self.pf.showPath()

    def eraseTrails(self):
        for y in self.grid:
            for x in y:
                if(x.active):
                    x.set_active()
                elif(x.fill==Cell.EMPTY_COLOR_BORDER):
                    x.set_white()

    def drawAll(self):
        for y in self.grid:
            for x in y:
                x.draw()

    def ChangeGridViaWindow(self):
        self.windowChangeGridInstance.ask()
        if(temp!=None):
            width,height,cellSize = temp
            grid = []
            for row in range(width):
                grid.append([])
                for column in range(height):
                    grid[row].append(Cell(self, column, row, cellSize))
                #grid.append(line)
            self.cellSize = cellSize
            self.grid = grid
            self.drawAll()
            print("HERE")

    def saveToFile(self,file,debug=False):
        self.eraseTrails()
        data = ""
        data+=str(self.cellSize)
        data+='\n'
        for y in self.grid:
            for x in y:
                if(x.fill == Cell.START_COLOR):
                    data+="X"
                elif(x.fill == Cell.GOAL_COLOR):
                    data+="Z"
                elif(x.fill == Cell.FILLED_COLOR_BG):
                    data+="#"
                elif(x.fill == Cell.EMPTY_COLOR_BG):
                    data+="-"
            data+='\n'
        if(debug):
            return data
        else:
            file.write(data)
            file.close()

    def switchStartGoal(self):
        self.grid[self.start[1]][self.start[0]].set_goal()
        self.grid[self.goal[1]][self.goal[0]].set_start()
        temp = self.start
        self.start = self.goal
        self.goal = temp

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
            elif(event.char=='2'):
                if(self.start!=None):
                    self.grid[self.start[1]][self.start[0]].set_white()
                self.start = [column,row]
                cell = self.grid[row][column]
                cell.set_start()
            elif(event.char=='3'):
                if(self.goal!=None):
                    self.grid[self.goal[1]][self.goal[0]].set_white()
                self.goal = [column,row]
                cell = self.grid[row][column]
                cell.set_goal()
            elif(event.char=='\x1b'):
                if(self.thread!=None and self.thread.isAlive()):
                    self.pf.kill()
                    self.thread.join(1)

                exit(0)
            elif(event.char=='\r'):
                if(self.start!=None and self.goal!=None and (self.thread==None or not self.thread.isAlive())):
                    self.thread = threading.Thread(target=self.findPath, args=([True,True,True,0.04]))
                    self.thread.start()
            elif(event.char=='\t'):
                if(self.start!=None and self.goal!=None and (self.thread==None or not self.thread.isAlive())):
                    self.thread = threading.Thread(target=self.findPath, args=([True,True,True,0]))
                    self.thread.start()
            elif(event.char=='e'):
                self.eraseTrails()
            elif(event.char=='i'):
                self.ChangeGridViaWindow()
            elif(event.char=='b'):
                if(self.start!=None and self.goal!=None and (self.thread==None or not self.thread.isAlive())):
                    self.thread = threading.Thread(target=self.findPath, args=([True,True,True,0]))
                    self.thread.start()
                    self.switchStartGoal()
                    self.thread2 = threading.Thread(target=self.findPath, args=([True,True,True,0]))
                    self.thread2.start()
            elif(event.char=='t'):
                benchTimes = []
                least = [0,float('inf')]
                max = [0,0]
                average = 0
                toCycle = 100
                for cycles in range(1,toCycle):
                    temp = self.findPath(False,False,None,0)
                    benchTimes.append(temp)
                    if(temp > max[1]):
                        max = [cycles-1, temp]
                    if(temp < least[1]):
                        least = [cycles-1, temp]
                    average+=temp
                average=(average/toCycle)
                f = open("benchmark.txt", "w")
                data = self.saveToFile(f,True)
                f.writelines(["benchmark", '\n',"fastest time", str(least[1]), '\n',"slowest time", str(max[1]), '\n', "average time", str(average), '\n',data])
                f.close()

            elif(event.char=='r'):
                self.switchStartGoal()
            elif(event.char=='s'):
                f = tkFileDialog.asksaveasfile(mode='w', defaultextension=".txt")
                if f is None: # asksaveasfile return `None` if dialog closed with "cancel".
                    return
                self.saveToFile(f)
            elif(event.char=='l'):
                f = tkFileDialog.askopenfile(mode='r', defaultextension=".txt")
                if f is None: # asksaveasfile return `None` if dialog closed with "cancel".
                    return
                grid=[]
                width = -1
                height=-1
                num = -1
                try:
                    cellSize = int(float(f.readline()))
                    for line in f:
                        height+=1
                        num=-1
                        if(num > width):
                            width = num
                        grid.append([])
                        for char in line:
                            if(char=='\n'):
                                continue
                            num+=1
                            tile = Cell(self, num, height, cellSize)
                            if(char=="#"):
                                tile.fill = Cell.FILLED_COLOR_BG
                            elif(char=="-"):
                                tile.fill = Cell.EMPTY_COLOR_BG
                            elif(char=="X"):
                                tile.fill = Cell.START_COLOR
                                start = [num,height]
                            elif(char=="Z"):
                                tile.fill = Cell.GOAL_COLOR
                                goal = [num,height]
                            grid[height].append(tile)
                            #print(height, num,char)
                            #time.sleep(1)
                        '''for y in grid:
                            for x in y:
                                print(x.abs,x.ord,x.fill)
                        exit(2)'''
                    self.cellSize = cellSize
                    self.grid = grid
                    self.start = start
                    self.goal = goal
                    self.drawAll()
                except:
                    print "ERROR: Loading map file",sys.exc_info()[0]
                    top = Toplevel()
                    top.title("ERROR")
                    msg = Message(top, text="ERROR loading file")
                    msg.pack()
                    button = Button(top, text="Ok", command=top.destroy)
                    button.pack()
                    raise
                f.close()
            elif(event.char=='c'):
                for y in self.grid:
                    for x in y:
                        if(x.active):
                            x.set_active()
                        x.set_white()
                self.start=None
                self.goal=None
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

    def handleMouseClick2(self, event):
        row, column = self._eventCoords(event)
        if(column<len(self.grid) and row<len(self.grid[column])):
            cell = self.grid[row][column]
            cell.set_white()

    def handleMouseMotion(self, event):
        row, column = self._eventCoords(event)
        if(column<len(self.grid) and row<len(self.grid[column])):
            cell = self.grid[row][column]

            cell.set_green()

    def handleMouseMotion2(self, event):
        row, column = self._eventCoords(event)
        if(column<len(self.grid) and row<len(self.grid[column])):
            cell = self.grid[row][column]

            cell.set_white()
