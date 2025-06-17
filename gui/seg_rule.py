from PySide6.QtCore import QPointF

from constant_value import HORIZON_SEG, VERTICAL_SEG


class SegRule(object):
    """
    Describes the rules to draw a segment
    """

    def __init__(self, orient, anchor):
        self._orient = orient  # Horizontal/Vertical
        self._anchor = QPointF(anchor)  # The segment must contain this point

    def normal_rule(self, anchor):
        if self._orient == HORIZON_SEG:
            return SegRule(VERTICAL_SEG, anchor)
        else:
            return SegRule(HORIZON_SEG, anchor)

    def translate(self, point):
        if self._orient == HORIZON_SEG:
            self._anchor.setY(point.y())
        else:
            self._anchor.setX(point.x())

    def set_anchor(self, anchor):
        self._anchor = QPointF(anchor)

    def project_point(self, point):
        if self._orient == HORIZON_SEG:
            point.setY(self._anchor.y())
        else:
            point.setX(self._anchor.x())

