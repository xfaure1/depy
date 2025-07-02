from PySide6.QtCore import QRectF, QPointF
from PySide6.QtWidgets import QGraphicsItem

from gui.click_zone import ClickZone
from gui.resizer import Resizer


MIN_VERTEX_WIDTH = 20
MIN_VERTEX_HEIGHT = 20

class VertexGItem(QGraphicsItem):
    NoSide = 0
    TopSide = 1
    BottomSide = 2
    LeftSide = 3
    RightSide = 4

    def __init__(self):
        super(VertexGItem, self).__init__()
        self.num = 0
        self._model = None
        self._resizer = Resizer(self, MIN_VERTEX_WIDTH, MIN_VERTEX_HEIGHT)

        flag = QGraphicsItem.GraphicsItemFlag
        self.setFlags(
            flag.ItemIsSelectable |
            flag.ItemIsMovable |
            flag.ItemIsFocusable |
            flag.ItemSendsGeometryChanges
        )

        self.setFlags(QGraphicsItem.ItemIsSelectable |
                      QGraphicsItem.ItemIsMovable |
                      QGraphicsItem.ItemIsFocusable |
                      QGraphicsItem.ItemSendsGeometryChanges)
        self._rect = QRectF(0, 0, 1, 1)
        self.setZValue(0)
        self._excluded = False  # excluded from diagram
        self._moving = False

    def set_model(self, model):
        self._model = model

    def boundingRect(self):
        return self._rect.adjusted(-ClickZone.HalfWidth, -ClickZone.HalfWidth, ClickZone.HalfWidth, ClickZone.HalfWidth)

    def abs_to_rel_point(self, abs_point):
        return QPointF((abs_point.x() - self._rect.left()) / self._rect.width(),
                       (abs_point.y() - self._rect.top()) / self._rect.height())

    def rel_to_abs_point(self, rel_point):
        return QPointF(self._rect.left() + rel_point.x() * self._rect.width(),
                       self._rect.top() + rel_point.y() * self._rect.height())

    def itemChange(self, change, value):
        self._resizer.itemChange(change, value)
        if change == QGraphicsItem.ItemPositionHasChanged and self.scene():
            self.scene().vertex_position_change(self)
        self._isSelect = self.isSelected()

        return super(VertexGItem, self).itemChange(change, value)

    def hoverMoveEvent(self, event):
        self._resizer.hoverMoveEvent(event)

    def mousePressEvent(self, event):
        self._resizer.mousePressEvent(event)
        super(VertexGItem, self).mousePressEvent(event)

    def mouseReleaseEvent(self, event):

        self._moving = False
        self.scene().vertex_position_change(None)
        self.update()
        return super(VertexGItem, self).mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        if self.scene():
            self.scene().set_dirty()
        self._moving = True
        if self._resizer.mouseMoveEvent(event):
            self.scene().vertex_size_has_changed(self)
        else:
            return super(VertexGItem, self).mouseMoveEvent(event)

    def remove_from_diagram(self):
        self.set_excluded(True)

    def set_excluded(self, value):
        self._excluded = value
        self.update_visibility()
        # update all transitions whose source/target state is self or
        # a child of self
        trans_set = []
        vertex = self._model
        self.scene().collect_transitions(vertex.container, vertex, trans_set)
        for (trans_gi, other_end) in trans_set:
            if trans_gi:
                trans_gi.update_visibility()

    def get_excluded(self):
        return self._excluded

    def get_excluded_r(self):
        if self._excluded:
            return True
        elif self.parentItem():
            return self.parentItem().get_excluded_r()
        else:
            return False

    def automatic_resize(self):
        pass

    def update_visibility(self):
        visible = not self._excluded
        self.setVisible(visible)

    # Update state graphic
    def set_vertex_gi(self, position, dimension, is_position_center=True):
        # Get position from item graphic vertex
        pos = self.pos()
        x_position = position[0]
        y_position = position[1]
        if is_position_center:
            x_position -= dimension[0] / 2
            y_position -= dimension[1] / 2
        # Update position
        pos.setX(x_position)
        pos.setY(y_position)
        self.setPos(pos)
        # Get rectangle from item graphic vertex
        self._rect.setX(0)
        self._rect.setY(0)
        self._rect.setWidth(dimension[0])
        self._rect.setHeight(dimension[1])


