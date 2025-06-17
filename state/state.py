from state.vertex import Vertex


class State(Vertex):
    def __init__(self, name, container):
        Vertex.__init__(self, container)
        self.name = name
        self.region = []
        self.entry = None
        self.exit = None
        self.doActivity = None
        self.deferrableTrigger = []
        self.subMachine = None
        self.connection = []
        self.connectionPoint = []
        self.note = ''  # non UML

    def isOrthogonal(self):
        return False

    def isComposite(self):
        return len(self.region) > 0

    def __str__(self):
        return self.name

    def Print(self):
        print("name " + self.name)
        print("cont " + str(self.container))
        print("region " + str(self.region))
        print("name " + str(self.outgoing()))
