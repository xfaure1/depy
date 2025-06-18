from PySide6.QtCore import QPointF


class SegPoint:
    """
    Describes a point owned by one or two segments
    """

    def __init__(self, point, rule_before):
        self.point = QPointF(point)  # QPointF
        self.rule_before = rule_before  # rule used to build the segment whose target is this point


    def __repr__(self):
        return str("P:" + str(self.point) + " R:" + str(self.rule_before))
