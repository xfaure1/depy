from gui.pseudo_state_gitem import PseudoStateGItem
from gui.state_gitem import StateGItem
from gui.transition_gitem import TransitionGItem
from uml_state_machine import State, TransitionKind, Transition_Id, PseudoState


class Controller(object):
    """Load a state machine into the diagram

    This class purpose is to manipulate the diagram according to changes in the
    semantic description

    TODO: the current architecture is upside-down: the Diagram creates the Controller
    This should be reversed

    """

    def __init__(self, scene):
        self._scene = scene
        self._sm_vertices = {}  # id:vertex
        self._sm_transitions = {}  # id:transition

    def _load_regions(self, regions):
        for vertex in regions[0].subVertex:
            self._sm_vertices[vertex.name] = vertex
            if isinstance(vertex, State) and vertex.isComposite():
                self._load_regions(vertex.region)

        for transition in regions[0].transition:
            if transition.kind != TransitionKind.internal:
                trans_id = Transition_Id(transition)
                self._sm_transitions[trans_id] = transition

    def getVertexName(self, text):

        # Upper case string
        search = text.upper()
        vertices = []
        nbMatch = 0

        # For each vertex item
        for (vertex_id, vertex) in self._sm_vertices.items():
            vertices.append((search in vertex.name.upper(), vertex.name))
            if search in vertex.name.upper():
                nbMatch = nbMatch + 1

        # Return list of vertices
        return (vertices, nbMatch)

    def getVertexSelected(self):

        # Selected
        selected = []
        # For each vertex item
        for (vertex_id, vertex) in self._sm_vertices.items():
            vertex_gi = self._scene.get_vertex_gi(vertex.name)
            if vertex_gi.isSelected():
                selected.append(vertex.name)

        # Return all selected vertex
        return selected

    def unselect(self):
        # For each vertex item
        for (vertex_id, vertex) in self._sm_vertices.items():
            vertex_gi = self._scene.get_vertex_gi(vertex.name)
            if vertex_gi.isSelected():
                vertex_gi.setSelected(False)

    def select_all(self):
        # For each vertex item
        for (vertex_id, vertex) in self._sm_vertices.items():
            vertex_gi = self._scene.get_vertex_gi(vertex.name)
            vertex_gi.setSelected(True)

    def load_sm(self, sm, placer):
        self._sm = sm
        self._sm_vertices = {}
        self._scene.set_sm(sm)
        if self._sm.region:
            self._load_regions(self._sm.region)

        # Detach their model from all vertices and transitions items and remove them from the scene
        for trans_gi in self._scene._transitions_gi.values():
            trans_gi.set_model(None, None, None)
            if trans_gi.scene():
                self._scene.removeItem(trans_gi)
        for vertex_gi in self._scene._vertices_gi.values():
            vertex_gi.set_model(None)
            if vertex_gi.scene():
                self._scene.removeItem(vertex_gi)
            elif vertex_gi.parentItem():
                vertex_gi.setParentItem(None)

        # Assign its model to each vertex item
        orphan_vertices = []
        for (vertex_id, vertex) in self._sm_vertices.items():
            vertex_gi = self._scene.get_vertex_gi(vertex.name)
            if vertex_gi:
                vertex_gi.set_model(vertex)
            else:
                orphan_vertices.append((vertex_id, vertex))

        # Create orphan vertices
        for (vertex_id, vertex) in orphan_vertices:
            # self._scene.add_vertex_gi(vertex.name, vertex_gi)
            if isinstance(vertex, State):
                vertex_gi = StateGItem()
            elif isinstance(vertex, PseudoState):
                vertex_gi = PseudoStateGItem()
            else:
                raise 'oula'
            vertex_gi.set_model(vertex)
            self._scene.add_vertex_gi(vertex_id, vertex_gi)

        # Remove vertices no longer in model
        orphan_vertex_gi_ids = [(vertex_id, vertex_gi) for (vertex_id, vertex_gi) in self._scene._vertices_gi.items() if
                                vertex_gi._model is None]

        for (vertex_id, vertex_gi) in orphan_vertex_gi_ids:
            self._scene.del_vertex_gi(vertex_id)

        # Build vertex items hierarchy according to the model
        for vertex_id, vertex in self._sm_vertices.items():
            vertex_gi = self._scene.get_vertex_gi(vertex.name)
            if vertex.container.state:
                parent_state = vertex.container.state
                parent_state_gi = self._scene.get_vertex_gi(parent_state.name)
                vertex_gi.setParentItem(parent_state_gi)
            else:
                self._scene.addItem(vertex_gi)

        # Place orphan vertices
        placer.place_vertices(self._scene, [vx for (vxid, vx) in orphan_vertices])

        # Assign its model to each transition
        orphans_transitions = []
        for (trans_id, trans) in self._sm_transitions.items():
            trans_gi = self._scene.get_transition_gi(trans_id)
            if trans_gi:
                src_gi = self._scene.get_vertex_gi(trans.source.name)
                tgt_gi = self._scene.get_vertex_gi(trans.target.name)
                trans_gi.set_model(trans, src_gi, tgt_gi)
                parent_state = trans.container.state
                if parent_state:
                    parent_state_gi = self._scene.get_vertex_gi(parent_state.name)
                    trans_gi.setParentItem(parent_state_gi)
                else:
                    self._scene.addItem(trans_gi)
                trans_gi.rebuild_path(False)
                trans_gi.rebuild_rules(False)
            else:
                orphans_transitions.append((trans_id, trans))

        # Create and place orphan transitions
        for (trans_id, trans) in orphans_transitions:
            trans_gi = TransitionGItem()
            source_gi = self._scene.get_vertex_gi(trans.source.name)
            target_gi = self._scene.get_vertex_gi(trans.target.name)
            trans_gi.set_model(trans, source_gi, target_gi)
            self._scene.add_transition_gi(trans_id, trans_gi)
            parent_state = trans.container.state
            if parent_state:
                parent_state_gi = self._scene.get_vertex_gi(parent_state.name)
                trans_gi.setParentItem(parent_state_gi)
            else:
                self._scene.addItem(trans_gi)
            placer.place_transition(trans_gi)

        # Remove transitions no longer in model
        orphan_trans_gi_ids = [(trans_id, trans_gi) for (trans_id, trans_gi) in self._scene._transitions_gi.items() if
                               trans_gi._model is None]

        for (trans_id, trans_gi) in orphan_trans_gi_ids:
            self._scene.del_transition_gi(trans_id)

        # Update vertices visibility
        for vertex_id, vertex in self._sm_vertices.items():
            vertex_gi = self._scene.get_vertex_gi(vertex.name)
            vertex_gi.update_visibility()
        for (trans_id, trans) in self._sm_transitions.items():
            trans_gi = self._scene.get_transition_gi(trans_id)
            trans_gi.update_visibility()
