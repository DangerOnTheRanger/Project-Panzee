#!/usr/bin/env python

try:
    # for Python2
    from Tkinter import *   ## notice capitalized T in Tkinter
except ImportError:
    # for Python3
    from tkinter import *   ## notice here too

from window import CellGrid
from window import Cell
from pathFinder import path_finder




if __name__ == "__main__" :
    app = Tk()
    grid = CellGrid(app, 20, 20, 40)
    grid.pack()
    app.mainloop()
