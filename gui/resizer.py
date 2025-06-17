from PySide6.QtCore import QPointF
from PySide6.QtGui import QBrush, QPen, Qt
from PySide6.QtWidgets import QGraphicsItem

from gui.click_zone import ClickZone


class Resizer(object):
    """
    Provides the resizing widgets to any QGraphicsItem that defines
    a _rect attribute
    """
    CursorShapes = { ''  : Qt.ArrowCursor,
                     'l' : Qt.SizeHorCursor,
                     'r' : Qt.SizeHorCursor,
                     't' : Qt.SizeVerCursor,
                     'b' : Qt.SizeVerCursor,
                     'tl' : Qt.SizeFDiagCursor,
                     'tr' : Qt.SizeBDiagCursor,
                     'br' : Qt.SizeFDiagCursor,
                     'bl' : Qt.SizeBDiagCursor }

    def __init__(self, gi, min_width, min_height):
        self._gi = gi
        self._min_width = min_width
        self._min_height = min_height
        self._resize = ''
        self._fixed_ratio = False

    def set_min_size(self, min_width, min_height):
        self._min_width = min_width
        self._min_height = min_height

    def set_fixed_ratio(self, value):
        self._fixed_ratio = value

    def is_resizing(self):
        return self._resize != False
    def adjust(self):
        self._gi.prepareGeometryChange()
        self.adjust_handles()

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemSelectedHasChanged:
            self._gi.prepareGeometryChange()
            self.adjust_handles()
            self._gi.setAcceptHoverEvents(value)
            if not value:
                self._gi.setCursor(Qt.ArrowCursor)

    def hoverMoveEvent(self, event):
        pos = event.pos()
        for handle in self._resize_handles:
            if handle[1].contains(pos):
                resize = handle[0]
                break
        else:
            resize = ''
        self._gi.setCursor(self.CursorShapes[resize])

    def mousePressEvent(self, event):
        self._resize = ''
        if self._gi.isSelected() and event.button() == Qt.LeftButton:
            pos = event.pos()
            for handle in self._resize_handles:
                if handle[1].contains(pos):
                    self._resize = handle[0]
                    break

    def mouseMoveEvent(self, event):
        if self._resize:
            pos = event.pos()
            adjl = 0
            adjt = 0
            adjr = 0
            adjb = 0
            adjposx = 0
            adjposy = 0
            if -1 != self._resize.find('l'):
                adjl = self._gi._rect.left() - pos.x()
            elif -1 != self._resize.find('r'):
                adjr = pos.x() - self._gi._rect.right()
            if -1 != self._resize.find('t'):
                adjt = self._gi._rect.top() - pos.y()
            elif -1 != self._resize.find('b'):
                adjb = pos.y() - self._gi._rect.bottom()
            if self._gi._rect.height() + adjt + adjb < self._min_height:
                adjt = 0
                adjb = 0
            if self._gi._rect.width() + adjl + adjr < self._min_width:
                adjl = 0
                adjr = 0
            new_rect = self._gi._rect.adjusted(-adjl, -adjt, adjr, adjb)
            self._gi.prepareGeometryChange()
            self._gi._rect = new_rect
            self.adjust_handles()
            return True
        return False

    def paint(self, painter, option, widget):
        pen = QPen(Qt.black)
        brush = QBrush(Qt.white)
        painter.setPen(pen)
        painter.setBrush(brush)
        for handle in self._resize_handles:
            painter.drawRect(handle[1])

    def adjust_handles(self):
        self._resize_handles = [
            ('tl', ClickZone(self._gi._rect.topLeft())),
            ('bl', ClickZone(self._gi._rect.bottomLeft())),
            ('tr', ClickZone(self._gi._rect.topRight())),
            ('br', ClickZone(self._gi._rect.bottomRight()))]
        if not self._fixed_ratio:
            if self._gi._rect.height() >= ClickZone.HalfWidth*8:
                self._resize_handles.extend([
                    ('l',  ClickZone(QPointF(self._gi._rect.left(), self._gi._rect.top() + self._gi._rect.height() / 2))),
                    ('r',  ClickZone(QPointF(self._gi._rect.right(), self._gi._rect.top() + self._gi._rect.height() / 2))) ])
            if self._gi._rect.width() >= ClickZone.HalfWidth*8:
                self._resize_handles.extend([
                    ('t',  ClickZone(QPointF(self._gi._rect.left() + self._gi._rect.width() / 2, self._gi._rect.top()))),
                    ('b',  ClickZone(QPointF(self._gi._rect.left() + self._gi._rect.width() / 2, self._gi._rect.bottom()))) ])


