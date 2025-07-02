import functools
import os

from PySide6.QtCore import QFile, QIODevice, Qt, QByteArray, QSettings, QFileInfo, QDir, QFileSystemWatcher, QEvent, \
    QCoreApplication
from PySide6.QtGui import QBrush, QKeySequence, QPalette, QColor, QTextDocument, QPainter, QActionGroup, QAction
from PySide6.QtPrintSupport import QPrintPreviewDialog
from PySide6.QtWidgets import QMainWindow, QMessageBox, QHBoxLayout, QCheckBox, QPushButton, QSizePolicy, QLineEdit, \
    QLabel, QTreeWidgetItem, QDockWidget, QTreeWidget, QWidget, QTabWidget, QFileDialog, \
    QToolButton, QVBoxLayout, QApplication

from cheat_sheet import CheatSheet
from compileHeaders import GetCmdsErrorFileName
from constant_value import MODE_GENERATE_NO
from generate_dot import generate_dot_from_pyreverse, get_dep_from_dot, generate_dot_from_source
from mode_generate_dep import ModeGenerateDep
from model.xml_reader import XMLReader
from model.xml_writer import XMLWriter
from semantics_edit import SemanticsEdit
from sms_reader import StateMachineBuilder
from model.state_diagram import StateDiagram
from state.state_machine import StateMachine
from status_bar import StatusBar

ORGANIZATION_NAME = 'Soft'
ORGANIZATION_DOMAIN='soft.com'
SOFTWARE_VERSION = '0.00.00'
SOFTWARE_NAME = 'Depy'
MAX_RECENT_FILES = 5

# -----------------------------------------------
#            Functions
# -----------------------------------------------


def GetFullPathInclude(Dir, File):
    # For each files
    for root, dirs, files in os.walk(Dir):
        for name in files:
            if File in name:
                return root + "\\" + name

    return ""

# -----------------------------------------------
#            Class Main Window
# -----------------------------------------------

class MainWindow(QMainWindow):

    def MessageBoxCompileFile(self, resCompilation):

        # Create box
        msgBox = QMessageBox()
        data = []

        # Init string
        mystr = "Compilation OK " + "\n"
        # If fail
        if (resCompilation != 0):
            # Reset string with fail message
            mystr = "Compilation FAIL " + "\n"

        # Read all lines of compile file
        with open(self._CompileFilePath, "r") as f:
            data = f.readlines()

        # For each line
        for line in data:
            # Add current line
            mystr = mystr + line

        # Exec
        msgBox.setText(mystr);
        msgBox.exec();

    def CreateFindLayout(self):

        # Create two buttons find / combo box / button done
        self._find_prev_wg = QToolButton(arrowType=Qt.LeftArrow)
        self._find_next_wg = QToolButton(arrowType=Qt.RightArrow)
        self._find_combo_wg = QLineEdit()
        self._find_combo_wg.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
        self._find_done_wg = QPushButton('Done')

        # Search layout
        search_ly = QHBoxLayout()
        search_ly.setContentsMargins(0, 0, 0, 0)
        search_ly.setSpacing(0)
        search_ly.addStretch(0)
        search_ly.addWidget(QLabel('Find:'))
        search_ly.addSpacing(5)
        search_ly.addWidget(self._find_prev_wg)
        search_ly.addWidget(self._find_next_wg)
        search_ly.addSpacing(5)
        search_ly.addWidget(self._find_combo_wg)
        search_ly.addSpacing(5)
        search_ly.addWidget(self._find_done_wg)

        # return layout
        return search_ly

    def CreateCornerLayout(self):

        # Create two buttons find / combo box / button done
        self._depend_combo_wg = QLineEdit()
        self._depend_combo_wg.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
        self._depend_combo_wg.setText(self._mode_generate_dep.get_dep_path_code())
        self._depend_update_wg = QPushButton('Update')
        self._selected_combo_wg = QLineEdit()
        self._selected_combo_wg.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
        self._selected_combo_wg.setFixedWidth(200)
        self._selected_combo_wg.setText("")
        self._compile_file_wg = QPushButton('Compile File')
        self._compile_all_wg = QPushButton('Compile All')
        self._add_diagram_wg = QPushButton('New diagram')
        self._checkbox_wg = QCheckBox("Force", self)

        # Search layout
        corner_ly = QHBoxLayout()
        corner_ly.setContentsMargins(0, 0, 0, 0)
        corner_ly.setSpacing(0)
        corner_ly.addSpacing(5)
        corner_ly.addWidget(QLabel('Path:'))
        corner_ly.addSpacing(5)
        corner_ly.addWidget(self._depend_combo_wg)
        corner_ly.addSpacing(5)
        corner_ly.addWidget(self._depend_update_wg)
        corner_ly.addSpacing(5)
        corner_ly.addWidget(QLabel('Selected:'))
        corner_ly.addSpacing(5)
        corner_ly.addWidget(self._selected_combo_wg)
        corner_ly.addSpacing(5)
        corner_ly.addWidget(self._compile_file_wg)
        corner_ly.addSpacing(5)
        corner_ly.addWidget(self._compile_all_wg)
        corner_ly.addSpacing(5)
        corner_ly.addWidget(self._checkbox_wg)

        # return layout
        return corner_ly

    def __init__(self, file_name, mode_generate):
        super(MainWindow, self).__init__(None)
        QCoreApplication.setApplicationName(SOFTWARE_NAME)
        QCoreApplication.setOrganizationName(ORGANIZATION_NAME)
        QCoreApplication.setOrganizationDomain(ORGANIZATION_DOMAIN)

        # Init attributes
        self._mode_generate_dep = ModeGenerateDep(mode_generate)
        self._CompileFilePath = "Tmp\\CompileOut.txt"
        self._CmdsErrorFilePath = "Tmp\\" + GetCmdsErrorFileName()
        self._sms_name = ''
        self._smd_name = ''
        self._sm = None
        self._dirty = False
        self._build_errors = []
        self._cur_build_error = -1
        self._current_file_base = ''
        self._current_rose_base = ''
        self.wrapped = []
        self._borders = []
        self._file_watcher = QFileSystemWatcher()
        self._recent_file_actions = []
        self.setAcceptDrops(True)
        self._menu_actions = {}
        self._cheat_sheet = CheatSheet(self)

        def add_menus(menu, items):
            for text, slot, shortcut in items:
                if text:
                    action = menu.addAction(text, slot, shortcut)
                    self._menu_actions[text] = action
                else:
                    menu.addSeparator()

        def add_menu_group(menu, func, items):
            group = QActionGroup(self)
            for item in items:
                wrapper = functools.partial(func, item[1])
                self.wrapped.append(wrapper)
                menu_action = QAction(item[0], group, checkable=True, triggered=wrapper)
                menu.addAction(menu_action)
                menu_action.setChecked(item[2])

        # Create corner widget for tab
        corner_wg = QWidget()
        corner_wg.setLayout(self.CreateCornerLayout())

        # Declaration main widget
        self._tabs_wg = QTabWidget()
        self._tabs_wg.setDocumentMode(True)
        self._tabs_wg.setCornerWidget(corner_wg)
        self._tabs_wg.setMovable(True)
        self._tabs_wg.setTabsClosable(True)

        # Declaration semantic page widget and text
        self._semantics_page = QWidget()
        self.semantics_text = SemanticsEdit()

        # Create widget search and layout search and set to the layout into the widget
        self._search_wg = QWidget()
        self._search_wg.setLayout(self.CreateFindLayout())

        # Add two widget on semantics diagram : 1) search 2) semantics text
        semantics_ly = QVBoxLayout(self._semantics_page)
        semantics_ly.setContentsMargins(0, 0, 0, 0)
        semantics_ly.setSpacing(0)
        semantics_ly.addWidget(self._search_wg)
        semantics_ly.addWidget(self.semantics_text)

        # Hide search widget
        self._search_wg.hide()
        self._diagrams = []
        self.setCentralWidget(self._tabs_wg)

        # Create the outline dock
        self._outline_wg = QTreeWidget()
        palette = self._outline_wg.palette()
        palette.setColor(QPalette.Inactive, QPalette.Base, QColor('#ededed'))
        palette.setColor(QPalette.Active, QPalette.Base, QColor('#d9dfe7'))
        self._outline_wg.setPalette(palette)
        self._outline_wg.setColumnCount(1)
        self._outline_wg.header().hide()
        self._outline_wg.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.MinimumExpanding)
        self._ol_states_wg = QTreeWidgetItem(('STATES',))
        self._ol_states_wg.setFlags(Qt.ItemIsEnabled)
        headerBrush = QBrush(Qt.darkGray)

        # Style of states
        self._ol_states_wg.setForeground(0, headerBrush)
        self._outline_wg.addTopLevelItem(self._ol_states_wg)
        self._ol_states_wg.setExpanded(True)

        outline_dock = QDockWidget('Outline')
        outline_dock.setObjectName('OutlineDock')
        outline_dock.setWidget(self._outline_wg)
        self.addDockWidget(Qt.LeftDockWidgetArea, outline_dock)

        self._status_bar = StatusBar()
        self.setStatusBar(self._status_bar)

        # Create menus
        fileMenu = self.menuBar().addMenu('File')
        add_menus(fileMenu, (
            ('New', self.cmd_new, QKeySequence.New),
            ('&Open...', self.cmd_open, QKeySequence.Open),
            ('&Save', self.cmd_save, QKeySequence.Save),
            ('Save as...', self.cmd_save_as, QKeySequence.SaveAs),
            ('', None, None),
            ('New diagram', self.cmd_new_diagram, QKeySequence()),
            ('', None, None),
            ('Print...', self.cmd_print, QKeySequence.Print),
            ('', None, None),
        ))

        # For each file
        for i in range(MAX_RECENT_FILES):
            action = QAction(self)
            self._recent_file_actions.append(action)
            action.setVisible(False)
            fileMenu.addAction(action)
            action.triggered.connect(self.cmd_open_recent_file)

        # recent file separator file menu
        self._recent_file_separator = fileMenu.addSeparator()
        add_menus(fileMenu, (
            ('&Quit', self.cmd_quit, 'Alt+F4'),
        ))

        # Search menu
        searchMenu = self.menuBar().addMenu('Search')
        add_menus(searchMenu, (
            ("Find...", self.cmd_find, QKeySequence.Find),
            ("Find Next", self.cmd_find_next, QKeySequence.FindNext),
            ("Find Previous", self.cmd_find_prev, QKeySequence.FindPrevious),
        ))

        # Super state menu
        superStateMenu = self.menuBar().addMenu('Super state')
        add_menus(superStateMenu, (
            ("Super State...", self.cmd_superstate, 'Ctrl+t'),
        ))

        # Edit menu
        editMenu = self.menuBar().addMenu('Edit')
        add_menus(editMenu, (
            ("Increase state nesting",
             self.semantics_text.inc_state_nesting, 'Ctrl+>'),
            ("Decrease state nesting",
             self.semantics_text.dec_state_nesting, 'Ctrl+<'),
            ('', None, None),
            ("Auto colorize all states", self.cmd_auto_colorize, QKeySequence()),
        ))

        viewMenu = self.menuBar().addMenu('View')
        add_menus(viewMenu, (
            ("Align selection", self.cmd_align, 'Ctrl+j'),
            ("Zoom in", self.cmd_zoom_in, 'Ctrl++'),
            ("Zoom out", self.cmd_zoom_out, 'Ctrl+-'),
            ("100%", self.cmd_zoom_100, 'Ctrl+='),
        ))

        helpMenu = self.menuBar().addMenu('Help')
        add_menus(helpMenu, (
            ("About...", self.cmd_about, QKeySequence()),
            ('', None, None),
            ("Language syntax...", self.cmd_syntax_cheat, QKeySequence()),
        ))

        self.update_title()
        self._compile_file_wg.clicked.connect(self.cmd_compile_file)
        self._compile_all_wg.clicked.connect(self.cmd_compile_all)
        self._depend_update_wg.clicked.connect(self.cmd_depend_update)
        self._add_diagram_wg.clicked.connect(self.cmd_new_diagram)
        self._tabs_wg.currentChanged.connect(self.currentTabChanged)
        self._tabs_wg.tabCloseRequested.connect(self.tabCloseRequested)
        self.semantics_text.textChanged.connect(self.set_dirty)

        # Connect button search
        self._find_combo_wg.installEventFilter(self)
        self._find_combo_wg.returnPressed.connect(self.cmd_find_next)
        self._find_prev_wg.clicked.connect(self.cmd_find_prev)
        self._find_next_wg.clicked.connect(self.cmd_find_next)
        self._find_done_wg.clicked.connect(self.cmd_find_done)

        # Connect file watcher
        self._file_watcher.fileChanged.connect(self.file_changed)
        self.update_recent_file_actions()

        self.read_settings()

        # If dependencies update is needed
        if self._mode_generate_dep.is_enabled_generator():
            # Update dependencies
            self.cmd_depend_update()
            # If file name is not found
            if file_name is None:
                # Get the file name SMS / SMD from module generator
                file_name = self._mode_generate_dep.get_sms_smd_name()
        if mode_generate != MODE_GENERATE_NO:
            # Update dependencies
            self.cmd_depend_update()

        # If file name is found
        if file_name is not None:
            # File Info
            file_info = QFileInfo(file_name)
            file_base = file_info.absolutePath() + '/' + file_info.completeBaseName()
            self.load_files(file_base)
        else:
            # New file
            self.cmd_new()
            if file_name is None:
                file_name = self._mode_generate_dep.get_sms_smd_name()

        self.file_name = file_name

    def cmd_new(self):

        finf = QFileInfo(self.file_name)
        file_base = finf.absolutePath() + '/' + finf.completeBaseName()
        loaded = self.load_files(file_base)

    def cmd_new(self):
        # ask for confirmation before losing current changes
        if not self.offer_save():
            return

        self.reset(True)

    def cmd_open(self):
        # ask for confirmation before losing current changes
        if not self.offer_save():
            return

        # ask for file name to open
        (file_name, filter) = QFileDialog.getOpenFileName(self,
                                                          SOFTWARE_NAME + ' - Open', self._current_file_base,
                                                          'Diagrams (*.smd);;Semantics (*.sms)')
        if not file_name:
            return

        # ok, load for real
        finf = QFileInfo(file_name)
        file_base = finf.path() + '/' + finf.completeBaseName()
        self.load_files(file_base)

    def cmd_save(self):
        if not self._current_file_base:
            return self.cmd_save_as()
        else:
            return self.save_files(self._current_file_base)

    def cmd_save_as(self):
        # ask for file name to save
        (file_name, filter) = QFileDialog.getSaveFileName(self,
                                                          SOFTWARE_NAME + ' - Save As', self._current_file_base,
                                                          "Diagrams (*.smd)",
                                                          options=QFileDialog.DontConfirmOverwrite)
        if not file_name:
            return False

        # remove user-appended sms/smd
        if file_name.endswith('.sms') or file_name.endswith('.smd'):
            file_name = file_name[:-4]

        # ask for confirmation before overwriting
        finf = QFileInfo(file_name)
        file_base = finf.path() + '/' + finf.completeBaseName()

        # Init sms name and smd name
        self._sms_name = file_base + '.sms'
        self._smd_name = file_base + '.smd'
        exists = []
        if QFile.exists(self._smd_name):
            exists.append((QDir.convertSeparators(self._smd_name)))
        if QFile.exists(self._sms_name):
            exists.append((QDir.convertSeparators(self._sms_name)))
        if exists:
            if len(exists) > 1:
                exists.append('already exist. Do you want to replace them?')
            else:
                exists.append('already exists. Do you want to replace it?')
            msg = '\n'.join(exists)
            res = QMessageBox.warning(self, SOFTWARE_NAME,
                                      msg,
                                      QMessageBox.Yes | QMessageBox.No,
                                      QMessageBox.No)
            if res == QMessageBox.No:
                return False

        # ok, save for real
        return self.save_files(file_base)

    def cmd_open_recent_file(self):
        action = self.sender()
        if action:
            if not self.offer_save():
                return
            self.load_files(action.data())

    def cmd_quit(self):
        if self.offer_save():
            self.write_settings()
            QCoreApplication.quit()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):

        print("dropEnter")

        # ask for confirmation before losing current changes
        if not self.offer_save():
            return

        # ask for file name to open
        file_name = event.mimeData().urls()[0].toLocalFile()

        # ok, load for real
        finf = QFileInfo(file_name)
        file_base = finf.path() + '/' + finf.completeBaseName()
        self.load_files(file_base)

    def cmd_about(self):
        QMessageBox.about(self, SOFTWARE_NAME,
                          SOFTWARE_NAME + ' ' + SOFTWARE_VERSION +
                          """
                          Qt licensed under the LGPL version 2.1 license
                          (http://qt.nokia.com)
                          
                          PySide licensed under the LGPL version 2.1 license
                          (http://www.pyside.org)
                          """)

    def cmd_syntax_cheat(self):
        self._cheat_sheet.show()

    def preview_print(self, printer):
        wg = self._tabs_wg.currentWidget()
        if isinstance(wg, StateDiagram):
            painter = QPainter(printer)
            wg._scene.clearSelection()
            wg._scene.setSceneRect(wg._scene.itemsBoundingRect())
            wg._scene.render(painter)
        else:
            self.semantics_text.print_(printer)

    def cmd_print(self):
        dialog = QPrintPreviewDialog()
        dialog.paintRequested.connect(self.preview_print)
        dialog.exec()

    def cmd_zoom_100(self):
        wg = self._tabs_wg.currentWidget()
        if isinstance(wg, StateDiagram):
            wg.zoom_100()

    def cmd_refresh(self):
        wg = self._tabs_wg.currentWidget()
        if isinstance(wg, StateDiagram):
            wg.refresh()

    def cmd_zoom_in(self):
        wg = self._tabs_wg.currentWidget()
        if isinstance(wg, StateDiagram):
            wg.zoom_in()

    def cmd_align(self):
        wg = self._tabs_wg.currentWidget()
        if isinstance(wg, StateDiagram):
            wg.align()

    def cmd_zoom_out(self):
        wg = self._tabs_wg.currentWidget()
        if isinstance(wg, StateDiagram):
            wg.zoom_out()

    def closeEvent(self, event):
        if self.offer_save():
            self.write_settings()
        else:
            event.ignore()

    def cmd_find(self):

        # Init find widget on semantics text
        cursor = self.semantics_text.textCursor()
        text = cursor.selectedText()
        if text:
            self._find_combo_wg.setText(text)
        self._search_wg.show()
        self._find_combo_wg.setFocus(Qt.OtherFocusReason)
        self._find_combo_wg.selectAll()

        # Init find widget on semantics text
        wg = self._tabs_wg.currentWidget()
        if isinstance(wg, StateDiagram):
            wg.InitFind()

    def cmd_superstate(self):

        # Init find widget on semantics text
        wg = self._tabs_wg.currentWidget()
        if isinstance(wg, StateDiagram):
            wg.InitSuperState()

    def cmd_find_done(self):
        self._search_wg.hide()

    def cmd_find_next(self):
        self.semantics_text.find(self._find_combo_wg.text())

        # Init find widget on semantics text
        wg = self._tabs_wg.currentWidget()
        if isinstance(wg, StateDiagram):
            wg.NextVertex()
            wg.ColorAllConcernedBlock()

    def cmd_find_prev(self):
        self.semantics_text.find(self._find_combo_wg.text(), QTextDocument.FindBackward)

        # Init find widget on semantics text
        wg = self._tabs_wg.currentWidget()
        if isinstance(wg, StateDiagram):
            wg.PreviousVertex()
            wg.ColorAllConcernedBlock()

    def cmd_auto_colorize(self):
        wg = self._tabs_wg.currentWidget()
        if isinstance(wg, StateDiagram):
            wg.auto_colorize()

    def compile(self):
        sm = StateMachine()
        smb = StateMachineBuilder(sm)
        res = smb.build_from_string(self.semantics_text.toPlainText())

        self._build_errors = smb.get_errors()
        self._cur_build_error = -1
        self._status_bar.display_build_status(self._build_errors)
        self.semantics_text.set_completion([s for s in sorted(smb._all_states)])

        def update_tree(wg, children):
            while wg.childCount():
                wg.removeChild(wg.child(0))
            for child in sorted(children):
                item = QTreeWidgetItem((child,))
                item.setFlags(Qt.ItemIsEnabled)
                wg.addChild(item)

        update_tree(self._ol_states_wg, smb._all_states)
        all_events_names = set([str(evt) for evt in smb._all_events])
        if '' in all_events_names: all_events_names.remove('')

        sm._port = smb._port

        if res:
            self._sm = sm
            return sm
        else:
            return None

    def file_changed(self, path):
        res = QMessageBox.warning(self, SOFTWARE_NAME,
                                  'Another application has modified the file\n\n%s\n\n'
                                  'Do you wish to reload the state machine ?' %
                                  path,
                                  QMessageBox.Yes | QMessageBox.No,
                                  QMessageBox.Yes)
        if res == QMessageBox.Yes:
            finf = QFileInfo(path)
            file_base = finf.path() + '/' + finf.completeBaseName()
            self.load_files(file_base)

    def offer_save(self):
        if self._dirty:
            res = QMessageBox.warning(self, SOFTWARE_NAME,
                                      'Save changes to %s before proceeding?' % QDir.toNativeSeparators(
                                          self._current_file_base),
                                      QMessageBox.Discard | QMessageBox.Save | QMessageBox.Cancel,
                                      QMessageBox.Save)
            if res == QMessageBox.Cancel:
                return False
            if res == QMessageBox.Save:
                if not self.cmd_save():
                    return False
        return True

    def reset(self, blank_diagram=False):
        del self._diagrams[:]
        self._tabs_wg.clear()
        self.semantics_text.setPlainText('= Root* =\n')
        self._tabs_wg.addTab(self._semantics_page, 'Semantics')
        if blank_diagram:
            self.new_diagram()
        self.set_current_file('')
        self.clear_dirty()

    def cmd_new_diagram(self, name=''):
        diagram = self.new_diagram()
        self._tabs_wg.setCurrentWidget(diagram)
        return diagram

    def cmd_depend_update(self):

        # Get folder input
        folder_input = self._depend_combo_wg.text()
        dot_name_path = self._mode_generate_dep.get_dot_name_path()

        # If python mode
        if self._mode_generate_dep.is_python():
            # Get dependencies from py reverse
            dot_name = self._mode_generate_dep.dot_name
            dependencies = generate_dot_from_pyreverse(folder_input, dot_name_path, dot_name)
        elif self._mode_generate_dep.is_dot():
            # Get dependencies from dot directly
            dependencies = get_dep_from_dot(dot_name_path)
        else:
            # Get dependencies from source
            mode_file = self._mode_generate_dep.mode
            dependencies = generate_dot_from_source(folder_input, dot_name_path, mode_file)

        # Generate SMS and SMD
        self._mode_generate_dep.generate_sms_smd(dependencies)

    def cmd_compile_all(self):

        # If checkbox force
        if self._checkbox_wg.isChecked():
            # if file exist
            print("check")
            if os.path.exists(self._CmdsErrorFilePath):
                # Remove file
                print("remove")
                os.remove(self._CmdsErrorFilePath)

                # Create command and execute
        cmd = "compileHeaders.bat "
        cmd += self._depend_combo_wg.text() + "..\\"
        print(cmd)
        os.system(cmd)

    def cmd_compile_file(self):

        # Init find widget on semantics text
        wg = self._tabs_wg.currentWidget()
        if isinstance(wg, StateDiagram):
            # Get selected combo
            selected = self._selected_combo_wg.text()

            # If almost one is selected
            if len(selected) > 0:
                # Get the first one
                filename = selected + ".h"
                # Build path
                FullPathTRDir = self._depend_combo_wg.text() + "..\\"
                FullPathInclude = GetFullPathInclude(FullPathTRDir, filename)

                # If not found
                if FullPathInclude == "":
                    print("not found")
                    print(FullPathTRDir)
                    print(filename)

                # Create command
                cmd = "..\\compileOneHeader.bat "
                cmd += FullPathInclude + " "
                cmd += FullPathTRDir + " "
                cmd += "1"

                # Create subfolder
                print("Create subdirectory")
                folderTmp = "Tmp"
                try:
                    os.mkdir(folderTmp)
                except OSError as error:
                    print(error)

                    # Change the current working directory
                os.chdir(folderTmp)

                # Clean workspace
                try:
                    os.remove("*.obj")
                except OSError as error:
                    print(error)

                    # Execute command
                print(cmd)
                resCompilation = os.system(cmd)

                # Go back directory
                os.chdir("..\\")

                # Message box compile
                self.MessageBoxCompileFile(resCompilation)

    def new_diagram(self, name=''):
        diagram = StateDiagram(self)
        diagram.dirty.connect(self.set_dirty)
        self._diagrams.append(diagram)
        if not name: name = 'Diagram'
        self._tabs_wg.addTab(diagram, name)
        self.set_dirty()
        return diagram

    # Update combo box
    def updateSelectedCombo(self, selected):

        # Update combo box
        self._selected_combo_wg.setText(selected)

    def load_files(self, file_base):

        # Init sms name and smd name
        self._sms_name = file_base + '.sms'
        self._smd_name = file_base + '.smd'

        # open the semantics file
        sms_file = QFile(self._sms_name)
        if not sms_file.open(QIODevice.ReadOnly):
            QMessageBox.warning(self, SOFTWARE_NAME,
                                'Cannot open semantics file %s' % QDir.convertSeparators(self._sms_name))
            return False

        # open the diagram file
        smd_file = QFile(self._smd_name)
        is_diagram = True
        if not smd_file.open(QIODevice.ReadOnly):
            is_diagram = False

        QApplication.setOverrideCursor(Qt.WaitCursor)

        # clear current scene and text
        self.reset()

        # read the diagrams file
        success = True
        if is_diagram:
            def diagram_factory(name):
                diagram = self.new_diagram(name)
                return diagram

            reader = XMLReader(smd_file)
            if not reader.read(diagram_factory):
                QMessageBox.error(self, SOFTWARE_NAME,
                                  'Error while reading diagram file %s' % QDir.convertSeparators(self._smd_name))
                success = False

        # load the semantics file into the text widget
        if success:
            data = sms_file.readAll()
            self.semantics_text.setPlainText(data.data().decode('Windows-1252'))

        sms_file.close()
        smd_file.close()

        QApplication.restoreOverrideCursor()

        if success:
            self.set_current_file(file_base)
            for d in self._diagrams:
                d.update()
                d.setWnd(self)
            self.clear_dirty()
        else:
            self.reset(True)

        return success

    def save_files(self, file_base):

        # Init sms name and smd name
        self._sms_name = file_base + '.sms'
        self._smd_name = file_base + '.smd'

        # we don't want to watch the files we're saving
        self._file_watcher.removePath(self._sms_name)
        self._file_watcher.removePath(self._smd_name)

        # open the semantics file
        sms_file = QFile(self._sms_name)
        if not sms_file.open(QIODevice.WriteOnly):
            QMessageBox.warning(self, SOFTWARE_NAME,
                                'Cannot save semantics to %s' % QDir.convertSeparators(self._sms_name))
            return False

        # open the diagram file
        smd_file = QFile(self._smd_name)
        is_diagram = True
        if not smd_file.open(QIODevice.WriteOnly):
            QMessageBox.warning(self, SOFTWARE_NAME,
                                'Cannot save diagram to %s' % QDir.convertSeparators(self._smd_name))
            sms_file.close()
            return False

        # save diagrams
        success = True
        if not XMLWriter(smd_file).write(self._diagrams):
            success = False
            QMessageBox.warning(self, SOFTWARE_NAME,
                                "Failed to save %s" % (self._smd_name))

        # save semantics # todo encoding
        if not sms_file.write(self.semantics_text.toPlainText().encode('Windows-1252')):
            success = False
            QMessageBox.warning(self, SOFTWARE_NAME,
                                "Failed to save %s" % (self._sms_name))

        sms_file.close()
        smd_file.close()

        self.clear_dirty()
        self.set_current_file(file_base)
        return success

    def set_current_file(self, file_base):
        if self._current_file_base:
            self._file_watcher.removePath(self._current_file_base + '.sms')
            self._file_watcher.removePath(self._current_file_base + '.smd')

        self._current_file_base = file_base
        self.update_title()

        if self._current_file_base:
            sms_file = self._current_file_base + '.sms'
            smd_file = self._current_file_base + '.smd'
            if QFile.exists(sms_file):
                self._file_watcher.addPath(sms_file)
            if QFile.exists(smd_file):
                self._file_watcher.addPath(smd_file)

            settings = QSettings()
            files = settings.value("recentFileList", [])
            files = [f for f in files if f != file_base]
            files.insert(0, file_base);
            files = files[:MAX_RECENT_FILES]
            settings.setValue("recentFileList", files)

            self.update_recent_file_actions()

    def update_recent_file_actions(self):
        settings = QSettings()
        files = settings.value("recentFileList", [])
        num_recent_files = min(len(files), MAX_RECENT_FILES)
        for i in range(num_recent_files):
            text = '&%d %s' % (i + 1, self.stripped_name(files[i]))
            self._recent_file_actions[i].setText(text)
            self._recent_file_actions[i].setData(files[i])
            self._recent_file_actions[i].setVisible(True)
        for i in range(num_recent_files, MAX_RECENT_FILES):
            self._recent_file_actions[i].setVisible(False)
        self._recent_file_separator.setVisible(num_recent_files > 0)

    def update_title(self):
        title = ''
        if self._current_file_base:
            title += self.stripped_name(self._current_file_base)
        title += '[*] - ' + SOFTWARE_NAME
        self.setWindowTitle(title)

    def stripped_name(self, file_base):
        return QFileInfo(file_base).fileName()

    def currentTabChanged(self, index):
        wg = self._tabs_wg.currentWidget()
        if isinstance(wg, StateDiagram):
            wg.update()
            is_diag = True
        else:
            is_diag = False
        for m in ("Zoom in", "Zoom out", "100%",
                  "Auto colorize all states"):
            self._menu_actions[m].setEnabled(is_diag)
        for m in ("Increase state nesting", "Decrease state nesting"):
            self._menu_actions[m].setEnabled(not is_diag)

    def tabCloseRequested(self, index):
        tab = self._tabs_wg.widget(index)
        if tab is self._semantics_page:
            return
        res = QMessageBox.warning(self, SOFTWARE_NAME,
                                  'Do you really want to discard the selected diagram?',
                                  QMessageBox.Discard | QMessageBox.Cancel,
                                  QMessageBox.Cancel)
        if res == QMessageBox.Cancel:
            return
        self._tabs_wg.removeTab(index)
        self._diagrams.remove(tab)
        self.set_dirty()

    def eventFilter(self, object, event):
        if event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Escape:
                if self._find_combo_wg == object:
                    self._search_wg.hide()
        return super(MainWindow, self).eventFilter(object, event)

    def set_dirty(self):
        if not self._dirty:
            self._dirty = True
            self.setWindowModified(True)

    def clear_dirty(self):
        self._dirty = False
        self.setWindowModified(False)
        # self._scene.clear_dirty()

    def repaintState(self):
        print("repaint")

    def set_status(self, my_string):
        self._status_bar.display_status(my_string)

    def write_settings(self):
        settings = QSettings()
        settings.beginGroup('MainWindow');
        settings.setValue('geometry', self.saveGeometry())
        settings.setValue('state', self.saveState())
        settings.endGroup();
        settings.beginGroup('CheatSheet');
        settings.setValue('geometry', self._cheat_sheet.saveGeometry())
        settings.endGroup();

    def read_settings(self):
        settings = QSettings()
        settings.beginGroup('MainWindow');
        self.restoreGeometry(settings.value('geometry', QByteArray()))
        self.restoreState(settings.value('state', QByteArray()))
        settings.endGroup();
        settings.beginGroup('CheatSheet');
        self._cheat_sheet.restoreGeometry(settings.value('geometry', QByteArray()))
        settings.endGroup();

