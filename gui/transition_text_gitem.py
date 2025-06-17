from PySide6.QtCore import QRectF
from PySide6.QtGui import QTextOption, Qt, QPainter, QFont, QPen
from PySide6.QtWidgets import QStyle, QGraphicsItem

from constant_value import ITEMS_FONT
from gui.click_zone import ClickZone
from gui.resizer import Resizer

MIN_TRANS_TEXT_WIDTH = 50
MIN_TRANS_TEXT_HEIGHT = 12
POINT_SIZE = 10

class TransitionTextGItem(QGraphicsItem):

    def __init__(self, parent):
        super(TransitionTextGItem, self).__init__(parent)
        self._resizer = Resizer(self, MIN_TRANS_TEXT_WIDTH, MIN_TRANS_TEXT_HEIGHT)

        flg = QGraphicsItem.GraphicsItemFlag
        self.setFlags(flg.ItemIsSelectable | flg.ItemIsMovable | flg.ItemIsFocusable | flg.ItemSendsGeometryChanges)

        self._text = ''
        painter = QPainter()
        self._rect = QRectF(-5*POINT_SIZE, -POINT_SIZE, 10*POINT_SIZE, 2*POINT_SIZE)
        self._font = QFont(ITEMS_FONT)
        self._moving = False
        self._resizing = False

    def set_model(self, model):
        if model:
            self._text = model.get_str()
            self.setVisible('' != self._text)

    def boundingRect(self):
        return self._rect.adjusted(-ClickZone.HalfWidth, -ClickZone.HalfWidth ,ClickZone.HalfWidth, ClickZone.HalfWidth)

    def itemChange(self, change, value):
        self._resizer.itemChange(change, value)
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged and self.scene():
            self.parentItem().setSelected(value)
        return super(TransitionTextGItem, self).itemChange(change, value)

    def hoverMoveEvent(self, event):
        self._resizer.hoverMoveEvent(event)

    def mousePressEvent(self, event):
        self._resizer.mousePressEvent(event)
        print("mousePressEvent QGraphicsItem")
        QGraphicsItem.mousePressEvent(self, event)
        print("mousePressEvent QGraphicsItem")

    def mouseReleaseEvent(self, event):
        super(TransitionTextGItem, self).mouseReleaseEvent(event)
        self._moving = False
        self._resizing = False
        self.update() # redraw handles

    def mouseMoveEvent(self, event):
        if self.scene(): self.scene().set_dirty()
        self._moving = True
        if self._resizer.mouseMoveEvent(event):
            self._resizing = True
        else:
            return super(TransitionTextGItem, self).mouseMoveEvent(event)

    def paint(self, painter, option, widget):
        pen = QPen(Qt.SolidLine)
        pen.setColor(Qt.black)
        painter.setPen(pen)
        painter.setFont(self._font)
        txt_option = QTextOption(Qt.AlignHCenter)
        txt_option.setWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
        painter.drawText(self._rect, self._text, txt_option)
        if option.state & QStyle.State_Selected and not self.parentItem()._moving:
            #moving resizing  border  handles
            #0      0         1       1
            #1      0         0       0
            #1      1         1       0
            if (self._moving and self._resizing) or (not self._moving and not self._resizing):
                pen.setStyle(Qt.DotLine)
                painter.setPen(pen)
                painter.drawRect(self._rect)
                pen.setStyle(Qt.SolidLine)
                painter.setPen(pen)
            if not self._moving:
                self._resizer.paint(painter, option, widget)




