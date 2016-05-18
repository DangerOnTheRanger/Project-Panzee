from cocos.director import director
from cocos import layer

import panzee.maputils
import cocos


class MockCell(object):
    """Mock a cocos2d tile cell for testing purposes.
    Implements everything but the cell attribute.
    """
    def __init__(self, i, j, properties=None):
        self.i = i
        self.j = j
        self.position = (i, j)
        self.properties = properties or dict()

    def __getitem__(self, key):
        return self.properties[key]

    def get(self, key, default=None):
        return self.properties.get(key, default)

class MockMap(object):
    """Mock a cocos2d tile map for testing purposes.
    Implements solely get_cell and __getitem__.
    """
    def __init__(self, map_data):
        self.map_data = map_data

    def get_cell(self, i, j):
        return self.map_data[i][j]


def main():
    cocos.director.director.init(width=600, height=600, caption="Project Panzee")
    cocos.director.director.set_show_FPS(True)
    mapfile = panzee.maputils.loadMap("map.tmx")
    manager = cocos.layer.ScrollingManager()
    manager.set_focus(0, 0)
    layers = list(mapfile.find(cocos.layer.base_layers.Layer))
    for i in range (0,len(layers)):
        manager.add(mapfile[layers[i][0]])
    main_scene = cocos.scene.Scene(manager)
    cocos.director.director.run (main_scene)


if __name__ == "__main__":
    main()
