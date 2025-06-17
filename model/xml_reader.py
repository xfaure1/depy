from PySide6.QtCore import QRectF, QPointF, QXmlStreamReader
from PySide6.QtGui import QColor

from gui.pseudo_state_gitem import PseudoStateGItem
from gui.seg_rule import SegRule
from gui.state_gitem import StateGItem
from gui.transition_gitem import TransitionGItem


def elements(stream, only_names=None):
    while not stream.atEnd():
        token_type = stream.readNext()
        if QXmlStreamReader.StartElement == token_type:
            name = str(stream.name())
            if not only_names or name in only_names:
                yield name
            else:
                skip_unknown_elements(stream)
        elif QXmlStreamReader.EndElement == token_type:
            break

def skip_unknown_elements(stream):
    while not stream.atEnd():
        token_type = stream.readNext()
        if QXmlStreamReader.StartElement == token_type:
            skip_unknown_elements(stream)
        elif QXmlStreamReader.EndElement == token_type:
            break

class XMLReader(object):
    def __init__(self, file):
        self._file = file
        self._stream = QXmlStreamReader(file)

    def read(self, diagram_factory):
        self._diagram_factory = diagram_factory
        while not self._stream.atEnd():
            token_type = self._stream.readNext()
            if QXmlStreamReader.StartElement == token_type:
                if self._stream.name() == 'body':
                    self.read_body()
                else:
                    skip_unknown_elements(self._stream)
        return True

    def read_body(self):
        for elem_name in elements(self._stream, ('diagram')) :
            if elem_name == 'diagram':
                attributes = self._stream.attributes()
                name = attributes.value('name')
                diagram = self._diagram_factory(name)
                self.read_StateDiagram(diagram)

    def read_StateDiagram(self, diagram):
        for elem_name in elements(self._stream, ('vertex', 'transition')) :
            if elem_name == 'vertex':
                attributes = self._stream.attributes()
                if attributes.hasAttribute('pseudo'):
                    vertex_gi = self.read_PseudoStateGItem()
                else:
                    vertex_gi = self.read_StateGItem()
                    vertex_gi.setDiagram(diagram)

                diagram._scene.add_vertex_gi(str(attributes.value('id')), vertex_gi)

            elif elem_name == 'transition':
                attributes = self._stream.attributes()
                transition_gi = self.read_TransitionGItem()
                diagram._scene.add_transition_gi(str(attributes.value('id')), transition_gi)

    def read_VertexGItem(self, state_gi):
        attributes = self._stream.attributes()
        state_gi._excluded = eval(str(attributes.value('excluded'))  or 'False')
        for elem_name in elements(self._stream, ('rect', 'pos')) :
            if self._stream.name() == 'rect':
                state_gi._rect = self.read_QRectF()
            elif self._stream.name() == 'pos':
                state_gi.setPos(self.read_QPointF())
        return state_gi


    def read_StateGItem(self):
        state_gi = StateGItem()
        attributes = self._stream.attributes()
        state_gi._background_color = QColor(attributes.value('background'))
        state_gi.show_sub = eval(str(attributes.value('show_sub')) or 'True')
        state_gi.show_actions = eval(str(attributes.value('show_actions'))  or 'True')
        state_gi = self.read_VertexGItem(state_gi)
        return state_gi

    def read_PseudoStateGItem(self):
        state = PseudoStateGItem()
        return self.read_VertexGItem(state)

    def read_TransitionGItem(self):
        transition = TransitionGItem()
        transition._rules = []
        for elem_name in elements(self._stream, ('source_point', 'target_point', 'rule', 'text_pos', 'text')) :
            if elem_name == 'source_point':
                transition._source_point = self.read_QPointF()
            elif elem_name == 'target_point':
                transition._target_point = self.read_QPointF()
            elif elem_name == 'rule':
                transition._rules.append(self.read_Rule())
            elif elem_name == 'text_pos':
                transition._text_pos = self.read_QPointF()
            elif elem_name == 'text':
                for telem_name in elements(self._stream, ('rect', 'pos')):
                    if telem_name == 'rect':
                        transition._text_gi._rect = self.read_QRectF()
                    elif telem_name == 'pos':
                        transition._text_gi.setPos(self.read_QPointF())
        return transition

    def read_Rule(self):
        attribs = self._stream.attributes()
        orient = str(attribs.value('orient'))
        for elem_name in elements(self._stream, ('anchor',)):
            if elem_name == 'anchor':
                anchor = self.read_QPointF()
        return SegRule(orient, anchor)

    def read_QRectF(self):
        attribs = self._stream.attributes()
        x = attribs.value('x')
        y = attribs.value('y')
        width = attribs.value('width')
        height = attribs.value('height')
        skip_unknown_elements(self._stream)
        return QRectF(float(x), float(y), float(width), float(height))

    def read_QPointF(self):
        attribs = self._stream.attributes()
        x = attribs.value('x')
        y = attribs.value('y')
        skip_unknown_elements(self._stream)
        return QPointF(float(x), float(y))

