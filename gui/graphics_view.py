import functools

from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QGraphicsView, QMenu


class GraphicsView(QGraphicsView):

    def __init__(self, parent=None):
        super(GraphicsView, self).__init__(parent)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.TextAntialiasing)

    def wheelEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            factor = 1.41 ** (-event.angleDelta().y() / 240.0)
            self.scale(factor, factor)
        else:
            QGraphicsView.wheelEvent(self, event)

    def contextMenuEvent(self, event):
        super(GraphicsView, self).contextMenuEvent(event)
        if not event.isAccepted():
            excluded = []
            for v in self.scene().get_sm().region[0].subVertex:
                v_gi = self.scene().get_vertex_gi(v.name)
                if v_gi.get_excluded():
                    excluded.append(v_gi)
            if excluded:
                wrapped = []
                menu = QMenu(self.parentWidget())
                addMenu = menu.addMenu('Add to diagram')
                for v_gi in excluded:
                    wrapper = functools.partial(v_gi.set_excluded, False)
                    addMenu.addAction(v_gi._model.name, wrapper)
                menu.exec_(event.globalPos())

    def mousePressEvent(self, event):
        # Get the current cursor
        self._beginCursor = event.pos()
        # for each transition
        for key in self.scene()._transitions_gi:
            # Get the current transition
            trans = self.scene()._transitions_gi[key]
            trans._beginCursor = self._beginCursor

        super(GraphicsView, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        # Get the current cursor
        currentCursor = event.pos()
        # for each transition
        for key in self.scene()._transitions_gi:
            # Get the current transition
            trans = self.scene()._transitions_gi[key]
            trans._currentCursor = currentCursor

        return super(GraphicsView, self).mouseMoveEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            self.scene().removeSelected()
        else:
            return super(GraphicsView, self).keyPressEvent(event)


# WARNING : the set "a" must be sorted
# If n values are too close Then
# The average are done for these values
# The mapping gives for these values the same average
def getMapping(a):
    if len(a) == 0:
        return {}

    # init indexes
    indexes = [0] * len(a)
    average = [0] * len(a)
    average[0] = a[0]
    nbValue = 1

    # for each value
    for i in range(1, len(a)):
        # If difference too much
        if a[i] - a[i - 1] > 5:
            # Open new class
            indexes[i] = indexes[i - 1] + 1
            average[indexes[i - 1]] = average[indexes[i - 1]] / nbValue
            nbValue = 1
        else:
            # Stay in the current class
            indexes[i] = indexes[i - 1]
            nbValue = nbValue + 1

        # Add new value
        average[indexes[i]] += a[i]

    # if almost two values
    if len(a) > 1:
        # Average of the last class
        average[indexes[i - 1]] = average[indexes[i - 1]] / nbValue

    # Create map
    m = {}

    # for each value
    for i in range(0, len(a)):
        # New mapping
        m[a[i]] = average[indexes[i]]

    # Return the mapping
    return m

