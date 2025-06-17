import math

from PySide6.QtCore import QPointF, Qt, QLineF
from PySide6.QtGui import QPainterPath, QPen
from PySide6.QtWidgets import QGraphicsPathItem, QGraphicsItem, QStyle

from constant_value import LINE_COLOR, HORIZON_SEG
from gui.click_zone import ClickZone
from gui.seg_point import SegPoint
from gui.segment import Segment
from gui.transition_text_gitem import TransitionTextGItem
from state.transition_kind import TransitionKind


def addCouple(tab, point, rule):
    tab.append([point.x(), point.y(), rule])


class TransitionGItem(QGraphicsPathItem):
    ArrowSize = 10

    def __init__(self):
        super(TransitionGItem, self).__init__()
        self._model = None
        self._source_gi = None
        self._target_gi = None
        self._source_point = QPointF()  # in % relative to _source_gi
        self._target_point = QPointF()  # in % relative to _target_gi
        self._middle_points = []  # in % relative to _source_gi, only for transitions to self
        self._rules = []
        self._segments = []  # currently drawn segments
        self._shape = QPainterPath()  # attribute returned by shape(), built from _segments
        self._text_pos = QPointF()  # automatic position of transition text
        self._text_gi = TransitionTextGItem(self)

        # transitions are above states
        self.setZValue(1)

        flag = QGraphicsItem.GraphicsItemFlag
        self.setFlags(flag.ItemIsSelectable | flag.ItemIsFocusable | flag.ItemSendsGeometryChanges)
        self._moving = False

    def set_model(self, model, source_gi, target_gi):
        self._model = model
        self._source_gi = source_gi
        self._target_gi = target_gi
        self._text_gi.set_model(model)

    def is_transition_to_self(self):
        return self._model.source is self._model.target

    def is_local_transition(self):
        return self._model.kind == TransitionKind.local

    def itemChange(self, change, value):

        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged and self.scene():
            self._text_gi.setSelected(value)
            self.prepareGeometryChange()
        return QGraphicsPathItem.itemChange(self, change, value)

    def shape(self):
        return self._shape

    def boundingRect(self):
        return self.path().boundingRect().adjusted(-ClickZone.HalfWidth - 2, -ClickZone.HalfWidth - 2,
                                                   ClickZone.HalfWidth + 2, ClickZone.HalfWidth + 2)

    def mousePressEvent(self, event):
        self._moving = False
        self._moving_segment = None
        if event.button() == Qt.LeftButton:
            pos = event.pos()
            for seg in self._segments:
                if seg.contains(pos):
                    self._moving_segment = seg
        super(TransitionGItem, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.scene(): self.scene().set_dirty()
        self._moving = True
        if self._moving_segment:
            rule = self._moving_segment.rule()
            if rule is not None:
                rule.translate(event.pos())
                self.rebuild_path(True)

    def mouseReleaseEvent(self, event):
        self._moving = False
        if not self._moving_segment is None:
            self.rebuild_rules(False)

        self.update()  # redraw selection
        self._text_gi.update()  # redraw selection

    def vertex_changed(self, vertex):
        if len(self._rules) >= 2 or vertex is self._source_gi._model:
            self._rules[0].set_anchor(self.rel_to_abs_point(self._source_gi, self._source_point))
        if len(self._rules) >= 2 or vertex is self._target_gi._model:
            self._rules[-1].set_anchor(self.rel_to_abs_point(self._target_gi, self._target_point))

        # todo probably something better in python to join iterators
        if self.is_transition_to_self():
            # for transitions to self, middle rules follow the state
            for i in range(len(self._middle_points)):
                self._rules[i + 1].set_anchor(self.rel_to_abs_point(
                    self._source_gi,
                    self._middle_points[i]))

        self.rebuild_path(True)

    def update_visibility(self):
        # don't update items which parent is not visible
        if not self.parentItem() or self.parentItem().isVisible():
            x = self.scene().get_vertex_gi(self._model.source.name).get_excluded_r() or \
                self.scene().get_vertex_gi(self._model.target.name).get_excluded_r()
            visible = not x
            self.setVisible(visible)

    def rel_to_abs_point(self, vertex_gi, rel_point):
        p = vertex_gi.rel_to_abs_point(rel_point)
        return self.mapFromItem(vertex_gi, p)

    def abs_to_rel_point(self, vertex_gi, abs_point):
        p = self.mapToItem(vertex_gi, abs_point)
        return vertex_gi.abs_to_rel_point(p)

    def rebuild_rules(self, moving):
        """ Rebuild the rules from the currently drawn segments
        """
        # don't rebuild if states are overlapping
        if len(self._segments) < 1:
            return

        self._rules = [seg.make_rule() for seg in self._segments]

        # rebuild relative source point from first rule
        spos = self.abs_to_rel_point(self._source_gi, self._segments[0].p1)
        if self._rules[0]._orient == HORIZON_SEG:
            self._source_point.setY(spos.y())
        else:
            self._source_point.setX(spos.x())

        # for local transitions, also rebuild the opposite coordinate
        if self.is_local_transition():
            if self._rules[0]._orient == HORIZON_SEG:
                self._source_point.setX(round(spos.x()))
            else:
                self._source_point.setY(round(spos.y()))

        # rebuild relative target point from last rule
        tpos = self.abs_to_rel_point(self._target_gi, self._segments[-1].p2)
        if self._rules[-1]._orient == HORIZON_SEG:
            self._target_point.setY(tpos.y())
        else:
            self._target_point.setX(tpos.x())

        # for self-transitions, rebuild relative middle points from middle rules
        if self.is_transition_to_self():
            self._middle_points = []
            for seg in self._segments[1:-1]:
                mpos = self.abs_to_rel_point(self._source_gi, seg.p1)
                self._middle_points.append(mpos)

        self.rebuild_path(moving)

    def rebuild_path(self, moving):
        """ Rebuild the transition path (segments) from the rules
        """
        # To use model
        # trans = self._model
        source_rect = self.mapFromItem(self._source_gi, self._source_gi._rect).boundingRect()
        target_rect = self.mapFromItem(self._target_gi, self._target_gi._rect).boundingRect()

        # Build the transition points, following orientation and position rules
        source_point = self.rel_to_abs_point(self._source_gi, self._source_point)
        target_point = self.rel_to_abs_point(self._target_gi, self._target_point)

        # Init current
        current_point = source_point
        prev_rule = None
        self._tabCouple = []

        # If current cursor exist
        if "_currentCursor" in dir(self):
            # Move cursor
            self._moveCursor = self._currentCursor - self._beginCursor
            self._beginCursor = self._currentCursor

        # The first seg_points is source point with no rule
        addCouple(self._tabCouple, source_point, None)

        # If the linked vertex of the current path are selected
        if (self._source_gi._isSelect and self._target_gi._isSelect):
            # If three segment
            if len(self._rules) == 3:
                # Get the orientation
                x = self._rules[1]._anchor.x() + self._moveCursor.x()
                y = self._rules[1]._anchor.y() + self._moveCursor.y()
                self._rules[1]._anchor.setX(x)
                self._rules[1]._anchor.setY(y)

        # For each rule
        # First rule describes the source point
        # Last rule describes the previous point before target point
        for rule in self._rules:
            # Projet the current point with the current rule
            rule.project_point(current_point)
            addCouple(self._tabCouple, current_point, prev_rule)

            # Incrementation
            prev_rule = rule

        # The last point should be computed judging from the target point
        prev_rule.normal_rule(target_point).project_point(current_point)

        # Add the last point with rule and with no rule
        addCouple(self._tabCouple, current_point, prev_rule)
        addCouple(self._tabCouple, target_point, None)
        seg_points = []

        # For each couple
        for i in range(0, len(self._tabCouple)):
            # Create transition
            cpl = self._tabCouple[i]
            x = cpl[0]
            y = cpl[1]
            seg_points.append(SegPoint(QPointF(x, y), cpl[2]))

        # Build a simplified path: stop as soon as it intersects the sink rect
        def streamline(sink_rect, seg_points, local_collision):
            result = []
            if len(seg_points) == 0:  # or sink_rect.contains(seg_points[0].point): # limit cases
                return result
            sp1 = seg_points[0]
            for sp in seg_points[1:]:
                sp2 = sp
                result.append(sp1)
                line = QLineF(sp1.point, sp2.point)
                int_point = QPointF()
                # round to avoid floating-point errors while switching coordinates systems
                dx = round(sp2.point.x() - sp1.point.x())
                dy = round(sp2.point.y() - sp1.point.y())
                if local_collision:
                    dx = -dx
                    dy = -dy
                if dy > 0:
                    int_res, int_point = QLineF(sink_rect.topLeft(), sink_rect.topRight()).intersects(line)
                elif dy < 0:
                    int_res, int_point = QLineF(sink_rect.bottomLeft(), sink_rect.bottomRight()).intersects(line)
                elif dx > 0:
                    int_res, int_point = QLineF(sink_rect.topLeft(), sink_rect.bottomLeft()).intersects(line)
                else:
                    int_res, int_point = QLineF(sink_rect.topRight(), sink_rect.bottomRight()).intersects(line)
                if int_res == QLineF.BoundedIntersection:
                    result.append(SegPoint(int_point, sp2.rule_before))
                    break
                sp1 = sp2
            return result

        # print 'stream line to target'
        seg_points = streamline(target_rect, seg_points, False)
        seg_points.reverse()
        # print 'stream line to source'
        seg_points = streamline(source_rect, seg_points, self.is_local_transition())
        seg_points.reverse()

        # Construct the actual Segments from the SegPoints, building the global
        # shape along the way
        self._shape = QPainterPath()
        self._segments = []
        if len(seg_points) > 1:
            p1 = seg_points[0].point
            for sp in seg_points[1:]:
                p2 = sp.point
                segment = Segment(sp.rule_before, p1, p2)
                # print 'add segment with rule %s' % sp.rule_before
                self._segments.append(segment)
                shape = QPainterPath()
                shape.addRect(segment.shape())
                self._shape = self._shape.united(shape)
                p1 = p2

        if len(seg_points) < 2:
            return

        # Compute and set the final path to draw, including the arrow
        path = QPainterPath()
        if len(seg_points) > 1:
            # Reposition the transition text relative to the middle segment
            # todo: this could be better, maybe use % distances instead of absolutes
            (q, m) = divmod(len(seg_points), 2)
            if m != 0:
                new_text_pos = seg_points[q].point
            else:
                p1 = seg_points[q - 1].point
                p2 = seg_points[q].point
                new_text_pos = QPointF((p1.x() + p2.x()) / 2, (p1.y() + p2.y()) / 2)
            self._text_gi.setPos(self._text_gi.pos() - self._text_pos + new_text_pos)
            self._text_pos = new_text_pos

            # Draw the segments
            path.moveTo(seg_points[0].point)
            for sp in seg_points[1:]:
                path.lineTo(sp.point)

            # Draw the arrow
            last = seg_points[-1].point
            penultimate = seg_points[-2].point
            line = QLineF(last, penultimate)
            if line.length():  # avoid division by zero if last segment is null
                angle = math.acos(line.dx() / line.length());
                if line.dy() >= 0:
                    angle = (math.pi * 2) - angle;
                arrowP1 = last + QPointF(math.sin(angle + math.pi / 3) * TransitionGItem.ArrowSize,
                                         math.cos(angle + math.pi / 3) * TransitionGItem.ArrowSize);
                arrowP2 = last + QPointF(math.sin(angle + math.pi - math.pi / 3) * TransitionGItem.ArrowSize,
                                         math.cos(angle + math.pi - math.pi / 3) * TransitionGItem.ArrowSize);
                path.moveTo(arrowP1)
                path.lineTo(last)
                path.lineTo(arrowP2)

        self.prepareGeometryChange()
        self.setPath(path)

    def paint(self, painter, option, widget):
        pen = QPen(Qt.SolidLine)
        pen.setColor(LINE_COLOR)
        pen.setWidth(0)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(self.path())
        if option.state & QStyle.State_Selected and not self._moving:
            pen.setStyle(Qt.DotLine)
            pen.setColor(Qt.black)
            painter.setPen(pen)
            painter.drawPath(self._shape)

