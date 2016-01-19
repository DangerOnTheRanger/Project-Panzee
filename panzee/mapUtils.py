import cocos

def loadMap(path=None):
	if path != None:
		map = cocos.tiles.load(path)
		return map
	else:
		return None

