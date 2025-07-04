import sys
import traceback

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QMessageBox, QApplication

from main_window import MainWindow
from mode_generate_dep import ModeGenerateDep
from model.state_diagram import *
from tools.cfg import CFG

ROSE_FACTOR = 4

def msg_excepthook(my_type, value, trace_back):
    msg = ''.join(traceback.format_exception(my_type, value, trace_back))

    # Create QWidget parent invisible
    dummy_parent = QWidget()
    dummy_parent.hide()
    QMessageBox.warning(dummy_parent, "Software exception", msg)
    sys.__excepthook__(my_type, value, trace_back)

def main():
    # Variables
    mode_generate = CFG.get_mode_generate()
    sys.excepthook = msg_excepthook

    # Get from argument
    if len(sys.argv) > 1:
        initial_file = sys.argv[1]
    else:
        initial_file = None

    # Init application
    app = QApplication(sys.argv)
    icon = QIcon('depy.png')
    app.setWindowIcon(icon)
    wnd = MainWindow(initial_file, mode_generate)
    wnd.setWindowIcon(icon)
    wnd.show()
    app.exec()
    return 0


# Main function
if __name__ == "__main__":
    sys.exit(main())



