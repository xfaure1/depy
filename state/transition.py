import weakref


class Transition(object):
    allInstances = []

    def __init__(self, kind, region, source, target, trigger, guard, effect):
        self.kind = kind         # TransitionKind
        self.container = region  # Region
        self.source = source     # State
        self.target = target     # State
        self.trigger = trigger   # Trigger
        self.effect = effect     # Behavior
        self.guard = guard       # Constraint
        self.allInstances.append(weakref.ref(self))

        # allInstances maintenance: remove references to dead transitions
        self.allInstances[:] = [trans_ref
                                for trans_ref in Transition.allInstances
                                if trans_ref()]

    def get_str(self):
        text_parts = []
        if self.trigger:
            text_parts.append(str(self.trigger.event))
        if self.guard:
            text_parts.append('[%s]' % str(self.guard))
        if self.effect:
            text_parts.append('/%s' % str(self.effect))
        return ' '.join(text_parts)

    def get_id_str(self):
        my_id = '%s->%s:' % (self.source.name, self.target.name)
        if self.trigger:
            my_id += str(self.trigger.event)
        if self.guard:
            my_id += '[' + str(self.guard) + ']'
        return my_id