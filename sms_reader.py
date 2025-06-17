"""

Build a StateMachine from a text description

"""
from constant_value import PSEUDO_STATE_INITIAL
from state.constraint import Constraint
from state.my_behaviour import MyBehavior
from state.my_event import MyEvent
from state.my_time_event import MyTimeEvent
from model.line_parser import LineParser
from state.trigger import Trigger


class StateMachineBuilder(object):
    def __init__(self, sm, extra_parser=None):
        self._sm = sm
        self._state_stack = []
        self._def_lines = {}
        self._extra_parser = extra_parser

    ALL_PARSERS = ()

    def check_line_syntax(cls, line):
        for parser in cls.ALL_PARSERS:
            match_res = parser.reg_exp.match(line)
            if match_res != None:
                return (parser.kind, match_res)
        return ('error', None)
    check_line_syntax = classmethod(check_line_syntax)


    def build_from_file(self, filename):
        """Build a state machine by reading from a text file"""
        smfile = open(filename, "r")
        smlines = smfile.readlines()
        smfile.close()
        return self._build(smlines)

    def build_from_string(self, string):
        """Build a state machine by reading from a string"""
        smlines = string.splitlines()
        return self._build(smlines)

    def get_errors(self):
        """Return the errors detect while building a state machine

        The result is returned as as list of
        (line, (col_begin, col_end), description)

        """
        return self._errors

    def get_passn(self):
        return self._passn

    def get_def_line(self, obj):
        return self._def_lines.get(obj, 0)

    def get_current_state(self):
        return self._state_stack[-1]

    def _build(self, smlines):
        self._errors = []
        self._all_states = {}
        self._all_actions = set()
        self._all_events = set()
        self._all_guards = set()
        self._port = -1

        for self._passn in range(0,2):
            self._state_stack = [''] # stack of state names
            self._line_nb = 1
            for line in smlines:
                for parser in self.ALL_PARSERS:
                    match_res = parser.reg_exp.match(line)
                    if match_res != None:
                        parser.pass_handlers[self._passn](self, match_res)
                        if self._extra_parser and match_res.group('comment'):
                            err = self._extra_parser.parse(self,
                                                    match_res.group('comment'))
                            if (err):
                                self._append_error(err, match_res.span(0))
                        break
                self._line_nb += 1

        return not self._errors

    def _append_error(self, description, columns):
        self._errors.append((self._line_nb, columns, description))

    def _get_current_state(self):
        return self._state_stack[-1]

    def _passX_nop(self, match_res):
        return None

    def _pass1_error(self, match_res):
        self._append_error('syntax error', match_res.span('error'))

    def _pass1_state(self, match_res):
        name = match_res.group('name')
        initial = match_res.group('initial')
        level = len(match_res.group('level'))
        current_level = len(self._state_stack) - 1
        if level > current_level + 1:
            self._append_error('invalid state nesting', match_res.span('statedef'))
        if self._sm.has_state(name):
            self._append_error('state "%s" already defined' % name, match_res.span('name'))
            return
        self._state_stack = self._state_stack[0 : level]
        parent_state = self._get_current_state()
        obj = self._sm.add_state(name, parent_state + '|')
        self._def_lines[obj] = self._line_nb
        self._state_stack.append(name)
        if initial:
            initial_name = parent_state + '::$I'
            if self._sm.has_state(initial_name):
                # multiple initial states in root region allowed
                if parent_state != '':
                    self._append_error('initial state inside %s already defined' %
                                        parent_state, match_res.span(0))
                return
            obj = self._sm.add_pseudo_state(initial_name, PSEUDO_STATE_INITIAL, parent_state + '|')
            self._def_lines[obj] = self._line_nb

    def _pass2_state(self, match_res):
        name = match_res.group('name')
        initial = match_res.group('initial')
        level = len(match_res.group('level'))
        current_level = len(self._state_stack)
        self._state_stack = self._state_stack[0 : level]
        parent_state = self._get_current_state()
        self._state_stack.append(name)
        self._all_states[name] = name
        if initial:
            trigger = None
            guard_cons = None
            effect = None
            obj = self._sm.add_transition(parent_state + '::$I', name, trigger, guard_cons, effect)
            self._def_lines[obj] = self._line_nb

    def _pass1_initial(self, match_res):
        initial_name = self._get_current_state() + '::$I'
        if self._sm.has_state(initial_name):
            self._append_error('initial state already defined', match_res.span(0))
            return
        obj = self._sm.add_pseudo_state(initial_name, PSEUDO_STATE_INITIAL, self._get_current_state() + '|')
        self._def_lines[obj] = self._line_nb

    def _pass2_initial(self, match_res):
        target = match_res.group('target')
        trigger = None
        guard_cons = None
        effect = None
        if not self._sm.has_state(target):
            self._append_error('state "%s" not defined' % target, match_res.span('target'))
            return
        obj = self._sm.add_transition(self._get_current_state() + '::$I', target, trigger, guard_cons, effect)
        self._def_lines[obj] = self._line_nb

    def _pass2_entry(self, match_res):
        action = match_res.group('action')
        check = match_res.group('check')
        if self._get_current_state():
            context = { 'source' : self._get_current_state(), 'event' : 'entry' }
            behaviour = MyBehavior(action, check, context)
            self._sm.add_entry_action(self._get_current_state(), behaviour)
            if action:
                self._all_actions.add(behaviour.fmt_action())

    def _pass2_exit(self, match_res):
        action = match_res.group('action')
        if self._get_current_state():
            context = { 'source' : self._get_current_state(), 'event' : 'exit' }
            behaviour = MyBehavior(action, None, context)
            self._sm.add_exit_action(self._get_current_state(), behaviour)
            if action:
                self._all_actions.add( behaviour.fmt_action() )

    def _pass2_event(self, match_res):
        event =  match_res.group('event')
        guard =  match_res.group('guard')
        action =  match_res.group('action')
        check =  match_res.group('check')

        if event:
            if 'timeout' in match_res.groupdict():
                timeout =  match_res.group('timeout')
                trigger = Trigger(MyTimeEvent(timeout))
            else:
                trigger = Trigger(MyEvent(event))
        else:
            trigger = Trigger(MyEvent('')) # implicit event
        event_id = trigger.event.id()
        if guard:
            guard_cons = Constraint(guard)
        else:
            guard_cons = None
        context = { 'source' : self._get_current_state(),
                    'target' : self._get_current_state(),
                    'event' : event_id,
                    'guard' : guard }
        effect = MyBehavior(action, check, context)
        if self._get_current_state():
            obj = self._sm.add_event(self._get_current_state(), trigger, guard_cons, effect)
            self._def_lines[obj] = self._line_nb
            if trigger:
                self._all_events.add(trigger.event)
            if guard:
                self._all_guards.add(guard)
            if action:
                self._all_actions.add(effect.fmt_action())

    def _pass2_transition(self, match_res):
        target =  match_res.group('target')
        event =  match_res.group('event')
        guard =  match_res.group('guard')
        action =  match_res.group('action')
        check =  False

        if event:
            if 'timeout' in match_res.groupdict():
                timeout =  match_res.group('timeout')
                trigger = Trigger(MyTimeEvent(timeout))
            else:
                trigger = Trigger(MyEvent(event))
        else:
            trigger = Trigger(MyEvent('')) # implicit event
        event_id = trigger.event.id()
        if guard:
            guard_cons = Constraint(guard)
        else:
            guard_cons = None
        if action or check:
            context = { 'source' : self._get_current_state(),
                        'target' : target,
                        'event' : event_id,
                        'guard' : guard }
            effect = MyBehavior(action, check, context)
        else:
            effect = None

        if not self._sm.has_state(target):
            self._append_error('state "%s" not defined' % target, match_res.span('target'))
            return

        if self._get_current_state():
            obj = self._sm.add_transition(self._get_current_state(), target, trigger, guard_cons, effect)
            self._def_lines[obj] = self._line_nb
            if trigger:
                self._all_events.add(trigger.event)
            if guard:
                self._all_guards.add(guard)
            if action:
                self._all_actions.add(effect.fmt_action())

    def _pass2_port(self, match_res):
        self._port = int(match_res.group('port'))

    def _pass2_note(self, match_res):
        note =  match_res.group('note')
        if self._get_current_state():
            cur_state = self._sm.get_state(self.get_current_state())
            cur_state.note += note
            cur_state.note += '\n'

    ALL_PARSERS = (
            LineParser(r'\s*(?P<statedef>(?P<level>=+)\s*(?P<name>\w+)(?P<initial>\*)?\s*(?P=level))\s*(?P<comment>#.*)?$',
                       _pass1_state, _pass2_state, 'state'),
            LineParser(r'\s*(?P<source>\$I)\s*->\s*(?P<target>\w+)\s*(?P<comment>#.*)?$',
                       _pass1_initial, _pass2_initial, 'initial'),
            LineParser(r'\s*(?P<keyword>entry)\s*/\s*((?P<action>[^\s]+)\s*)?(\^\s*(?P<check>check|c)\s*)?(?P<comment>#.*)?$',
                       _passX_nop, _pass2_entry, 'entry'),
            LineParser(r'\s*(?P<keyword>exit)\s*/\s*(?P<action>[^\s]+)\s*(?P<comment>#.*)?$',
                       _passX_nop, _pass2_exit, 'exit'),
            LineParser(r'\s*(?P<event>(?!(exit|entry|do)\s)\w+)\s*(\[\s*(?P<guard>!?[^\]]+)\s*\]\s*)?\/\s*(\s*(?P<action>[^\s]+)\s*)?(\^\s*(?P<check>check|c)\s*)?(?P<comment>#.*)?$',
                       _passX_nop,_pass2_event, 'event'),
            LineParser(r'\s*((?P<event>(?!(exit|entry|do)\s)\w+)\s*)?(\[\s*(?P<guard>!?[^\]]+)\s*\]\s*)?(\/\s*(?P<action>[^\s]+)\s*)?\s*->\s*(?P<target>\w+)\s*(?P<comment>#.*)?$',
                       _passX_nop, _pass2_transition, 'transition'),
            LineParser(r'\s*(?P<event>(?!(exit|entry|do)\s)after\s*\(\s*(?P<timeout>\w+)\s*\)\s*)\s*(\[\s*(?P<guard>!?[^\]]+)\s*\]\s*)?\/\s*(\s*(?P<action>[^\s]+)\s*)?(\^\s*(?P<check>check|c)\s*)?(?P<comment>#.*)?$',
                       _passX_nop,_pass2_event, 'event'),
            LineParser(r'\s*((?P<event>(?!(exit|entry|do)\s)after\s*\(\s*(?P<timeout>\w+)\s*\)\s*)\s*)?(\[\s*(?P<guard>!?[^\]]+)\s*\]\s*)?(\/\s*(?P<action>[^\s]+)\s*)?\s*->\s*(?P<target>\w+)\s*(?P<comment>#.*)?$',
                       _passX_nop, _pass2_transition, 'transition'),
            LineParser(r'\s*(?P<comment>#port=(?P<port>.+))$', _passX_nop, _pass2_port, 'port'),
            LineParser(r'\s*(?P<comment>##(?P<note>.+))$', _passX_nop, _pass2_note, 'note'),
            LineParser(r'\s*(?P<comment>#.*)?$', _passX_nop, _passX_nop, 'comment'),
            LineParser(r'\s*(?P<error>.+?)\s*(?P<comment>#.*)?$', _pass1_error, _passX_nop, 'error'),
            )
