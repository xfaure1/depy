from PySide6.QtCore import QPointF

from constant_value import HORIZON_SEG, VERTICAL_SEG, DIAGONAL_SEG


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
        elif self._orient == VERTICAL_SEG:
            return SegRule(HORIZON_SEG, anchor)
        else:
            return SegRule(DIAGONAL_SEG, anchor)

    def translate(self, point):
        if self._orient == HORIZON_SEG:
            self._anchor.setY(point.y())
        elif self._orient == VERTICAL_SEG:
            self._anchor.setX(point.x())
        else:
            self._anchor.setX(point.x())
            self._anchor.setY(point.y())


    def set_anchor(self, anchor):
        self._anchor = QPointF(anchor)

    def project_point(self, point):
        if self._orient == HORIZON_SEG:
            point.setY(self._anchor.y())
        elif self._orient == VERTICAL_SEG:
            point.setX(self._anchor.x())
        else:
            point.setX(self._anchor.x())
            point.setY(self._anchor.y())

    def __repr__(self):
        return "O:" + str(self._orient) + " A:" + str(self._anchor)


