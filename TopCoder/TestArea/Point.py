class Point(object):
    def __init__(self, x = 0, y = 0):
        self.x = x
        self.y = y

    def distance(self):
        """Find distance from origin"""
        return (self.x**2 + self.y**2)**0.5