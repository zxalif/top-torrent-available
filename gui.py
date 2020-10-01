#!/usr/bin/python3.6

import sys
from PyQt5.QtWidgets import QSystemTrayIcon, QApplication

from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import (
    QDesktopWidget,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
    QAbstractScrollArea,
    QHeaderView,
    QMessageBox,
)

from PyQt5.QtGui import (
    QFont,
)

from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore

from PyQt5.QtCore import QEvent, Qt
from libs.torrent import get_top_movies, get_trending_movies


try:
    from tmp import DATA as DUMMY
except ImportError:
    DUMMY = []

DEBUG = False


class SystemTrayIcon(QSystemTrayIcon):

    def __init__(self, icon, parent=None):
        super(SystemTrayIcon, self).__init__(icon, parent)
        self.parent = parent
        menu = QtWidgets.QMenu(parent)
        show = menu.addAction("Show")
        exitAction = menu.addAction("Exit")
        show.triggered.connect(self._show)
        exitAction.triggered.connect(self.closeVisibleWindow)
        self.setContextMenu(menu)

    def _show(self):
        self.parent.show()
        self.parent.raise_()
        self.parent.activateWindow()

    def closeVisibleWindow(self):

        qm = QMessageBox
        ret = qm.question(self.parent,
                          '?', "Are you sure, you want to exist?", qm.Yes | qm.No)
        if ret != qm.No:
            self.parent.fromTray = True
            self.parent.close()


class QMovieLabel(QtWidgets.QLabel):
    def __init__(self, fileName, parent=None):
        super(QMovieLabel, self).__init__(parent)
        m = QtGui.QMovie(fileName)
        self.setMovie(m)
        m.start()

    def setMovie(self, movie):
        super(QMovieLabel, self).setMovie(movie)
        s = movie.currentImage().size()
        self._movieWidth = s.width()
        self._movieHeight = s.height()


class WidgetWindow(QtWidgets.QMainWindow):
    gotoSignal = QtCore.pyqtSignal(str)

    def goto(self, name):
        self.gotoSignal.emit(name)


class MainWindow(WidgetWindow):
    windowName = 'main'
    headers = [
        'name',
        'type',
        'se',
        'le',
        'time',
        'size',
        '?',
    ]

    def __init__(self):
        super().__init__()
        self._data = DUMMY if DEBUG else []
        self.setWindowTitle("Trending/Top Torrent")

        self.initUI()

    def initUI(self):
        self.central_widgets = QWidget()
        self.UIComponents()

    def UIComponents(self):
        # choice the one

        # refresh button
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh)

        # main contents
        self.content = QTableWidget()
        self.content.setColumnCount(6)
        self.content.verticalHeader().setVisible(False)
        self.content.setHorizontalHeaderLabels(self.headers)
        self.content.resizeColumnsToContents()

        top_content_layout = QVBoxLayout()
        top_content_layout.addWidget(self.content)

        bottom_button_layout = QHBoxLayout()
        bottom_button_layout.addStretch(1)
        bottom_button_layout.addWidget(refresh_button)

        main_box_layout = QVBoxLayout()
        main_box_layout.addLayout(top_content_layout, 1)
        main_box_layout.addLayout(bottom_button_layout, 2)

        self.update_table()
        self.central_widgets.setLayout(main_box_layout)
        self.setCentralWidget(self.central_widgets)

    # refresh the current window
    def refresh(self):
        self.update_table()

    def get_data(self, force=False):
        return self.data

    @property
    def data(self):

        # try refreshing after 10 minute or an hour
        # ForceTabbedDocks

        if DEBUG: return self._data
        top_ = get_top_movies()
        trending_ = get_trending_movies()
        self._data = top_ + trending_
        return self._data

    def update_row(self, cell_no, data):
        url = 'https://127.0.0.1:8000'
        for index, key in enumerate(self.headers):
            self.content.setItem(
                cell_no,
                index,
                QTableWidgetItem(
                    data.get(key, url)
                )
            )

    def _clear_table(self):
        while self.content.rowCount() > 0:
            self.content.removeRow(0)

    def update_table(self):
        self._clear_table()
        self.content.setRowCount(
            len(self.data)
        )
        for i, item in enumerate(self.data):
            self.update_row(i, item)

        self.content.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        self.content.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)


class Window(QMainWindow):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.stacked_widget = QtWidgets.QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        self.frames = {}

        self.setFixedSize(350, 450)
        self.set_to_bottom_right_corner()

        # self.loading = QMovieLabel(fileName='img/loading.gif', parent=self)
        # self.loading.setAlignment(Qt.AlignCenter)

        self.tray_icon = SystemTrayIcon(QtGui.QIcon('img/tray.png'), self)
        self.tray_icon.show()

        # system app setup
        self.setWindowFlag(Qt.WindowMinimizeButtonHint, False)
        self.setFont(QFont('Courier', 9))

        # register all widgets
        self.register(MainWindow())

        self.goto('main')

    def set_to_bottom_right_corner(self):
        ag = QDesktopWidget().availableGeometry()
        # sg = QDesktopWidget().screenGeometry()

        x = ag.width()
        y = ag.height()
        self.move(x, y)

    def register(self, widget, name=None):
        self.frames[name or widget.windowName] = widget
        self.stacked_widget.addWidget(widget)
        if isinstance(widget, WidgetWindow):
            widget.gotoSignal.connect(self.goto)

    @QtCore.pyqtSlot(str)
    def goto(self, name):
        if name in self.frames:
            widget = self.frames[name]
            self.stacked_widget.setCurrentWidget(widget)
            self.setWindowTitle(widget.windowTitle())

    # on change Event (minimized/maximized)
    def changeEvent(self, event):
        if event.type() == QEvent.WindowStateChange:
            if event.oldState() and Qt.WindowMinimized:
                self.hide()

    # quit only available from system tray or DEBUG mode
    def closeEvent(self, event, **kwargs):
        if getattr(self, 'fromTray', False) or DEBUG:
            event.accept()
            return
        self.hide()
        event.ignore()


app = QApplication(sys.argv)
window = Window()
if DEBUG: window.show()
sys.exit(app.exec_())
