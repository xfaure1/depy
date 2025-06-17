from state.vertex import Vertex


class PseudoState(Vertex):
    def __init__(self, name, kind, container):
        Vertex.__init__(self, container)
        self.name = name
        self.kind = kind
        self.stateMachine = None
        self.state = None  # attribute valid when used as a connectionPoint

    def __str__(self):
        return self.name
