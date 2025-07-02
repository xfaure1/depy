import math

from PySide6.QtCore import QPointF, QRectF

from constant_value import VERTICAL_SEG, HORIZON_SEG, DIAGONAL_SEG
from gui.seg_rule import SegRule
from state.state import State
from tools.cfg import CFG


class DefaultPlacer(object):
    """Standard Placer

    This class assigns positions to orphans vertices and transitions, i.e.
    items which have been described in the semantics editor but not yet placed
    manually by the user
    """

    def place_vertices(self, scene, orphan_vertices):
        if not orphan_vertices:  # don't waste our time if there's nothing to do
            return
        self._scene = scene
        self._orphan_vertices = orphan_vertices
        self.layout_region(scene.get_sm().region[0], QPointF(0, 0))

    def layout_region(self, region, from_point):
        """Resize/Move all orphan vertices from a region. from_point is the suggested location
           the vertices will be placed
        """
        vertices = region.subVertex

        # layout each vertex first
        for vertex in vertices:
            self.layout_vertex(vertex)

        # if this region contains already-placed & visible vertices, orphans are placed
        # to the right of the bounding rectangle containing these vertices
        brect = QRectF()
        nb_orphans = 0
        for vertex in vertices:
            if not vertex in self._orphan_vertices:
                vertex_gi = self._scene.get_vertex_gi(vertex.name)
                if vertex_gi.isVisible():
                    rect = vertex_gi.mapToParent(vertex_gi.boundingRect()).boundingRect()
                    brect |= rect
            else:
                nb_orphans += 1
        if not brect.isNull():
            from_point = brect.topRight() + QPointF(20, 0)

        # place orphan vertices in a matrix starting from from_point
        if nb_orphans:
            nb_col = math.floor(math.sqrt(nb_orphans))
            nb_row = math.ceil(nb_orphans / nb_col)
            from_top = from_point.y()
            y = 0
            max_width = 0
            for vertex in vertices:
                if vertex in self._orphan_vertices:
                    vertex_gi = self._scene.get_vertex_gi(vertex.name)
                    cur_tl = vertex_gi.mapToParent(vertex_gi._rect.topLeft())
                    dx = from_point.x() - cur_tl.x()
                    dy = from_point.y() - cur_tl.y()
                    vertex_gi.setPos(vertex_gi.x() + dx, vertex_gi.y() + dy)

                    max_width = max(max_width, vertex_gi._rect.width())
                    y += 1
                    if y < nb_row:
                        from_point += QPointF(0, vertex_gi._rect.height() + 30)
                    else:
                        y = 0
                        from_point = QPointF(from_point.x() + max_width + 30, from_top)

    def layout_vertex(self, vertex):
        """Place the sub-vertices of this vertex and resize the vertex to fit
           if this was an orphan vertex
        """
        vertex_gi = self._scene.get_vertex_gi(vertex.name)
        if isinstance(vertex, State) and vertex.isComposite():
            if vertex in self._orphan_vertices:
                # no fancy placement, the vertex will be resized to fit anyway
                from_point = QPointF(0, 0)
            else:
                # ask the vertex where the sub-vertices should be placed
                from_point = vertex_gi.hint_place_sub_vertices()
            self.layout_region(vertex.region[0], from_point)

        if vertex in self._orphan_vertices:
            vertex_gi.automatic_resize()

    def place_transition(self, trans_gi):
        if trans_gi.is_transition_to_self():
            # transition to self: 3 segments
            trans_gi._source_point = QPointF(0.25, 0.5)
            middle_point = QPointF(0.5, 1.5)
            trans_gi._target_point = QPointF(0.75, 0.5)
            abs_source = trans_gi.rel_to_abs_point(trans_gi._source_gi, trans_gi._source_point)
            abs_middle = trans_gi.rel_to_abs_point(trans_gi._source_gi, middle_point)
            abs_target = trans_gi.rel_to_abs_point(trans_gi._target_gi, trans_gi._target_point)
            trans_gi._rules = \
                [SegRule(VERTICAL_SEG, abs_source),
                 SegRule(HORIZON_SEG, abs_middle),
                 SegRule(VERTICAL_SEG, abs_target)]
        elif trans_gi.is_local_transition():
            # local transition: from source border to target center
            trans_gi._source_point = QPointF(0, 0)
            trans_gi._target_point = QPointF(0.5, 0.5)
            abs_source = trans_gi.rel_to_abs_point(trans_gi._source_gi, trans_gi._source_point)
            abs_target = trans_gi.rel_to_abs_point(trans_gi._target_gi, trans_gi._target_point)
            trans_gi._rules = [SegRule(HORIZON_SEG, abs_source)]
        else:
            # regular transition: from source center to target center
            trans_gi._source_point = QPointF(0.5, 0.5)
            trans_gi._target_point = QPointF(0.5, 0.5)
            abs_source = trans_gi.rel_to_abs_point(trans_gi._source_gi, trans_gi._source_point)

            if CFG.is_used_diagonal():
                trans_gi._rules = [SegRule(DIAGONAL_SEG, abs_source)]
            else:
                trans_gi._rules = [SegRule(HORIZON_SEG, abs_source)]
        trans_gi.rebuild_path(False)
        trans_gi.rebuild_rules(False)

