import math

from PySide6.QtCore import QRectF
from PySide6.QtGui import QPainterPath, QTransform

from constant_value import HORIZON_SEG, VERTICAL_SEG, DIAGONAL_SEG
from gui.seg_rule import SegRule

class Segment:
    """
    Describes an actual segment to draw with a clickable shape aligned with the direction
    """

    def __init__(self, rule, p1, p2):
        self._rule = rule  # rule used to draw this segment
        self.p1 = p1  # source point
        self.p2 = p2  # target point

        # Epaisseur du segment cliquable
        thickness = 10.0  # pixels (modifiable)
        self._thickness = thickness

        # Calculer direction et longueur
        dx = self.p2.x() - self.p1.x()
        dy = self.p2.y() - self.p1.y()
        length = math.hypot(dx, dy)
        angle = math.degrees(math.atan2(dy, dx))

        # Créer un rectangle horizontal centré sur y=0
        rect = QRectF(0, -thickness / 2, length, thickness)
        path = QPainterPath()
        path.addRect(rect)

        # Appliquer la transformation (translation + rotation)
        transform = QTransform()
        transform.translate(self.p1.x(), self.p1.y())
        transform.rotate(angle)

        # Appliquer au path et stocker comme forme
        self._shape = transform.map(path)

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
        dx = round(self.p1.x() - self.p2.x())
        dy = round(self.p1.y() - self.p2.y())

        if (dx == 0 and dy == 0) or (dx != 0 and dy !=0):
            return SegRule(DIAGONAL_SEG, self.p1)
        if dx != 0:
            return SegRule(HORIZON_SEG, self.p1)
        else:
            return SegRule(VERTICAL_SEG, self.p1)

    def __repr__(self):
        return "R:" + str(self._rule) + " P1:" + str(self.p1) + " P2:" + str(self.p2)
