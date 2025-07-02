import re

from PySide6.QtCore import QFile, QIODevice

from state.pseudo_state import PseudoState
from state.region import Region
from state.state import State
from state.transition import Transition
from state.transition_kind import TransitionKind


class StateMachine(object):
    def __init__(self):
        self.submachineState = None
        self.connectionPoint = []
        self.region = []
        self._all_vertices = {}
        self._all_regions = {}  # referenced by their full name: State|Region
        self._re_regname = re.compile(r'(?P<state>\w+)?|(?P<region>\w+)?')

    def _region_stack(self, region):
        # print '_region_stack(%s)' % str(region)
        stack = [region]
        while region.state:
            container = region.state.container
            stack.append(container)
            region = container
        return stack

    def _ancestor_region(self, state1, state2):
        stack1 = self._region_stack(state1.container)
        stack2 = self._region_stack(state2.container)
        # for i in stack1: print ' 1: %s' % i
        # for i in stack2: print ' 2: %s' % i
        while stack1 and stack2 and stack1[-1] == stack2[-1]:
            ancestor = stack1[-1]
            stack1.pop()
            stack2.pop()
        # print '  ancestor %s' % ancestor
        return ancestor

    def _retrieve_region(self, region_name):
        """
        region_name 'State|Region'  or 'State|' for State's unique region,
        or '|Region' '|' for the state machine region
        """
        # find/create the region
        if region_name in self._all_regions:
            region = self._all_regions[region_name]
            # print '  region found'
        else:
            res = self._re_regname.match(region_name)
            reg_state = res.group('state')
            reg_region = res.group('region')
            if not reg_region: reg_region = ''
            if reg_state:
                # add the region to the parent state
                parent_state = self._all_vertices[reg_state]
                region = Region(reg_region, parent_state)
                parent_state.region.append(region)
            else:
                # add the region to the StateMachine
                region = Region(reg_region, None)
                region.stateMachine = self
                self.region.append(region)
            self._all_regions[region_name] = region
            # print '  create region "%s" in state %s' % (region.name, p_state.name)
        return region

    def add_state(self, name, region_name):
        """
        region_name -- 'State|Region' or 'State|' for the State's unique region
                        or '|Region' '|' for the SM's region
        """
        # print 'add_state "%s" to region "%s"' % (name, region_name)

        region = self._retrieve_region(region_name)
        state = State(name, region)
        region.subVertex.append(state)

        self._all_vertices[name] = state
        return state

    def add_pseudo_state(self, name, kind, region_name):
        region = self._retrieve_region(region_name)
        state = PseudoState(name, kind, region)
        region.subVertex.append(state)
        self._all_vertices[name] = state
        # print 'add_pseudo_state "%s" to region "%s"' % (name, region_name)
        return state

    def add_entry_action(self, state_name, behavior):
        # print 'add action %s to state %s' % (str(behavior), state_name)
        state = self._all_vertices[state_name]
        state.entry = behavior

    def add_exit_action(self, state_name, behavior):
        state = self._all_vertices[state_name]
        state.exit = behavior

    def add_event(self, state_name, trigger, guard, effect):
        """Add an internal transition to the state machine

        trigger -- Trigger
        guard -- Constraint
        effect -- Behavior
        """
        state = self._all_vertices[state_name]
        container = state.container
        transition = Transition(TransitionKind.internal, container, state,
                                state, trigger, guard, effect)
        container.transition.append(transition)
        # print "add internal transition from %s on %s in region %s" % (state_name, trigger.event.name, container)
        return transition

    def add_transition(self, from_name, to_name, trigger, guard, effect):
        """Add an external or local transition to the state machine

        trigger -- Trigger
        guard -- Constraint
        effect -- Behavior
        """
        from_state = self._all_vertices[from_name]
        to_state = self._all_vertices[to_name]
        container = self._ancestor_region(from_state, to_state)

        # Detect external vs local transitions
        to_cont = to_state.container
        external = True
        while to_cont.state:
            if to_cont.state is from_state:
                external = False
                container = to_cont
                break
            to_cont = to_cont.state.container

        if external:
            transition = Transition(TransitionKind.external, container,
                                    from_state, to_state,
                                    trigger, guard, effect)
            # print 'add external transition from %s to %s in region %s' % (from_name, to_name, container)
        else:
            transition = Transition(TransitionKind.local, container,
                                    from_state, to_state,
                                    trigger, guard, effect)
            # print 'add local transition from %s to %s in region %s' % (from_name, to_name, container)
        container.transition.append(transition)
        return transition

    def get_state(self, state_name):
        return self._all_vertices[state_name]

    def has_state(self, state_name):
        return state_name in self._all_vertices

    def get_all_vertices(self):
        return self._all_vertices

    def Print(self):

        # for each node
        for v in self._all_vertices:
            # Write name
            self._all_vertices[v].Print()

    def save_state_machine(self, filename):

        # Write all lines
        sms_file = QFile(filename)
        sms_file.open(QIODevice.WriteOnly)

        # for each node
        for v_key in self._all_vertices:

            # Get vertex
            v = self._all_vertices[v_key]

            # If region is not empty
            if len(v.region) > 0:

                # Write state root
                sms_file.write("=" + v.name + "=" + '\n')

            else:

                # Write sub state
                sms_file.write("==" + v.name + "==" + '\n')

                # For each transition outgoing
                for t in v.outgoing():
                    # Write transition outgoing
                    sms_file.write("->" + str(t.target) + '\n')

    def get_simple_graph(self):

        # Init map
        map_graph = {}
        # for each node
        for v_key in self._all_vertices:

            # Get vertex
            v = self._all_vertices[v_key]
            # For each transition outgoing
            for t in v.outgoing():
                if v_key in map_graph.keys():
                    map_graph[v_key].append(t.target.name)
                else:
                    map_graph[v_key] = [t.target.name]

        # Return simple graph
        return map_graph
