from uml_state_machine import Event


class MyEvent(Event):
    def __init__ (self, event):
        self.event = event

    def id(self):
        if self.event:
            return self.event
        else:
            return 'Check'

    def __str__(self):
        return self.event