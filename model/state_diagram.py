
from PySide6.QtCore import QEvent, Signal, Qt
from PySide6.QtGui import QKeySequence, QShortcut, QColor
from PySide6.QtWidgets import QToolButton, QLineEdit, QPushButton, QSizePolicy, QHBoxLayout, QLabel, QWidget, \
    QVBoxLayout, QStackedLayout

import numpy as np

from gui.controller import Controller
from gui.graphics_scene import GraphicsScene
from gui.graphics_view import GraphicsView
from model.default_placer import DefaultPlacer
from model.server_change_state import ServerChangeState
from state.state import State
from tools.cfg import CFG
from tools.circle_representation import update_representation

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
            # Get graphic vertex of the selected vertex
            vertex = self._scene.get_vertex_gi(selected[i])
            # Update position and dimension
            vertex.set_vertex_gi([position[1], position[2]], [all_dimension_x[i], all_dimension_y[i]], False)

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

            # Update background color If reset color when search mode
            if CFG.is_reset_color_search():
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

    def update(self):
        placer = DefaultPlacer()
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

        # If reset representation circle then update representation
        if CFG.is_reset_representation_circle():
            update_representation(sm, self._scene)

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

