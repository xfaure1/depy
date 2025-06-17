from uml_state_machine import Event


class MyTimeEvent(Event):
    def __init__ (self, timeout):
        self.timeout = timeout

    def id(self):
        return 'after%s%s' % (self.timeout[0].upper(), self.timeout[1:])

    def __str__(self):
        return 'after(%s)' % self.timeout

