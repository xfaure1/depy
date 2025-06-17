from PySide6.QtCore import QXmlStreamWriter

from gui.pseudo_state_gitem import PseudoStateGItem
from gui.state_gitem import StateGItem


class XMLWriter(object):
    def __init__(self, file):
        self._file = file
        self._stream = QXmlStreamWriter(file)
        self._stream.setAutoFormatting(True)
        self._stream.setAutoFormattingIndent(2)

    def write(self, diagrams):
        self._stream.writeStartDocument()
        self._stream.writeStartElement('body')
        for d in diagrams:
            self._stream.writeStartElement('diagram')
            self.write_StateDiagram(d)
            self._stream.writeEndElement()
        self._stream.writeEndElement()
        self._stream.writeEndDocument()
        return True

    def write_StateDiagram(self, diagram):
        #self._stream.writeAttribute('name', vertex_id)
        for (vertex_id, vertex_gi) in diagram._scene._vertices_gi.items():
            self._stream.writeStartElement('vertex')
            self._stream.writeAttribute('id', vertex_id)
            if isinstance(vertex_gi, StateGItem):
                self.write_StateGItem(vertex_gi)
            elif isinstance(vertex_gi, PseudoStateGItem):
                self.write_PseudoStateGItem(vertex_gi)
            else:
                raise 'oula'
            self._stream.writeEndElement()

        for (transition_id, transition_gi) in diagram._scene._transitions_gi.items():
            self._stream.writeStartElement('transition')
            self._stream.writeAttribute('id', transition_id)
            self.write_TransitionGItem(transition_gi)
            self._stream.writeEndElement()

    def write_VertexGItem(self, state_gi):
        self._stream.writeAttribute('excluded', str(state_gi._excluded))
        self._stream.writeEmptyElement('rect')
        self.write_QRectF(state_gi._rect)
        self._stream.writeEmptyElement('pos')
        self.write_QPointF(state_gi.pos())

    def write_StateGItem(self, state_gi):
        self._stream.writeAttribute('background', state_gi._background_color.name())
        self.write_VertexGItem(state_gi)

    def write_PseudoStateGItem(self, state_gi):
        self._stream.writeAttribute('pseudo', state_gi._model.kind)
        self.write_VertexGItem(state_gi)

    def write_QRectF(self, rect):
        self._stream.writeAttribute('x', str(rect.x()))
        self._stream.writeAttribute('y', str(rect.y()))
        self._stream.writeAttribute('width', str(rect.width()))
        self._stream.writeAttribute('height', str(rect.height()))

    def write_QPointF(self, point):
        self._stream.writeAttribute('x', str(point.x()))
        self._stream.writeAttribute('y', str(point.y()))

    def write_TransitionGItem(self, transition_gi):
        self._stream.writeEmptyElement('source_point')
        self.write_QPointF(transition_gi._source_point)
        self._stream.writeEmptyElement('target_point')
        self.write_QPointF(transition_gi._target_point)
        for rule in transition_gi._rules:
            self._stream.writeStartElement('rule')
            self._stream.writeAttribute('orient', rule._orient)
            self._stream.writeEmptyElement('anchor')
            self.write_QPointF(rule._anchor)
            self._stream.writeEndElement()
        if transition_gi._text_gi:
            self._stream.writeEmptyElement('text_pos')
            self.write_QPointF(transition_gi._text_pos)
            self._stream.writeStartElement('text')
            self._stream.writeEmptyElement('rect')
            self.write_QRectF(transition_gi._text_gi._rect)
            self._stream.writeEmptyElement('pos')
            self.write_QPointF(transition_gi._text_gi.pos())
            self._stream.writeEndElement()

