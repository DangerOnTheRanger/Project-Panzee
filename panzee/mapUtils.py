import cocos

def loadMap(path=None):
    if path != None:
        map = cocos.tiles.load(path)
        return map
    else:
        return None

def getCellProperty(cell, var):
#	(cocos.tiles.Cell, String)
    if  not issubclass(type(cell), cocos.tiles.Cell):
        raise TypeError 
    try:
        return cell[var]
    except KeyError:
        return None

def setCellProperty(cell, var, set):
    #(cocos.tiles.Cell, String)
    if  not issubclass(type(cell), cocos.tiles.Cell):
        raise TypeError 
    try:
        cell[var] = set
    except KeyError:
        return None

def getCellsWithValue(maplayer, var, value):
    last = -1
    cells = [[0 for x in range(5)] for x in range(5)] 
    for x in range (0,len(maplayer)):
        for y in range (0,len(maplayer[x])):
            if(getCellProperty(maplayer[x][y],var)):
                last+=1
                cells[last][0]=x
                cells[last][1]=y
                
            
    return cells        
            
            