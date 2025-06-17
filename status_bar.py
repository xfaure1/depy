import functools

from PySide6.QtWidgets import QStatusBar, QToolButton, QMenu
from PySide6.QtCore import Signal


class StatusBar(QStatusBar):
    jump_to_error = Signal(tuple)

    def __init__(self, parent=None):
        super(StatusBar, self).__init__(parent)
        self._errors = []
        self._errors_wg = QToolButton()
        self._errors_wg.setPopupMode(QToolButton.InstantPopup)
        self.addPermanentWidget(self._errors_wg)
        self.display_build_status([])


    def display_build_status(self, errors):
        self._errors  = errors
        nb_errors = len(errors)
        if nb_errors == 0:
            self._errors_wg.setText('No errors')
        else:
            menu = QMenu(self.parentWidget())
            for error in self._errors:
                wrapper = functools.partial(self.signal_jump_to_error, error)
                menu.addAction('Error line %d: %s' % (error[0], error[2]), wrapper)
            self._errors_wg.setMenu(menu)
            self.display_error(self._errors[0])

    def display_error(self, error):
        self._errors_wg.setText('Error Line %d: %s' %
                                 (error[0], error[2]))
    def display_status(self, status):
        self._errors_wg.setText(status)

    def signal_jump_to_error(self, error):
        self.jump_to_error.emit(error)

