from PySide6.QtGui import QColor

TAB_WIDTH = 3
ITEMS_FONT = 'Arial'
LINE_COLOR = QColor('#990033')
HORIZON_SEG = 'H'
VERTICAL_SEG = 'V'
DIAGONAL_SEG = 'D'
PSEUDO_STATE_INITIAL = 'initial'

MODE_GENERATE_NO = "No"
MODE_GENERATE_CPP_SRC = "source"
MODE_GENERATE_CPP_HEADER = "header"
MODE_GENERATE_PHP = "php"
MODE_GENERATE_PY = "python"
MODE_GENERATE_XML = "Xml"
MODE_GENERATE_DOT = "MyDot"
ALL_MODES = [MODE_GENERATE_CPP_SRC, MODE_GENERATE_CPP_HEADER,
             MODE_GENERATE_PHP, MODE_GENERATE_PY, MODE_GENERATE_XML, MODE_GENERATE_NO, MODE_GENERATE_DOT]