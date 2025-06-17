import os

from PySide6.QtCore import QFile, QIODevice, SIGNAL
from PySide6.QtWidgets import QDialog, QTextBrowser, QDialogButtonBox, QVBoxLayout


class CheatSheet(QDialog):
    def __init__(self, parent):
        super(CheatSheet, self).__init__(parent)
        text = QTextBrowser()
        help_path = os.path.join('help.html')
        help_file = QFile(os.path.normpath(help_path))
        if help_file.open(QIODevice.ReadOnly):
            data = help_file.readAll().data()
            text.setHtml(data.decode('utf8'))
        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        layout = QVBoxLayout()
        layout.addWidget(text)
        layout.addWidget(button_box)
        self.setLayout(layout)
        self.setWindowTitle("State machine language cheat sheet")
        self.connect(button_box, SIGNAL("accepted()"), self.accept)
