from PySide6.QtCore import QRectF


class ClickZone(QRectF):
    HalfWidth = 4
    def __init__(self, point):
        super(ClickZone, self).__init__(
                   point.x() - ClickZone.HalfWidth,
                   point.y() - ClickZone.HalfWidth,
                   2 * ClickZone.HalfWidth,
                   2 * ClickZone.HalfWidth)

