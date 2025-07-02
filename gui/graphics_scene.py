from PySide6.QtCore import Signal
from PySide6.QtWidgets import QGraphicsScene

from gui.graphics_view import getMapping
from gui.transition_gitem import TransitionGItem
from state.transition_kind import TransitionKind


class GraphicsScene(QGraphicsScene):
    dirty = Signal()

    def __init__(self, parent):
        super(GraphicsScene, self).__init__(parent)
        self._parent = parent
        self._vertices_gi = {}
        self._transitions_gi = {}
        self._moving_vertex_gi = None
        self._moving_vertex_transitions = []
        self._dirty = False

    def reset(self):
        self.clear()
        self._sm = None
        self._vertices_gi = {}
        self._transitions_gi = {}
        self._moving_vertex_gi = None
        self._moving_vertex_transitions = []

    def set_sm(self, sm):
        self._sm = sm

    def get_sm(self):
        return self._sm

    def clear_dirty(self):
        self._dirty = False

    def set_dirty(self):
        if not self._dirty:
            self._dirty = True
            self.dirty.emit()

    def add_vertex_gi(self, id, gi):
        self._vertices_gi[id] = gi

    def del_vertex_gi(self, id):
        del self._vertices_gi[id]

    def get_vertex_gi(self, id):
        return self._vertices_gi.get(id)

    def add_transition_gi(self, id, gi):
        self._transitions_gi[id] = gi

    def del_transition_gi(self, id):
        del self._transitions_gi[id]

    def get_transition_gi(self, id):
        return self._transitions_gi.get(id)

    def is_sub_vertex(self, candidate, parent):
        if candidate is parent:
            return True
        elif candidate.container.state:
            return self.is_sub_vertex(candidate.container.state, parent)
        else:
            return False

    def collect_transitions(self, container, vertex, collected):
        # collect all transitions of this region
        for trans in container.transition:
            if trans.kind is not TransitionKind.internal:
                if self.is_sub_vertex(trans.source, vertex):
                    endpoint = trans.source
                elif self.is_sub_vertex(trans.target, vertex):
                    endpoint = trans.target
                else:
                    endpoint = None
                if endpoint:
                    trans_gi = self.get_transition_gi(trans.get_id_str())
                    if trans_gi:  # no append when transition gi are not yet created
                        collected.append((trans_gi, endpoint))

        # collect transitions for parent regions
        if container.state:
            self.collect_transitions(container.state.container, vertex, collected)

    # The position of state is updated
    # So we have to update transition
    def vertex_position_change(self, vertex_gi):
        # If the moving vertex is not the current vertex
        if self._moving_vertex_gi is not vertex_gi:
            # if previous vertex movement is done, update the transitions rules
            if vertex_gi is None:
                # For each transition-vertex
                for (transition_gi, mvertex) in self._moving_vertex_transitions:
                    transition_gi.rebuild_rules(False)

            # a new vertex is moving: collect all transitions whose source/target state
            # is vertex_gi or a child of vertex_gi
            self._moving_vertex_transitions = []
            if vertex_gi is not None:
                vertex = vertex_gi._model
                self.collect_transitions(vertex.container, vertex, self._moving_vertex_transitions)

            self._moving_vertex_gi = vertex_gi

        # redraw the transitions linked to the currently moving vertex
        for (transition_gi, mvertex) in self._moving_vertex_transitions:
            if transition_gi:
                transition_gi.vertex_changed(mvertex)

    def vertex_size_has_changed(self, vertex_gi):
        vertex = vertex_gi._model
        # redraw the transitions linked to the currently changing vertex
        for gitem in self.items():
            if type(gitem) is TransitionGItem:
                trans = gitem._model
                if trans.source is vertex or trans.target is vertex:
                    gitem.vertex_changed(vertex)

    def align(self):

        # Init set x and set y
        setX = set()
        setY = set()

        # for each transition
        for key in self._transitions_gi:
            # Get current transition
            transition = self._transitions_gi[key]
            # For each rules
            for r in transition._rules:
                # Get the current anchor
                setX.add(r._anchor.x())
                setY.add(r._anchor.y())

        # Get mapping for x and y
        mappingX = getMapping(sorted(setX))
        mappingY = getMapping(sorted(setY))

        # for each transition
        for key in self._transitions_gi:
            # Get current transition
            transition = self._transitions_gi[key]
            # For each rules
            for r in transition._rules:
                # Set the new anchor
                r._anchor.setX(mappingX[r._anchor.x()])
                r._anchor.setY(mappingY[r._anchor.y()])

            # Rebuild path
            transition.rebuild_path(False)

    def removeSelected(self):

        # For each vertex
        for key in self._vertices_gi:
            # Get the current vertex
            vertex = self._vertices_gi[key]
            # If selected
            if vertex.isSelected():
                # Remove from the diagram
                vertex.remove_from_diagram()

    def mousePressEvent(self, event):
        self.align()
        super(GraphicsScene, self).mousePressEvent(event)
        self._parent.mousePressEvent()

    def get_vertices(self):
        return self._vertices_gi



