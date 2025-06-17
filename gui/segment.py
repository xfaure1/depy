import math

from PySide6.QtCore import QRectF

from constant_value import HORIZON_SEG, VERTICAL_SEG
from gui.seg_rule import SegRule


class Segment:
    """
    Describes an actual segment to draw
    """

    def __init__(self, rule, p1, p2):
        # compute rectangle for click detection
        shape_half_width = 5
        self._shape = QRectF(min(p1.x(), p2.x()) - shape_half_width,
                             min(p1.y(), p2.y()) - shape_half_width,
                             math.fabs(p2.x() - p1.x()) + 2 * shape_half_width,
                             math.fabs(p2.y() - p1.y()) + 2 * shape_half_width)
        self._rule = rule  # rule used to draw this segment
        self.p1 = p1  # source point
        self.p2 = p2  # target point

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
            return SegRule(HORIZON_SEG, self.p1)
        else:
            return SegRule(VERTICAL_SEG, self.p1)


