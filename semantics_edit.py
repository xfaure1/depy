import re
from PySide6.QtCore import Qt, QSettings, QStringListModel
from PySide6.QtGui import QTextCharFormat, QFont, QTextCursor
from PySide6.QtWidgets import QPlainTextEdit, QCompleter

from constant_value import TAB_WIDTH
from high_lighter import Highlighter


class SemanticsEdit(QPlainTextEdit):
    def __init__(self):
        super(SemanticsEdit, self).__init__()
        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.setUndoRedoEnabled(True)
        self.highlighter = Highlighter(self.document())
        self.read_settings()
        self.other_error_fmt = QTextCharFormat()
        self.other_error_fmt.setUnderlineStyle(QTextCharFormat.SpellCheckUnderline)
        self.other_error_fmt.setUnderlineColor(Qt.green)
        self.other_error_fmt.setFontUnderline(True)
        self._re_state = re.compile(r'\s*(?P<statedef>(?P<level>=+)\s*(?P<name>\w+)(?P<initial>\*)?\s*(?P<levele>(?P=level)))\s*(?P<comment>#.*)?$')
        self._completer = QCompleter(self)
        self._completer.setModelSorting(QCompleter.CaseSensitivelySortedModel)
        self._completer.setCaseSensitivity(Qt.CaseSensitive)
        self._completer.setWrapAround(False)
        self._completer.setWidget(self)
        self._completer.setCompletionMode(QCompleter.PopupCompletion)
        self._completer.setCaseSensitivity(Qt.CaseSensitive)
        self._completer.activated.connect(self.insert_completion)

    def read_settings(self):
        settings = QSettings()
        settings.beginGroup('SemanticsEditor')
        settings.beginGroup('Font')
        family = settings.value('Family', 'Courier')
        point_size = settings.value('PointSize', 10 )
        font = QFont(family, point_size)
        self.document().setDefaultFont(font)
        settings.endGroup()
        settings.beginReadArray('Formats')
        fmt_name = settings.value('Name')
        fmt_format = settings.value('Format')
        self.highlighter.set_format(fmt_name, fmt_format)
        settings.endArray()
        settings.endGroup()

    def set_completion(self, my_list):
        model = QStringListModel(my_list)
        self._completer.setModel(model)

    def insert_completion(self, completion):
        completion = self._completer.completionModel().data(completion)
        if self._completer.widget() is not self:
             return
        tc = self.textCursor()
        extra = len(completion) - len(self._completer.completionPrefix())
        if extra:
            tc.movePosition(QTextCursor.EndOfWord)
            tc.insertText(completion[-extra:])
            self.setTextCursor(tc)

    def _selected_blocks(self):
        cursor = self.textCursor()
        block = self.document().findBlock(cursor.selectionStart())
        if cursor.hasSelection():
            last_block = self.document().findBlock(cursor.selectionEnd()-1)
        else:
            last_block = block
        cursor.beginEditBlock()
        while True:
            cursor = QTextCursor(block)
            yield block
            if block == last_block:
                break
            block = block.next()
        cursor.endEditBlock()

    def inc_state_nesting(self):
        for block in self._selected_blocks():
            self._inc_state_nesting(block)

    def dec_state_nesting(self):
        for block in self._selected_blocks():
            self._dec_state_nesting(block)

    def _inc_state_nesting(self, block):
        text = (block.text())
        res = self._re_state.match(text)
        if res:
            cursor = QTextCursor(block)
            begin_pos = cursor.position()
            cursor.beginEditBlock()
            cursor.setPosition(begin_pos + res.end('level'))
            cursor.insertText('=')
            cursor.setPosition(begin_pos + res.start('level')+1)
            cursor.insertText('=')
            cursor.endEditBlock()

    def _dec_state_nesting(self, block):
        text = (block.text())
        res = self._re_state.match(text)
        if res and '=' != res.group('level'):
            cursor = QTextCursor(block)
            begin_pos = cursor.position()
            cursor.beginEditBlock()
            cursor.setPosition(begin_pos + res.end('level'))
            cursor.deletePreviousChar ()
            cursor.setPosition(begin_pos + res.start('level')-1)
            cursor.deleteChar ()
            cursor.endEditBlock()

    def keyPressEvent(self, event):
        """Reimplement tab handling, smart indentation on return and completion"""

        if self._completer.popup().isVisible():
            if event.key() == Qt.Key_Enter or \
               event.key() == Qt.Key_Return or \
               event.key() == Qt.Key_Escape or \
               event.key() == Qt.Key_Tab or \
               event.key() == Qt.Key_Backtab:
                event.ignore()
            return

        if event.key() == Qt.Key_Space and \
           event.modifiers() & Qt.ControlModifier:
            tc = self.textCursor()
            tc.select(QTextCursor.WordUnderCursor)
            completion_prefix = tc.selectedText()
            self._completer.setCompletionPrefix(completion_prefix)
            self._completer.popup().setCurrentIndex(
                self._completer.completionModel().index(0, 0))
            cr = self.cursorRect()
            cr.setWidth(self._completer.popup().sizeHintForColumn(0) +
                        self._completer.popup().verticalScrollBar().sizeHint().width())
            self._completer.complete(cr)

        elif event.key() == Qt.Key_Tab:
            # ctrl-tab rejected, reserved for tab change
            if event.modifiers() & Qt.ControlModifier:
                event.setAccepted(False)
                return

            cursor = self.textCursor()

            # Tab without selection: add spaces on the left of the cursor
            # until it is aligned on a tab stop
            if not cursor.hasSelection():
                position = cursor.position()
                pos_in_line = position - cursor.block().position()
                nb_add = TAB_WIDTH - (pos_in_line % TAB_WIDTH)
                cursor.insertText(' ' * nb_add)
                #if event.modifiers() & Qt.ControlModifier:
                #    self.inc_state_nesting()

            # Tab with selection: add tab_width spaces at the beginning of
            # each selected line
            else:
                insert_text = ' ' * TAB_WIDTH
                block = self.document().findBlock(cursor.selectionStart())
                last_block = self.document().findBlock(cursor.selectionEnd()-1)
                cursor.beginEditBlock()
                while True:
                    cursor = QTextCursor(block)
                    cursor.insertText(insert_text)
                    if block == last_block:
                        break
                    block = block.next()
                cursor.endEditBlock()
                #if event.modifiers() & Qt.ControlModifier:
                #    self.inc_state_nesting()

        elif event.key() == Qt.Key_Backtab:
            # shift-ctrl-tab rejected, reserved for tab change
            if event.modifiers() & Qt.ControlModifier:
                event.setAccepted(False)
                return

            cursor = self.textCursor()

            # BackTab without no selection: remove spaces on the left of the
            # cursor until it is aligned on a tab stop
            if not cursor.hasSelection():
                position = cursor.position()
                pos_in_line = position - cursor.block().position()
                if pos_in_line:
                    nb_remove = 1 + (pos_in_line-1) % TAB_WIDTH
                else:
                    nb_remove = 0
                for i in range(nb_remove):
                    if not self.document().characterAt(position-1).isspace():
                        return
                    cursor.deletePreviousChar()
                    position -= 1
                #if event.modifiers() & Qt.ControlModifier:
                #    self.dec_state_nesting()

            # BackTab with selection: remove tab_width spaces from the beginning
            # of selected each line
            else:
                block = self.document().findBlock(cursor.selectionStart())
                last_block = self.document().findBlock(cursor.selectionEnd()-1)
                cursor.beginEditBlock()
                while True:
                    cursor = QTextCursor(block)
                    for i in range(TAB_WIDTH):
                        if 1 >= block.length() or \
                            not self.document().characterAt(cursor.position()).isspace():
                            break
                        cursor.deleteChar()
                    if block == last_block:
                        break
                    block = block.next()
                cursor.endEditBlock()
                #if event.modifiers() & Qt.ControlModifier:
                #    self.dec_state_nesting()

        elif event.key() == Qt.Key_Return:
            cursor = self.textCursor()
            position = QTextCursor(cursor.block()).position()
            position_end = position + cursor.block().length() - 1
            ins = '\n'
            while self.document().characterAt(position).isspace() and \
                  position < position_end:
                ins += ' '
                position += 1

            cursor.insertText(ins)

        else:
            super(SemanticsEdit, self).keyPressEvent(event)

    def display_errors(self, errors):
        for err in errors:
            block = self.document().findBlockByLineNumber(err[0]-1)
            columns = err[1]
            s = columns[0]
            e = columns[1]
            cursor = QTextCursor(block)
            cursor.setPosition(block.position() + s, QTextCursor.MoveAnchor)
            cursor.setPosition(block.position() + e, QTextCursor.KeepAnchor)
            cursor.setCharFormat(self.other_error_fmt)

