import functools

from PySide6.QtCore import QRectF, QSizeF, QPointF
from PySide6.QtGui import QColor, QFont, QPainterPath, QPixmap, QIcon, QFontMetrics, QPen, Qt, QBrush
from PySide6.QtWidgets import QGraphicsItem, QMenu, QStyle

from constant_value import ITEMS_FONT, LINE_COLOR
from gui.vertex_gitem import VertexGItem
from state.transition_kind import TransitionKind
from tools.cfg import CFG

MIN_STATE_WIDTH = 100
MIN_STATE_HEIGHT = 30
STATE_TEXT_MARGIN_H = 5
STATE_TEXT_MARGIN_V = 5

class StateGItem(VertexGItem):
    Colors = (
                '#ffffcc',
                '#c0c0c0',
                '#e0e0e0',
                '#ffd0d0',
                '#d0ffd0',
                '#d0ffff',
                '#d0d0ff',
                '#ffd0ff',
            )


    def __init__(self):
        super(StateGItem, self).__init__()
        self._resizer.set_min_size(MIN_STATE_WIDTH, MIN_STATE_HEIGHT)
        rect = QRectF(0, 0,
                      MIN_STATE_WIDTH, MIN_STATE_HEIGHT)
        self._rect = rect
        self._name_font = QFont(ITEMS_FONT)
        self._name_font.setWeight(QFont.Bold)
        self._background_color = QColor(StateGItem.Colors[0])
        self._actions_font = QFont(ITEMS_FONT)
        self._diagram = None

    def setDiagram(self,diagram):
        self._diagram = diagram

    def set_model(self, model):
        VertexGItem.set_model(self, model)
        self.build_actions_text()
        if self._model:
            self.setToolTip(self._model.note)

    def build_actions_text(self):
        if self._model:
            lines = []
            if self._model.entry:
                lines.append('entry /%s' % str(self._model.entry))
            if self._model.exit:
                lines.append('exit /%s' % str(self._model.exit))

            container = self._model.container
            for transition in container.transition:
                if transition.kind == TransitionKind.internal and transition.source is self._model:
                    lines.append(transition.get_str())

            self._actions_text = '\n'.join(lines)
        else:
            self._actions_text = ''

    def shape(self):
        path = QPainterPath()
        if self.isSelected():
            path.addRect(self.boundingRect())
        else:
            path.addRect(self._rect)
        return path

    def itemChange(self, change, value):

        if change == QGraphicsItem.GraphicsItemChange.ItemChildAddedChange:
            value.update_visibility()
        return super(StateGItem, self).itemChange(change, value)

    def contextMenuEvent(self, event):
        wrapped = []
        menu = QMenu(self.parentWidget())

        def add_toggle(attr_name, off_text, on_text):
            attr = getattr(self, attr_name)
            if attr:
                text = off_text
            else:
                text = on_text
            wrapper = functools.partial(setattr, self, attr_name, not attr)
            wrapped.append(wrapper)
            menu.addAction(text, wrapper)

        colorMenu = menu.addMenu('Background color')
        for color in StateGItem.Colors:
            pixmap = QPixmap(20, 20)
            qcolor = QColor(color)
            pixmap.fill(qcolor)
            icon = QIcon(pixmap)
            wrapper = functools.partial(setattr, self, 'background_color', qcolor)
            wrapped.append(wrapper)
            colorMenu.addAction(icon, '', wrapper)
        menu.addAction('Auto resize', self.automatic_resize)
        menu.addSeparator()
        menu.addAction('Remove from diagram', self.remove_from_diagram)

        excluded = []
        if self._model.isComposite():
            for v in self._model.region[0].subVertex:
                v_gi = self.scene().get_vertex_gi(v.name)
                if v_gi.get_excluded():
                    excluded.append(v_gi)
        if excluded:
            addMenu = menu.addMenu('Add to diagram')
            for v_gi in excluded:
                wrapper = functools.partial(v_gi.set_excluded, False)
                addMenu.addAction(v_gi._model.name, wrapper)

        menu.exec_(event.screenPos())

    def getbackground_color(self):
        return self._background_color

    def setbackground_color(self, qcolor):
        if self.scene(): self.scene().set_dirty()
        self._background_color = qcolor
        self.update()

    background_color = property(getbackground_color, setbackground_color)

    def automatic_resize(self):
        # visible children union
        cr = QRectF()
        for c in self.childItems():
            if c.isVisible():
                cr |= c.mapToParent(c.boundingRect()).boundingRect()

        # size needed for name and actions
        nmet = QFontMetrics(self._name_font)
        nw = nmet.horizontalAdvance(self._model.name) + 2*STATE_TEXT_MARGIN_H
        nh = nmet.height() + STATE_TEXT_MARGIN_V
        asz = self.get_action_text_size() + QSizeF(2*STATE_TEXT_MARGIN_H, STATE_TEXT_MARGIN_V)
        nasz = QSizeF(max(nw, asz.width(), MIN_STATE_WIDTH),
                      max(nh + asz.height(), MIN_STATE_HEIGHT))
        nar = QRectF(0, 0, nasz.width(), nasz.height() )
        if cr.isNull():
            nar.moveTo(self._rect.topLeft())
        else:
            nar.moveTo(cr.left(), cr.top() - nasz.height())
        cr |= nar

        self.prepareGeometryChange()
        self._rect = cr
        self._resizer.adjust()
        self.scene().vertex_size_has_changed(self)

    def hint_place_sub_vertices(self):
        nm = QFontMetrics(self._name_font)
        sepline_y = nm.height() + STATE_TEXT_MARGIN_V
        asz = self.get_action_text_size() + QSizeF(2*STATE_TEXT_MARGIN_H, STATE_TEXT_MARGIN_V)
        x = self._rect.left() + STATE_TEXT_MARGIN_H
        y = self._rect.top() + sepline_y + asz.height() + STATE_TEXT_MARGIN_V
        return QPointF(x,y)

    def paint(self, painter, option, widget):
        name_metrics = QFontMetrics(self._name_font)
        sepline_y = name_metrics.height() + STATE_TEXT_MARGIN_V

        # Draw state enclosure (in red if state is outside of its parent)
        pen = QPen(Qt.SolidLine)
        pen.setWidth(0)

        currentState = False
        if self._diagram != None:
            if self._diagram._currentState != None:
                if self._model.name == self._diagram._currentState:
                    brush = QBrush(QColor(255,0,0))
                    currentState = True

        if not currentState:
            brush = QBrush(self._background_color)

        parent_item = self.parentItem()
        if parent_item and not parent_item._rect.contains(self.mapToParent(self._rect).boundingRect()):
            pen.setColor(Qt.red)
        else:
            pen.setColor(LINE_COLOR)

        painter.setPen(pen)
        painter.setBrush(brush)
        painter.drawRoundedRect(self._rect, 5, 5)
        if self._actions_text:
            painter.drawLine(self._rect.left()  + STATE_TEXT_MARGIN_H,
                             self._rect.top() +  sepline_y,
                             self._rect.right() - STATE_TEXT_MARGIN_H,
                             self._rect.top() +  sepline_y)

        # Draw state name
        pen.setColor(Qt.black)
        painter.setPen(pen)
        rect = QRectF(self._rect.left()  + 1*STATE_TEXT_MARGIN_H,
                       self._rect.top(),
                       self._rect.width() - 2*STATE_TEXT_MARGIN_H,
                       CFG.get_height_rectangle(sepline_y, self._rect.height()))
        painter.setFont(self._name_font)
        painter.drawText(rect, Qt.AlignCenter, self._model.name.replace("_"," "))

        # Draw state actions & events
        if self._actions_text:
            rect = QRectF(self._rect.left()   + STATE_TEXT_MARGIN_H,
                          self._rect.top()    + sepline_y,
                          self._rect.width()  - 2*STATE_TEXT_MARGIN_H,
                          self._rect.height() - sepline_y - STATE_TEXT_MARGIN_V )
            painter.setFont(self._actions_font)
            painter.drawText(rect, Qt.AlignLeft, self._actions_text)

        # Draw resize handles if necessary
        if option.state & QStyle.State_Selected and not self._moving:
            self._resizer.paint(painter, option, widget)

    def get_action_text_size(self):
        afm = QFontMetrics(self._actions_font)
        size = afm.size(0, "")
        return QSizeF(size.width()*1.1, size.height()+1)

    def get_action_text_rect(self):
        name_metrics = QFontMetrics(self._name_font)
        sepline_y = name_metrics.height() + STATE_TEXT_MARGIN_V
        ats = self.get_action_text_size()
        rect = QRectF(self._rect.left()   + STATE_TEXT_MARGIN_H,
                      self._rect.top()    + sepline_y,
                      ats.width(),
                      ats.height() )
        return rect

