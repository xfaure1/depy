
class MyEvent(object):
    def __init__ (self, event):
        self.event = event

    def id(self):
        if self.event:
            return self.event
        else:
            return 'Check'

    def __str__(self):
        return self.event