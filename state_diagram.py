from PySide6.QtCore import QEvent
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QToolButton, QLineEdit, QPushButton, QSizePolicy, QHBoxLayout, QLabel, QWidget, \
    QVBoxLayout, QStackedLayout

from graphics_items import *
import socket
import threading
import numpy as np

AUTO_COLORS = (
                '#ffffcc',
                '#c0c0c0',
                '#e0e0e0',
                '#ffd0d0',
                '#d0ffd0',
                '#d0ffff',
                '#d0d0ff',
                '#ffd0ff',
              )



# Uniformization of all position x y
def uniform_all_position(position, index_x, index_y):
    # Get position x and y
    p_x = [a[index_x] for a in position]
    p_y = [a[index_y] for a in position]

    # Compute variance
    vx = np.var(p_x)
    vy = np.var(p_y)

    # If variance is greater in x than in y
    if vx > vy:
        # Inversion of parameter
        uniform_all_position(position, index_y, index_x)
    # If x is more aligned than y
    else:
        # Compute average in x
        ax = np.average(p_x)
        # For each element
        for i in range(0, len(p_x)):
            # Update current element
            position[i][index_x] = ax
        # If almost three elements
        if len(p_y) >= 3:
            # Sort all values from y value
            position.sort(key=lambda value: value[index_y])
            # Difference average for each element
            difference = position[len(position) - 1][index_y] - position[0][index_y]
            diff_between_two_vertices = difference / (len(position) - 1)
            # For each element
            for i in range(0, len(p_y)):
                # Update current element
                position[i][index_y] = position[0][index_y] + i * diff_between_two_vertices


# Uniformization of all values
def uniform_all_dimension(values):
    # Compute average
    av = np.average(values)
    # For each element
    for i in range(0, len(values)):
        # Update current element
        values[i] = av


class DefaultPlacer(object):
    """Standard Placer

    This class assigns positions to orphans vertices and transitions, i.e.
    items which have been described in the semantics editor but not yet placed
    manually by the user
    """

    def place_vertices(self, scene, orphan_vertices):
        if not orphan_vertices:  # don't waste our time if there's nothing to do
            return
        self._scene = scene
        self._orphan_vertices = orphan_vertices
        self.layout_region(scene.get_sm().region[0], QPointF(0, 0))

    def layout_region(self, region, from_point):
        """Resize/Move all orphan vertices from a region. from_point is the suggested location
           the vertices will be placed
        """
        vertices = region.subVertex

        # layout each vertex first
        for vertex in vertices:
            self.layout_vertex(vertex)

        # if this region contains already-placed & visible vertices, orphans are placed
        # to the right of the bounding rectangle containing these vertices
        brect = QRectF()
        nb_orphans = 0
        for vertex in vertices:
            if not vertex in self._orphan_vertices:
                vertex_gi = self._scene.get_vertex_gi(vertex.name)
                if vertex_gi.isVisible():
                    rect = vertex_gi.mapToParent(vertex_gi.boundingRect()).boundingRect()
                    brect |= rect
            else:
                nb_orphans += 1
        if not brect.isNull():
            from_point = brect.topRight() + QPointF(20, 0)

        # place orphan vertices in a matrix starting from from_point
        if nb_orphans:
            nb_col = math.floor(math.sqrt(nb_orphans))
            nb_row = math.ceil(nb_orphans / nb_col)
            from_top = from_point.y()
            y = 0
            max_width = 0
            for vertex in vertices:
                if vertex in self._orphan_vertices:
                    vertex_gi = self._scene.get_vertex_gi(vertex.name)
                    cur_tl = vertex_gi.mapToParent(vertex_gi._rect.topLeft())
                    dx = from_point.x() - cur_tl.x()
                    dy = from_point.y() - cur_tl.y()
                    vertex_gi.setPos(vertex_gi.x() + dx, vertex_gi.y() + dy)

                    max_width = max(max_width, vertex_gi._rect.width())
                    y += 1
                    if y < nb_row:
                        from_point += QPointF(0, vertex_gi._rect.height() + 30)
                    else:
                        y = 0
                        from_point = QPointF(from_point.x() + max_width + 30, from_top)

    def layout_vertex(self, vertex):
        """Place the sub-vertices of this vertex and resize the vertex to fit
           if this was an orphan vertex
        """
        vertex_gi = self._scene.get_vertex_gi(vertex.name)
        if isinstance(vertex, State) and vertex.isComposite():
            if vertex in self._orphan_vertices:
                # no fancy placement, the vertex will be resized to fit anyway
                from_point = QPointF(0, 0)
            else:
                # ask the vertex where the sub-vertices should be placed
                from_point = vertex_gi.hint_place_sub_vertices()
            self.layout_region(vertex.region[0], from_point)

        if vertex in self._orphan_vertices:
            vertex_gi.automatic_resize()

    def place_transition(self, trans_gi):
        if trans_gi.is_transition_to_self():
            # transition to self: 3 segments
            trans_gi._source_point = QPointF(0.25, 0.5)
            middle_point = QPointF(0.5, 1.5)
            trans_gi._target_point = QPointF(0.75, 0.5)
            abs_source = trans_gi.rel_to_abs_point(trans_gi._source_gi, trans_gi._source_point)
            abs_middle = trans_gi.rel_to_abs_point(trans_gi._source_gi, middle_point)
            abs_target = trans_gi.rel_to_abs_point(trans_gi._target_gi, trans_gi._target_point)
            trans_gi._rules = \
                [TransitionGItem.SegRule(TransitionGItem.VertSeg, abs_source),
                 TransitionGItem.SegRule(TransitionGItem.HorizSeg, abs_middle),
                 TransitionGItem.SegRule(TransitionGItem.VertSeg, abs_target)]
        elif trans_gi.is_local_transition():
            # local transition: from source border to target center
            trans_gi._source_point = QPointF(0, 0)
            trans_gi._target_point = QPointF(0.5, 0.5)
            abs_source = trans_gi.rel_to_abs_point(trans_gi._source_gi, trans_gi._source_point)
            abs_target = trans_gi.rel_to_abs_point(trans_gi._target_gi, trans_gi._target_point)
            trans_gi._rules = [TransitionGItem.SegRule(TransitionGItem.HorizSeg, abs_source)]
        else:
            # regular transition: from source center to target center
            trans_gi._source_point = QPointF(0.5, 0.5)
            trans_gi._target_point = QPointF(0.5, 0.5)
            abs_source = trans_gi.rel_to_abs_point(trans_gi._source_gi, trans_gi._source_point)
            abs_target = trans_gi.rel_to_abs_point(trans_gi._target_gi, trans_gi._target_point)
            trans_gi._rules = [TransitionGItem.SegRule(TransitionGItem.HorizSeg, abs_source)]
        trans_gi.rebuild_path(False)
        trans_gi.rebuild_rules(False)


class StateDiagram(QWidget):
    """State Diagram widget

    This is a stacked widget that contains two sub-widgets
    - the GraphicView state diagram itself
    - a read-only text widget that displays an error message when the semantic description is wrong

    """
    dirty = Signal()

    def CreateFindLayout(self):

        # Create two buttons find / combo box / button done
        self._find_prev_wg = QToolButton(arrowType=Qt.LeftArrow)
        self._find_next_wg = QToolButton(arrowType=Qt.RightArrow)
        self._find_combo_wg = QLineEdit()
        self._find_combo_wg.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
        self._find_done_wg = QPushButton('Done')

        # Search layout
        search_ly = QHBoxLayout()
        search_ly.setContentsMargins(0, 0, 0, 0)
        search_ly.setSpacing(0)
        search_ly.addStretch(0)
        search_ly.addWidget(QLabel('Find:'))
        search_ly.addSpacing(5)
        search_ly.addWidget(self._find_prev_wg)
        search_ly.addWidget(self._find_next_wg)
        search_ly.addSpacing(5)
        search_ly.addWidget(self._find_combo_wg)
        search_ly.addSpacing(5)
        search_ly.addWidget(self._find_done_wg)

        # return layout
        return search_ly

    def CreateSuperStateLayout(self):

        # Create combo box / button done
        self._superstate_combo_wg = QLineEdit()
        self._superstate_combo_wg.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
        self._superstate_valid_wg = QPushButton('Valid')
        self._superstate_cancel_wg = QPushButton('Cancel')

        # Superstate layout
        superstate_ly = QHBoxLayout()
        superstate_ly.setContentsMargins(0, 0, 0, 0)
        superstate_ly.setSpacing(0)
        superstate_ly.addStretch(0)
        superstate_ly.addWidget(QLabel('Name super state:'))
        superstate_ly.addSpacing(5)
        superstate_ly.addWidget(self._superstate_combo_wg)
        superstate_ly.addSpacing(5)
        superstate_ly.addWidget(self._superstate_valid_wg)
        superstate_ly.addSpacing(5)
        superstate_ly.addWidget(self._superstate_cancel_wg)

        # return layout
        return superstate_ly

    def __init__(self, parent):
        super(StateDiagram, self).__init__(parent)
        self._parent = parent

        # Raccourci Ctrl+A
        shortcut = QShortcut(QKeySequence("Ctrl+a"), self)
        shortcut.activated.connect(self.handle_ctrl_a)

        # Info widget
        self._info_wg = QLabel(alignment=Qt.AlignCenter, wordWrap=True)

        # View widget
        self._scene = GraphicsScene(self)
        self._view_wg = GraphicsView()
        self._view_wg.setScene(self._scene)
        self._scene.selectionChanged.connect(self.on_selection_changed)

        # Create widget search and add link widget <-> layout
        self._search_wg = QWidget()
        self._search_wg.setLayout(self.CreateFindLayout())

        # Create widget superstate and layout superstate and set to the layout into the widget
        self._superstate_wg = QWidget()
        self._superstate_wg.setLayout(self.CreateSuperStateLayout())

        # Add two widget on diagram : 1) search 2) super state 3) diagram view
        self._search_view_wd = QWidget()
        self._search_view_ly = QVBoxLayout(self._search_view_wd)
        self._search_view_ly.setContentsMargins(0, 0, 0, 0)
        self._search_view_ly.setSpacing(0)
        self._search_view_ly.addWidget(self._search_wg)
        self._search_view_ly.addWidget(self._superstate_wg)
        self._search_view_ly.addWidget(self._view_wg)

        # Main widget
        self._main_ly = QStackedLayout(self)
        self._main_ly.addWidget(self._info_wg)
        self._main_ly.addWidget(self._search_view_wd)
        self._search_wg.hide()
        self._superstate_wg.hide()

        # End of configuration
        self._scene.dirty.connect(self.dirty)
        self._serverChangeState = None
        self._currentState = None
        self._wnd = None
        self._nbMatch = 0
        self._iVertexMatch = 0

        # Connect button search
        self._find_prev_wg.clicked.connect(self.PreviousVertex)
        self._find_next_wg.clicked.connect(self.NextVertex)
        self._find_done_wg.clicked.connect(self.cmd_find_done)
        self._find_combo_wg.installEventFilter(self)

        # Connect button super state
        self._superstate_combo_wg.installEventFilter(self)
        self._superstate_valid_wg.clicked.connect(self.cmd_superstate_valid)
        self._superstate_cancel_wg.clicked.connect(self.cmd_superstate_cancel)

    def on_selection_changed(self):
        selected = self._scene.selectedItems()
        self._parent.set_status("Nb selected : " + str(len(selected)))

    def handle_ctrl_a(self):
        self.controller.select_all()

    def mousePressEvent(self, event=None):

        # Get vertices with info match or not match
        selected = self.controller.getVertexSelected()

        # If not empty
        if len(selected) > 0:
            # Update combo box
            self._parent.updateSelectedCombo(selected[0])

    def cmd_find_done(self):

        self._search_wg.hide()

    def InitFind(self):

        # Init find section for state diagram
        self._search_wg.show()
        self._find_combo_wg.setFocus(Qt.OtherFocusReason)
        self._find_combo_wg.selectAll()
        self.NextVertex()

    def align(self):
        # Get vertex selected
        selected = self.controller.getVertexSelected()
        all_position = []
        all_dimension_x = []
        all_dimension_y = []

        # For each vertex
        for i in range(0, len(selected)):
            # Get name of the selected vertex
            vertex = selected[i]
            # Get state graphic
            state_graphic = self._scene.get_vertex_gi(vertex)
            # Get rectangle from item graphic vertex
            rect = state_graphic._rect
            # Get position from item graphic vertex
            pos = state_graphic.pos()
            # Add current position
            all_position.append([i, pos.x(), pos.y()])
            # Add current dimension
            all_dimension_x.append(rect.width())
            all_dimension_y.append(rect.height())

        # Uniformization of all position x y
        uniform_all_position(all_position, index_x=1, index_y=2)
        # Uniformization of all dimension
        uniform_all_dimension(all_dimension_x)
        uniform_all_dimension(all_dimension_y)

        # For each position
        for position in all_position:
            # Get number position
            i = position[0]
            # Get name of the selected vertex
            vertex = selected[i]
            # Get state graphic
            state_graphic = self._scene.get_vertex_gi(vertex)
            # Get position from item graphic vertex
            pos = state_graphic.pos()
            # Update position
            pos.setX(position[1])
            pos.setY(position[2])
            state_graphic.setPos(pos)
            # Get rectangle from item graphic vertex
            state_graphic._rect.setX(0)
            state_graphic._rect.setY(0)
            state_graphic._rect.setWidth(all_dimension_x[i])
            state_graphic._rect.setHeight(all_dimension_y[i])

        # Refresh the graphic
        self.controller.unselect()
        self.refresh()

    def InitSuperState(self):

        # Init super state section for state diagram
        self._superstate_wg.show()
        self._superstate_combo_wg.setFocus(Qt.OtherFocusReason)
        self._superstate_combo_wg.selectAll()

    def cmd_superstate_valid(self):

        # Get vertices with info match or not match
        selected = self.controller.getVertexSelected()

        # Update file with new super state
        self._parent.rewrite_superstate(self._superstate_combo_wg.text(), selected)

        # Hide the super state
        self._superstate_wg.hide()

    def cmd_superstate_cancel(self):
        self._superstate_wg.hide()

    def NextVertex(self):
        if self._iVertexMatch < self._nbMatch:
            self._iVertexMatch = self._iVertexMatch + 1
        else:
            self._iVertexMatch = 0;

    def PreviousVertex(self):
        if self._iVertexMatch > 0:
            self._iVertexMatch = self._iVertexMatch - 1
        else:
            self._iVertexMatch = self._nbMatch - 1

    def eventFilter(self, object, event):

        # if the touch is released
        if event.type() == QEvent.KeyRelease:
            # if it's escape
            if event.key() == Qt.Key_Escape:
                if self._find_combo_wg == object:
                    self._search_wg.hide()
                    # if not control T
            elif self._superstate_wg.isHidden():
                # Colorise corresponding key
                self.ColorAllConcernedBlock()
            # if control T and Return
            elif event.key() == Qt.Key_Return:
                # Run rewrite super state
                self.cmd_superstate_valid()

            self.refresh()

        return super(QWidget, self).eventFilter(object, event)

    def ColorAllConcernedBlock(self):

        # Get vertices with info match or not match
        (vertices, self._nbMatch) = self.controller.getVertexName(self._find_combo_wg.text())

        # if nb match is not null
        if self._nbMatch > 0:
            # Current item vertex
            self._iVertexMatch = self._iVertexMatch % self._nbMatch
        else:
            # Current item vertex
            self._iVertexMatch = 0

        # Init vertex match
        iVertexMatch = 0

        # For each vertex
        for (match, name) in vertices:
            # Get gui vertex
            vertex_gi = self._scene.get_vertex_gi(name)

            # Compute color
            i = 0
            if match:
                # Color Selection
                i = int(len(AUTO_COLORS) / 2)

                # If match and it's the good occurence
                if iVertexMatch == self._iVertexMatch:
                    self._view_wg.centerOn(vertex_gi.x(), vertex_gi.y())

                # Go to the next vertex
                iVertexMatch = iVertexMatch + 1

            else:
                i = 0

            # Update color
            vertex_gi.background_color = QColor(AUTO_COLORS[i])

        # Refresh vertices
        self.refresh()

    def __exit__(self, type, value, traceback):
        print("exit")

    def updateServerChangeState(self):
        if self._serverChangeState == None:
            if self._sm._port != -1:
                self._serverChangeState = ServerChangeState(self, self._sm._port)

    def setWnd(self, wnd):
        self._wnd = wnd

    def update(self, placer=DefaultPlacer()):
        sm = self._parent.compile()
        if sm:
            self._sm = sm
            self.controller = Controller(self._scene)
            self.controller.load_sm(self._sm, placer)
            self.updateServerChangeState()
            self._main_ly.setCurrentWidget(self._search_view_wd)
            self._scene.setSceneRect(self._scene.itemsBoundingRect())
        else:
            self._main_ly.setCurrentWidget(self._info_wg)
            self._info_wg.setText('The semantics description '
                                  'contains some errors which must be fixed '
                                  'before the diagram can be displayed')

    def zoom_100(self):
        self._view_wg.resetTransform()

    def refresh(self):
        self._view_wg.scale(0.5, 0.5)
        self._view_wg.scale(2, 2)

    def zoom_in(self):
        self._view_wg.scale(1.25, 1.25)

    def zoom_out(self):
        self._view_wg.scale(0.75, 0.75)

    def reset(self):
        self._scene.reset()

    def auto_colorize(self):
        def do_region(region, col_index):
            for vertex in region.subVertex:
                vertex_gi = self._scene.get_vertex_gi(vertex.name)
                vertex_gi.background_color = QColor(AUTO_COLORS[col_index])
                sub_col = (col_index + 1) % len(AUTO_COLORS)
                if isinstance(vertex, State) and vertex.isComposite():
                    do_region(vertex.region[0], sub_col)

        do_region(self._sm.region[0], 0)


def listenClientChangeState(smd, port):
    Sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # l'ip locale de l'ordinateur
    Host = '127.0.0.1'
    # choix d'un port
    Port = port

    # on bind notre socket
    Sock.bind((Host, Port))
    # On est a l'ecoute d'une seule et unique connexion :
    Sock.listen(1)

    while 1:

        # Le script se stoppe ici jusqu'a ce qu'il y ait connexion :
        client, adresse = Sock.accept()  # accepte les connexions de l'exterieur
        print("L'adresse", adresse, "vient de se connecter au serveur !")

        while 1:
            received = client.recv(1)
            if (len(received) == 0):
                break

            nbBitRead = ord(received)

            if nbBitRead == 0:
                print("end connection requested")
                break

            # on revoit n caracteres
            message = client.recv(nbBitRead)
            # si on ne recoit plus rien
            if not message:
                # on break la boucle (sinon les bips vont se repeter)
                break
            # affiche les donnees envoyees, suivi d'un bip sonore
            print("Entry into ", message)

            # Set message into State Machine Diagram
            smd._currentState = message
            # Refresh window
            smd._wnd.cmd_refresh()

        # ferme la connexion avec le client
        client.close()

        if nbBitRead == 0:
            print("end connection now")
            break


class ServerChangeStateThread(threading.Thread):
    def __init__(self, smd, port):
        threading.Thread.__init__(self)
        self._smd = smd
        self._port = port

    def run(self):
        print("Starting listenClientChangeState")
        listenClientChangeState(self._smd, self._port)
        print("End listenClientChangeState")


class ServerChangeState(object):
    def __init__(self, smd, port):
        a = ServerChangeStateThread(smd, port)
        a.start()


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
