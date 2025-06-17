from state.transition import Transition


class Vertex(object):
    def __init__(self, container):
        self.container = container # region

    def outgoing(self):
        return [transition() for transition in Transition.allInstances
                if transition() and transition().source is self]

    def incoming(self):
        return [transition() for transition in Transition.allInstances
                if transition() and transition().target is self]
