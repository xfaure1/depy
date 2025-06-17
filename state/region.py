class Region(object):
    def __init__(self, name, state):
        self.name = name
        self.stateMachine = None
        self.transition = []
        self.state = state      # state containing the region
        self.subVertex = []

    def __str__(self):
        if self.state:
            return '%s|%s' % (self.state.name, self.name)
        else:
            return '|%s' % self.name
