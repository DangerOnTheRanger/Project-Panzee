import panzee.map


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
