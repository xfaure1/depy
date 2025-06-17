from uml_state_machine import *

class SmsWriter(object):
    def __init__(self, file, tab_width):
        self._file = file
        self._tabs = ' ' * tab_width

    def write(self, sm):
        self._sm = sm
        for vertex in self.sort_vertices(self._sm.region[0].subVertex):
            self.write_vertex(vertex, 1)

    def write_vertex(self, vertex, level):
        tabs = self._tabs * (level-1)

        if isinstance(vertex, State):
            # write state header
            lev_sep = '=' * level
            if self.is_initial(vertex):
                initial = '*'
            else:
                initial = ''
            self._file.write('%s%s %s%s %s\n' %
                (tabs, lev_sep, vertex.name, initial, lev_sep))

            # write comments
            doc = getattr(vertex, 'documentation', None)
            if doc:
                lns = ['%s#%s' % (tabs, l) for l in doc.splitlines()]
                self._file.write('\n'.join(lns))
                self._file.write('\n')

            # write entry action
            entry = self.gen_action(vertex.entry)
            if entry:
                self._file.write('%sentry%s\n' % (tabs, entry))

            # write exit action
            exit = self.gen_action(vertex.exit)
            if exit:
                self._file.write('%sexit%s\n' % (tabs, exit))

            # write outgoing transitions
            for trans in vertex.outgoing():
                if trans.trigger and trans.trigger.event:
                    trigger = trans.trigger.event
                else:
                    trigger = ''
                if trans.guard and trans.guard.specification:
                    guard = '[%s]' % trans.guard.specification
                else:
                    guard = ''
                effect = self.gen_action(trans.effect)
                if trans.kind == TransitionKind.internal:
                    target = ''
                else:
                    target = ' ->%s' % trans.target
                self._file.write('%s%s%s%s%s\n' %
                    (tabs, trigger, guard, effect, target))

            self._file.write('\n')

            if vertex.isComposite():
                for sub in self.sort_vertices(vertex.region[0].subVertex):
                    self.write_vertex(sub, level+1)

    def sort_vertices(self, vertices):
        # move initial state in first position
        result = []
        for sub in vertices:
            if self.is_initial(sub):
                result.insert(0, sub)
            else:
                result.append(sub)
        return result

    def is_initial(self, vertex):
        for trans in vertex.incoming():
            if isinstance(trans.source, PseudoState) and \
               trans.source.kind == PseudoStateKind.initial:
                   return True
        return False

    def gen_action(self, behaviour):
        if behaviour:
            action = ' /%s' % behaviour.action
            if behaviour.check:
                action += '^%s' % behaviour.check
            return action
        return ''

