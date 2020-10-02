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
    QLabel,
)

from PyQt5.QtGui import (
    QFont,
)

from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore

from PyQt5.QtCore import QEvent, Qt
from libs.torrent import get_top_movies, get_trending_movies
from datetime import timedelta, datetime
from uuid import uuid4
import qtawesome as qta
import requests
import time


try:
    from tmp import DATA as DUMMY
except ImportError:
    DUMMY = []

DEBUG = True
COUNT_LABEL = 'Count: %d'
CONNECT_CHECK_INTERVAL = 3600  # (s) - every hour
PAUSE = False
CHECK_SAFE_SCREEN = True


def downloader():
    return DUMMY

get_top_movies = downloader
get_trending_movies = downloader


def get_uuid_16(length=16):
    return uuid4().hex[:16]


def printer(data):
    print(data)


class WorkerThread(QtCore.QThread):

    def __init__(self, func, parent=None, *args, **kwargs):
        super(WorkerThread, self).__init__(parent)
        self.func = func
        self.args = args
        self.kwargs = kwargs


class DownloadThread(WorkerThread):
    job_done = QtCore.pyqtSignal(object, 'QString')

    def run(self):
        data = self.func()
        dtype = self.kwargs.get('dtype', '-')
        self.job_done.emit(data, dtype)


class ConnectionThread(QtCore.QThread):
    signal = QtCore.pyqtSignal(bool)

    def __init__(self, parent=None):
        super(ConnectionThread, self).__init__(parent)

    def run(self):
        cfm = False
        while True:
            try:
                requests.get("https://api.myip.com/")
                cfm = True
            except requests.exceptions.ConnectionError:
                cfm = False
            self.signal.emit(cfm)
            time.sleep(CONNECT_CHECK_INTERVAL)


class MemCache:

    _mem = {}

    @classmethod
    def update(self, data):
        MemCache._mem.update(data)

    @classmethod
    def get(self, key, default=None):
        return MemCache._mem.get(key, default)


class KeepAlive(WorkerThread):

    signal = QtCore.pyqtSignal(object)

    def __init__(self, func, connector, interval=0.1, parent=None, *args, **kwargs):
        super(KeepAlive, self).__init__(func, parent, *args, **kwargs)
        self._interval = interval
        self.connector = connector
        self._id = get_uuid_16()
        self._break = False

    def run(self):
        self._last_check = now = datetime.now()

        if now >= now + timedelta(seconds=self._interval):
            data = self.func()
            self.signal.emit(data)

        if not self._break:
            ka = KeepAlive(self.func, self._interval, self.parent, *self.args, **self.kwargs)
            ka.signal.connect(self.connector)
            ka.start()


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
        'dtype',
        'type',
        'se',
        'le',
        'time',
        'size',
        '?',
    ]

    thread_safe_func = {
        'thrending': get_trending_movies,
        'top': get_top_movies,
    }

    def __init__(self):
        super().__init__()
        self._data = DUMMY if DEBUG else []
        self.setWindowTitle("Trending/Top Torrent")

        # download thread
        self.threads = [DownloadThread(func, dtype=dtype) for dtype, func in self.thread_safe_func.items()]
        for thread in self.threads: thread.job_done.connect(self.update_screen)

        # connection check threads
        self.connection_thread = ConnectionThread()
        self.connection_thread.signal.connect(self.update_connection_status)

        self.initUI()

    def initUI(self):
        self.central_widgets = QWidget()
        self.UIComponents()

    def update_connection_status(self, has_connection):
        if not has_connection:
            self.connection.setStyleSheet("background-color: red")

        if has_connection:
            self.connection.setStyleSheet("background-color: green")

    def UIComponents(self):
        # choice the one

        # refresh button
        eye_connect = qta.icon('fa5.eye')
        self.connection = QPushButton(eye_connect, "")
        self.connection.setStyleSheet("background-color: blue")
        self.connection.setToolTip("Internet Connection")
        self.counter_label = QLabel(COUNT_LABEL % 0)
        refresh = qta.icon('fa5.arrow-alt-circle-down')
        refresh_button = QPushButton(refresh, "Refresh")
        refresh_button.clicked.connect(self.refresh)

        # progress widget
        self.progress = QMovieLabel('img/loading.gif')
        self.progress.setAlignment(Qt.AlignCenter)

        # main contents
        self.content = QTableWidget()
        self.content.setColumnCount(len(self.headers))
        self.content.verticalHeader().setVisible(False)
        self.content.setHorizontalHeaderLabels(self.headers)
        self.content.resizeColumnsToContents()
        self.content.hide()

        top_content_layout = QVBoxLayout()
        top_content_layout.addWidget(self.progress)
        top_content_layout.addWidget(self.content)

        bottom_button_layout = QHBoxLayout()
        bottom_button_layout.addStretch(1)
        bottom_button_layout.addWidget(self.counter_label)
        bottom_button_layout.addWidget(self.connection)
        bottom_button_layout.addWidget(refresh_button)

        main_box_layout = QVBoxLayout()
        main_box_layout.addLayout(top_content_layout, 1)
        main_box_layout.addLayout(bottom_button_layout, 2)

        self.central_widgets.setLayout(main_box_layout)
        self.setCentralWidget(self.central_widgets)

        # lets download the data
        self.refresh()

    # refresh the current window
    def refresh(self):
        self.content.hide()
        self.progress.show()
        for thread in self.threads:
            thread.start()

        # connection button check
        self.connection_thread.start()

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

    def _clear_table(self, **kwargs):
        if kwargs.get('force', False):
            while self.content.rowCount() > 0:
                self.content.removeRow(0)
        if kwargs.get('dtype') and kwargs.get('previous_rows'):
            previous_rows = kwargs['previous_rows']
            for index in range(*previous_rows):
                self.content.removeRow(index)

    def _update_counter_label(self, count):
        label = str(COUNT_LABEL % count)
        self.counter_label.setText(label)

    def update_screen(self, data, dtype):
        if not data: return

        # remove any previous data related to the dtype
        mem_cache_key = '{}:{}'.format(dtype, data[0].get('type'))
        previous_rows = MemCache.get(mem_cache_key, default=(0, 0))
        self._clear_table(dtype=dtype, previous_rows=previous_rows)

        previous_count = self.content.rowCount()
        data_count = len(data)
        print(data_count, mem_cache_key, previous_rows)

        # set the current dtype indexs
        max_length = previous_count + data_count
        MemCache.update({mem_cache_key: (previous_count, max_length)})

        self.content.setRowCount(max_length)
        for i, item in enumerate(data):
            item.update({'dtype': dtype})
            self.update_row(previous_count + i, item)

        self._update_counter_label(max_length)

        self.content.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        self.content.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.progress.hide()
        self.content.show()


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


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Window()
    if DEBUG: window.show()
    sys.exit(app.exec_())
