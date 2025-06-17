from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPen, QBrush
from PySide6.QtWidgets import QStyle

from constant_value import LINE_COLOR
from gui.vertex_gitem import VertexGItem

MIN_PSEUDO_STATE_WIDTH = 20
MIN_PSEUDO_STATE_HEIGHT = 20

class PseudoStateGItem(VertexGItem):
    def __init__(self):
        super(PseudoStateGItem, self).__init__()
        self._resizer.set_min_size(MIN_PSEUDO_STATE_WIDTH, MIN_PSEUDO_STATE_HEIGHT)
        self._resizer.set_fixed_ratio(True)
        rect = QRectF(0, 0, MIN_PSEUDO_STATE_WIDTH, MIN_PSEUDO_STATE_HEIGHT)
        self._rect = rect

    def paint(self, painter, option, widget):
        pen = QPen(Qt.SolidLine)
        pen.setColor(LINE_COLOR)
        pen.setWidth(0)
        brush = QBrush(Qt.black)
        parent_item = self.parentItem()
        if parent_item and not parent_item._rect.contains(self.mapToParent(self._rect).boundingRect()):
            pen.setColor(Qt.red)
            brush.setColor(Qt.red)
        painter.setPen(pen)
        painter.setBrush(brush)
        painter.drawEllipse(self._rect)

        # Draw resize handles if necessary
        if option.state & QStyle.State_Selected and not self._moving:
            self._resizer.paint(painter, option, widget)

