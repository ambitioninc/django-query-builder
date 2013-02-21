

class WindowFunction(object):
    name = ''

    def __init__(self, over, lookup=None):
        """
        :type lookup: str
        """
        self.over = over
        self.lookup = lookup


class Rank(WindowFunction):
    name = 'rank'
