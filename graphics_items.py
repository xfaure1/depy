import functools
import math

from PySide6.QtCore import QRectF, Qt, QPointF, QLineF, QSizeF, Signal
from PySide6.QtGui import QColor, QPen, QBrush, QPainter, QFont, QTextOption, QPainterPath, QFontMetrics, QIcon, QPixmap
from PySide6.QtWidgets import QGraphicsItem, QStyle, QGraphicsPathItem, QMenu, QGraphicsView, QGraphicsScene
from uml_state_machine import *

PointSize = 10
Z_VALUE = 0
Z_VALUE_TRANSITION = 1  # transitions are above states
LINE_COLOR = QColor('#990033')
ITEMS_FONT = 'Arial'
MIN_TRANS_TEXT_WIDTH = 50
MIN_TRANS_TEXT_HEIGHT = 12
MIN_VERTEX_WIDTH = 20
MIN_VERTEX_HEIGHT = 20
MIN_STATE_WIDTH = 100
MIN_STATE_HEIGHT = 30
PSEUDO_STATE_WIDTH = 20
PSEUDO_STATE_HEIGHT = 20
MIN_PSEUDO_STATE_WIDTH = 20
MIN_PSEUDO_STATE_HEIGHT = 20
STATE_TEXT_MARGIN_H = 5
STATE_TEXT_MARGIN_V = 5

def Transition_Text(transition):
    textparts = []
    if transition.trigger:
        textparts.append(str(transition.trigger.event))
    if transition.guard:
        textparts.append('[%s]' % str(transition.guard))
    if transition.effect:
        textparts.append('/%s' % str(transition.effect))
    return ' '.join(textparts)

class ClickZone(QRectF):
    HalfWidth = 4
    def __init__(self, point):
        super(ClickZone, self).__init__(
                   point.x() - ClickZone.HalfWidth, \
                   point.y() - ClickZone.HalfWidth, \
                   2 * ClickZone.HalfWidth, \
                   2 * ClickZone.HalfWidth)

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
        self._resize_handles = [ \
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


class TransitionTextGItem(QGraphicsItem):

    def __init__(self, parent):
        super(TransitionTextGItem, self).__init__(parent)
        self._resizer = Resizer(self, MIN_TRANS_TEXT_WIDTH, MIN_TRANS_TEXT_HEIGHT)
        self.setFlags(QGraphicsItem.ItemIsSelectable|
                      QGraphicsItem.ItemIsMovable |
                      QGraphicsItem.ItemIsFocusable |
                      QGraphicsItem.ItemSendsGeometryChanges )
        self._text = ''
        painter = QPainter()
        self._rect = QRectF(-5*PointSize, -PointSize, 10*PointSize, 2*PointSize)
        self._font = QFont(ITEMS_FONT)
        self._moving = False
        self._resizing = False

    def set_model(self, model):
        if model:
            self._text = Transition_Text(model)
            self.setVisible('' != self._text)

    def boundingRect(self):
        return self._rect.adjusted(-ClickZone.HalfWidth, -ClickZone.HalfWidth ,ClickZone.HalfWidth, ClickZone.HalfWidth)

    def itemChange(self, change, value):
        self._resizer.itemChange(change, value)
        if change == QGraphicsItem.ItemSelectedHasChanged and self.scene():
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


def addCouple(tab, point, rule):
    tab.append([point.x(),point.y(), rule])
    
class TransitionGItem(QGraphicsPathItem):
    ArrowSize = 10
    ShapeHalfWidth = 5
    HorizSeg = 'H'
    VertSeg = 'V'

    class SegRule(object):
        """
        Describes the rules to draw a segment
        """
        def __init__(self, orient, anchor):
            self._orient = orient           # Horizontal/Vertical
            self._anchor = QPointF(anchor)    # The segment must contain this point

        def normal_rule(self, anchor):
            if self._orient == TransitionGItem.HorizSeg:
                return TransitionGItem.SegRule(TransitionGItem.VertSeg, anchor)
            else:
                return TransitionGItem.SegRule(TransitionGItem.HorizSeg, anchor)

        def translate(self, point):
            if self._orient == TransitionGItem.HorizSeg:
                self._anchor.setY(point.y())
            else:
                self._anchor.setX(point.x())

        def set_anchor(self, anchor):
            self._anchor = QPointF(anchor)

        def project_point(self, point):
            if self._orient == TransitionGItem.HorizSeg:
                point.setY(self._anchor.y())
            else:
                point.setX(self._anchor.x())

    class Segment:
        """
        Describes an actual segment to draw
        """
        def __init__(self, rule, p1, p2):
            # compute rectangle for click detection
            self._shape = QRectF(min(p1.x(), p2.x()) - TransitionGItem.ShapeHalfWidth,
                         min(p1.y(), p2.y()) - TransitionGItem.ShapeHalfWidth, \
                         math.fabs(p2.x() - p1.x()) + 2*TransitionGItem.ShapeHalfWidth, \
                         math.fabs(p2.y() - p1.y()) + 2*TransitionGItem.ShapeHalfWidth)
            self._rule = rule # rule used to draw this segment
            self.p1 = p1 # source point
            self.p2 = p2 # target point

        def contains(self, point):
            return self._shape.contains(point)

        def shape(self):
            return self._shape

        def rule(self):
            return self._rule

        def make_rule(self):
            """
            Returns a rule that can be used to describe this segment
            """
            # round to avoid floating-point errors while switching coordinates systems
            dx = round(self.p1.x() - self.p2.x())
            if 0 != dx:
                return TransitionGItem.SegRule(TransitionGItem.HorizSeg, self.p1)
            else:
                return TransitionGItem.SegRule(TransitionGItem.VertSeg, self.p1)


    class SegPoint:
        """
        Describes a point owned by one or two segments
        """
        def __init__(self, point, rule_before):
            self.point = QPointF(point)     # QPointF
            self.rule_before = rule_before # rule used to build the segment whose target is this point


    def __init__(self):
        super(TransitionGItem, self).__init__()
        self._model = None
        self._source_gi = None
        self._target_gi = None
        self._source_point = QPointF() # in % relative to _source_gi
        self._target_point = QPointF() # in % relative to _target_gi
        self._middle_points = [] # in % relative to _source_gi, only for transitions to self
        self._rules = []
        self._segments = []  # currently drawn segments
        self._shape = QPainterPath() # attribute returned by shape(), built from _segments
        self._text_pos = QPointF() # automatic position of transition text
        self._text_gi = TransitionTextGItem(self)
        self.setZValue(Z_VALUE_TRANSITION)
        self.setFlags(QGraphicsItem.ItemIsSelectable|
                      QGraphicsItem.ItemIsFocusable |
                      QGraphicsItem.ItemSendsGeometryChanges)
        self._moving = False

    def set_model(self, model, source_gi, target_gi):
        self._model = model
        self._source_gi = source_gi
        self._target_gi = target_gi
        self._text_gi.set_model(model)

    def is_transition_to_self( self ):
        return self._model.source is self._model.target

    def is_local_transition( self ):
        return self._model.kind == TransitionKind.local

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemSelectedHasChanged and self.scene():
            self._text_gi.setSelected(value)
            self.prepareGeometryChange()
        return QGraphicsPathItem.itemChange(self, change,  value)

    def shape(self):
        return self._shape

    def boundingRect(self):
        return self.path().boundingRect().adjusted(-ClickZone.HalfWidth-2, -ClickZone.HalfWidth-2, \
                                                    ClickZone.HalfWidth+2, ClickZone.HalfWidth+2)

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
    
        self.update() # redraw selection
        self._text_gi.update() # redraw selection

    def vertex_changed(self, vertex):
        if len(self._rules) >= 2 or vertex is self._source_gi._model:
            self._rules[0].set_anchor(self.rel_to_abs_point(self._source_gi, self._source_point))
        if len(self._rules) >= 2 or vertex is self._target_gi._model:
            self._rules[-1].set_anchor(self.rel_to_abs_point(self._target_gi, self._target_point))
            
        #todo probably something better in python to join iterators
        if self.is_transition_to_self():
            # for transitions to self, middle rules follow the state
            for i in range(len(self._middle_points)):
                self._rules[i+1].set_anchor(self.rel_to_abs_point(
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

    def rel_to_abs_point(self, vertex_gi, rel_point ):
        p = vertex_gi.rel_to_abs_point( rel_point )
        return self.mapFromItem(vertex_gi, p)

    def abs_to_rel_point(self, vertex_gi, abs_point):
        p = self.mapToItem(vertex_gi, abs_point)
        return vertex_gi.abs_to_rel_point( p )

    def rebuild_rules(self, moving):
        """ Rebuild the rules from the currently drawn segments
        """
        # don't rebuild if states are overlapping
        if len(self._segments) < 1:
            return

        self._rules = [seg.make_rule() for seg in self._segments]

        # rebuild relative source point from first rule
        spos = self.abs_to_rel_point(self._source_gi, self._segments[0].p1)
        if self._rules[0]._orient == TransitionGItem.HorizSeg:
            self._source_point.setY(spos.y())
        else:
            self._source_point.setX(spos.x())

        # for local transitions, also rebuild the opposite coordinate
        if self.is_local_transition():
            if self._rules[0]._orient == TransitionGItem.HorizSeg:
                self._source_point.setX(round(spos.x()))
            else:
                self._source_point.setY(round(spos.y()))

        # rebuild relative target point from last rule
        tpos = self.abs_to_rel_point(self._target_gi, self._segments[-1].p2)
        if self._rules[-1]._orient == TransitionGItem.HorizSeg:
            self._target_point.setY(tpos.y())
        else:
            self._target_point.setX(tpos.x())

        # for self-transitions, rebuild relative middle points from middle rules
        if self.is_transition_to_self():
            self._middle_points = []
            for seg in self._segments[1:-1]:
                mpos = self.abs_to_rel_point(self._source_gi, seg.p1)
                self._middle_points.append( mpos )

        self.rebuild_path(moving)


    def rebuild_path(self, moving):
        """ Rebuild the transition path (segments) from the rules
        """
        #To use model
        #trans = self._model
        source_rect = self.mapFromItem(self._source_gi, self._source_gi._rect).boundingRect()
        target_rect = self.mapFromItem(self._target_gi, self._target_gi._rect).boundingRect()
        
        # Build the transition points, following orientation and position rules
        source_point = self.rel_to_abs_point(self._source_gi, self._source_point)
        target_point = self.rel_to_abs_point(self._target_gi, self._target_point)

        #Init current
        current_point = source_point
        prev_rule = None
        self._tabCouple = []

        #If current cursor exist        
        if "_currentCursor" in dir(self):
            #Move cursor
            self._moveCursor = self._currentCursor-self._beginCursor
            self._beginCursor = self._currentCursor
                
        # The first seg_points is source point with no rule
        addCouple(self._tabCouple,source_point, None)
        
        #If the linked vertex of the current path are selected
        if (self._source_gi._isSelect and self._target_gi._isSelect):
            #If three segment
            if len(self._rules)==3:
                #Get the orientation
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
            addCouple(self._tabCouple,current_point, prev_rule)
            
            # Incrementation
            prev_rule = rule
            
        #The last point should be computed judging from the target point
        prev_rule.normal_rule(target_point).project_point(current_point)
        
        #Add the last point with rule and with no rule
        addCouple(self._tabCouple,current_point, prev_rule)
        addCouple(self._tabCouple,target_point, None)
        seg_points = []
        
        #For each couple
        for i in range(0,len(self._tabCouple)):
            #Create transition
            cpl = self._tabCouple[i]
            x = cpl[0]
            y = cpl[1]                
            seg_points.append(TransitionGItem.SegPoint(QPointF(x,y), cpl[2]))


        # Build a simplified path: stop as soon as it intersects the sink rect
        def streamline(sink_rect, seg_points, local_collision):
            result = []
            if len(seg_points) == 0: # or sink_rect.contains(seg_points[0].point): # limit cases
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
                    int_res, int_point = QLineF(sink_rect.topLeft(),    sink_rect.topRight()   ).intersects(line)
                elif dy < 0:
                    int_res, int_point = QLineF(sink_rect.bottomLeft(), sink_rect.bottomRight()).intersects(line)
                elif dx > 0:
                    int_res, int_point = QLineF(sink_rect.topLeft(),    sink_rect.bottomLeft() ).intersects(line)
                else:
                    int_res, int_point = QLineF(sink_rect.topRight(),   sink_rect.bottomRight()).intersects(line)
                if int_res == QLineF.BoundedIntersection:
                    result.append(TransitionGItem.SegPoint(int_point, sp2.rule_before))
                    break
                sp1 = sp2
            return result

        #print 'stream line to target'
        seg_points = streamline(target_rect, seg_points, False )
        seg_points.reverse()
        #print 'stream line to source'
        seg_points = streamline(source_rect, seg_points, self.is_local_transition() )
        seg_points.reverse()


        # Construct the actual Segments from the SegPoints, building the global
        # shape along the way
        self._shape = QPainterPath()
        self._segments = []
        if len(seg_points) > 1:
            p1 = seg_points[0].point
            for sp in seg_points[1:]:
                p2 = sp.point
                segment = TransitionGItem.Segment(sp.rule_before, p1, p2)
                #print 'add segment with rule %s' % sp.rule_before
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
                p1 = seg_points[q-1].point
                p2 = seg_points[q].point
                new_text_pos = QPointF((p1.x() + p2.x())/2, (p1.y() + p2.y())/2)
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
            if line.length(): # avoid division by zero if last segment is null
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
        self.setFlags(QGraphicsItem.ItemIsSelectable|
                      QGraphicsItem.ItemIsMovable|
                      QGraphicsItem.ItemIsFocusable|
                      QGraphicsItem.ItemSendsGeometryChanges)
        self._rect = QRectF(0,0,1,1)
        self.setZValue(Z_VALUE)
        self._excluded = False # excluded from diagram
        self._moving = False
            
    def set_model(self, model):
        self._model = model

    def boundingRect(self):
        return self._rect.adjusted(-ClickZone.HalfWidth, -ClickZone.HalfWidth, ClickZone.HalfWidth, ClickZone.HalfWidth)

    def abs_to_rel_point(self, abs_point):
        return QPointF((abs_point.x() - self._rect.left()) / self._rect.width(),
                       (abs_point.y() - self._rect.top()) / self._rect.height())

    def rel_to_abs_point(self, rel_point ):
        return QPointF(self._rect.left() + rel_point.x() * self._rect.width(),
                       self._rect.top() + rel_point.y() * self._rect.height())

    def itemChange(self, change, value):
        self._resizer.itemChange(change, value)
        if change == QGraphicsItem.ItemPositionHasChanged and self.scene():
            self.scene().vertex_position_change(self)
        self._isSelect = self.isSelected()
            
        return super(VertexGItem, self).itemChange(change,  value)

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
        #a child of self
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
                    lines.append(Transition_Text(transition))

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
        if change == QGraphicsItem.ItemChildAddedChange:
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
                       sepline_y)
        painter.setFont(self._name_font)
        painter.drawText(rect, Qt.AlignHCenter, self._model.name)

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
        #Get the current cursor
        self._beginCursor = event.pos()
        #for each transition
        for key in self.scene()._transitions_gi:
            #Get the current transition
            trans = self.scene()._transitions_gi[key]
            trans._beginCursor = self._beginCursor
        
        super(GraphicsView, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        #Get the current cursor
        currentCursor = event.pos()
        #for each transition
        for key in self.scene()._transitions_gi:
            #Get the current transition
            trans = self.scene()._transitions_gi[key]
            trans._currentCursor = currentCursor

        return super(GraphicsView, self).mouseMoveEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            self.scene().removeSelected()
        else:
            return super(GraphicsView, self).keyPressEvent(event)


#WARNING : the set "a" must be sorted
#If n values are too close Then 
#The average are done for these values
#The mapping gives for these values the same average
def getMapping(a):
    
    #init indexes
    indexes = [0]*len(a)
    average = [0]*len(a)
    average[0] = a[0]
    nbValue = 1
    
    #for each value
    for i in range(1,len(a)):
        #If difference too much
        if a[i]-a[i-1]>5:
            #Open new class
            indexes[i] = indexes[i-1]+1
            average[indexes[i-1]] = average[indexes[i-1]]/nbValue
            nbValue = 1
        else:
            #Stay in the current class
            indexes[i] = indexes[i-1]
            nbValue = nbValue + 1
        
        #Add new value
        average[indexes[i]] += a[i]
            
    #if almost two values
    if len(a)>1:
        #Average of the last class
        average[indexes[i-1]] = average[indexes[i-1]]/nbValue
    
    #Create map
    m = {}
    
    #for each value
    for i in range(0,len(a)):
        #New mapping
        m[a[i]] = average[indexes[i]]
    
    #Return the mapping
    return m

class GraphicsScene(QGraphicsScene):
    dirty = Signal()

    def __init__(self, parent):
        super(GraphicsScene, self).__init__(parent)
        self._parent = parent
        self._vertices_gi = {}
        self._transitions_gi = {}
        self._moving_vertex_gi = None
        self._moving_vertex_transitions = []
        self._dirty = False

    def reset(self):
        self.clear()
        self._sm = None
        self._vertices_gi = {}
        self._transitions_gi = {}
        self._moving_vertex_gi = None
        self._moving_vertex_transitions = []

    def set_sm(self, sm):
        self._sm = sm

    def get_sm(self):
        return self._sm

    def clear_dirty(self):
        self._dirty = False

    def set_dirty(self):
        if not self._dirty:
            self._dirty = True
            self.dirty.emit()

    def add_vertex_gi(self, id, gi):
        self._vertices_gi[ id ] = gi

    def del_vertex_gi(self, id):
        del self._vertices_gi[ id ]

    def get_vertex_gi(self, id):
        return self._vertices_gi.get(id)

    def add_transition_gi(self, id, gi):
        self._transitions_gi[ id ] = gi

    def del_transition_gi(self, id):
        del self._transitions_gi[ id ]

    def get_transition_gi(self, id):
        return self._transitions_gi.get(id)

    def is_sub_vertex(self, candidate, parent):
        if candidate is parent:
            return True
        elif candidate.container.state:
            return self.is_sub_vertex(candidate.container.state, parent)
        else:
            return False

    def collect_transitions(self, container, vertex, collected):
        # collect all transitions of this region
        for trans in container.transition:
            if trans.kind is not TransitionKind.internal:
                if self.is_sub_vertex(trans.source, vertex):
                    endpoint = trans.source
                elif self.is_sub_vertex(trans.target, vertex):
                    endpoint = trans.target
                else:
                    endpoint = None
                if endpoint:
                    trans_gi = self.get_transition_gi(Transition_Id(trans))
                    #print 'collect: %s' % Transition_Id(trans)
                    if trans_gi: # no append when transition gi are not yet created
                        collected.append((trans_gi, endpoint))

        # collect transitions for parent regions
        if container.state:
            self.collect_transitions(container.state.container, vertex, collected)

    #The position of state is updated
    #So we have to update transition
    def vertex_position_change(self, vertex_gi):
        #If the moving vertex is not the current vertex
        if self._moving_vertex_gi is not vertex_gi:
            # if previous vertex movement is done, update the transitions rules
            if vertex_gi is None:
                #For each transition-vertex
                for (transition_gi, mvertex) in self._moving_vertex_transitions:
                    transition_gi.rebuild_rules(False)

            # a new vertex is moving: collect all transitions whose source/target state
            # is vertex_gi or a child of vertex_gi
            self._moving_vertex_transitions = []
            if vertex_gi is not None:
                vertex = vertex_gi._model
                self.collect_transitions(vertex.container, vertex, self._moving_vertex_transitions)

            self._moving_vertex_gi = vertex_gi

        # redraw the transitions linked to the currently moving vertex
        for (transition_gi, mvertex) in self._moving_vertex_transitions:
            if transition_gi:
                transition_gi.vertex_changed(mvertex)


    def vertex_size_has_changed(self, vertex_gi):
        vertex = vertex_gi._model
        # redraw the transitions linked to the currently changing vertex
        for gitem in self.items():
            if type(gitem) is TransitionGItem:
                trans = gitem._model
                if trans.source is vertex or trans.target is vertex:
                    gitem.vertex_changed( vertex )
    
    def align(self):
        
        #Init set x and set y
        setX = set()
        setY = set()
        
        #for each transition
        for key in self._transitions_gi:
            #Get current transition
            transition = self._transitions_gi[key]
            #For each rules
            for r in transition._rules:
                #Get the current anchor
                setX.add(r._anchor.x())
                setY.add(r._anchor.y())
                
        #Get mapping for x and y
        mappingX = getMapping(sorted(setX))
        mappingY = getMapping(sorted(setY))

        #for each transition
        for key in self._transitions_gi:
            #Get current transition
            transition = self._transitions_gi[key]
            #For each rules
            for r in transition._rules:
                #Set the new anchor
                r._anchor.setX(mappingX[r._anchor.x()])
                r._anchor.setY(mappingY[r._anchor.y()])
                
            #Rebuild path
            transition.rebuild_path(False)
            
    def removeSelected(self):
        
        #For each vertex
        for key in self._vertices_gi:
            #Get the current vertex
            vertex = self._vertices_gi[key]
            #If selected
            if vertex.isSelected():
                #Remove from the diagram
                vertex.remove_from_diagram()
                
                
    def mousePressEvent(self, event):
        self.align()
        super(GraphicsScene, self).mousePressEvent(event)
        self._parent.mousePressEvent()
            
    
    