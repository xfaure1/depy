from PySide6.QtCore import Qt
from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat, QBrush, QFont

from sms_reader import StateMachineBuilder


class Highlighter(QSyntaxHighlighter):
    def __init__(self, parent):
        super(Highlighter, self).__init__(parent)
        syntax_error_fmt = QTextCharFormat()
        syntax_error_fmt.setUnderlineStyle(QTextCharFormat.SpellCheckUnderline)
        syntax_error_fmt.setUnderlineColor(Qt.red)
        syntax_error_fmt.setFontUnderline(True)
        QTextCharFormat()
        comment_fmt = QTextCharFormat()
        comment_fmt.setForeground (QBrush(Qt.darkGreen))
        comment_fmt.setFontItalic(True)
        state_fmt = QTextCharFormat()
        state_fmt.setFontWeight (QFont.Bold)
        keyword_fmt = QTextCharFormat()
        keyword_fmt.setForeground (QBrush(Qt.blue))
        event_fmt = QTextCharFormat()
        event_fmt.setForeground (QBrush(Qt.darkRed))
        self.fmts = { 'statedef' : state_fmt,
                      'target' : state_fmt,
                      'keyword' : keyword_fmt,
                      'event' : event_fmt,
                      'guard' : event_fmt,
                      'comment' : comment_fmt,
                      'error' : syntax_error_fmt }

    def set_format(self, name, my_format):
        self.fmts[name] = my_format

    def highlightBlock(self, text):
        (kind, matched) = StateMachineBuilder.check_line_syntax(text)
        if matched:
            for group in matched.groupdict().keys():
                #key = kind + '_' + group
                #if key in self.fmts:
                #    fmt = self.fmts[key]
                #else:
                key = group
                if key in self.fmts:
                    fmt = self.fmts[key]
                else:
                    fmt = None
                if fmt:
                    (s,e) = matched.span(group)
                    self.setFormat(s, e-s, fmt)

