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
    QListWidget,
)

from PyQt5.QtGui import (
    QFont,
    QPixmap,
)

from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore

from PyQt5.QtCore import QEvent, Qt
from libs.torrent import (
    get_top_movies,
    get_trending_movies,
    get_details,
)
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
WIDTH = 350
HEIGHT = 450
SIZE = (WIDTH, HEIGHT)


def get_uuid_16(length=16):
    return uuid4().hex[:16]


def set_to_bottom_right_corner(self):
    ag = QDesktopWidget().availableGeometry()
    # sg = QDesktopWidget().screenGeometry()
    x = ag.width()
    y = ag.height()
    self.move(x, y)


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


class DetailDownloadThread(WorkerThread):
    job_done = QtCore.pyqtSignal(object)

    def run(self):
        url = self.kwargs['url']
        data = self.func(url)
        self.job_done.emit(data)


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


class ContentDetailsWindow(WidgetWindow):
    windowName = 'details'

    def __init__(self, parent=None):
        super(WidgetWindow, self).__init__(parent)
        self.parent = parent
        self.central_widgets = QWidget()
        self._self_url = None
        self.initUI()

    def initUI(self):
        self.UIComponents()

    def UIComponents(self):
        # contentents details
        self.image_label = QLabel(self)
        pixmap = QPixmap('img/icon.jpg')
        self.image_label.setPixmap(pixmap)

        # top text details
        text_details = QVBoxLayout()
        self.name_label = QLabel()
        self.se_le = QLabel()
        self.keywords = QLabel()
        self.downloads = QLabel()
        self.languages = QLabel()
        self.category = QLabel()
        self.types = QLabel()

        text_details.addWidget(self.name_label)
        text_details.addWidget(self.keywords)
        text_details.addWidget(self.category)
        text_details.addWidget(self.se_le)
        text_details.addWidget(self.downloads)
        text_details.addWidget(self.languages)
        text_details.addWidget(self.types)

        top_content_layout = QHBoxLayout()
        top_content_layout.addWidget(self.image_label)
        top_content_layout.addLayout(text_details)
        text_details.addStretch(1)

        # content related list
        self.lists = QListWidget()

        # main bottom lines
        back_icon = qta.icon('fa5.arrow-alt-circle-left')
        self.back_button = QPushButton(back_icon, "")
        self.back_button.clicked.connect(lambda: self.goto('main'))

        copy_icon = qta.icon('fa5.copy')
        self.copy_magnet = QPushButton(copy_icon, "")
        self.copy_magnet.clicked.connect(self.copy_magnet_url)
        open_icon = qta.icon('fa5s.external-link-square-alt')
        self.open_button = QPushButton(open_icon, "")

        bottom_button_layout = QHBoxLayout()
        bottom_button_layout.addWidget(self.back_button)
        bottom_button_layout.addStretch(1)
        bottom_button_layout.addWidget(self.copy_magnet)
        bottom_button_layout.addWidget(self.open_button)

        main_box_layout = QVBoxLayout()
        main_box_layout.addLayout(top_content_layout, 1)
        main_box_layout.addWidget(self.lists, 2)
        main_box_layout.addLayout(bottom_button_layout, 3)
        self.central_widgets.setLayout(main_box_layout)
        self.setCentralWidget(self.central_widgets)

    def keyPressEvent(self, event):
        if event.key() in (QtCore.Qt.Key_Backspace, QtCore.Qt.Key_Escape):
            self.goto('main')
        else:
            super().keyPressEvent(event)

    def copy_magnet_url(self):
        cb = QApplication.clipboard()
        cb.clear(mode=cb.Clipboard)
        cb.setText('get_copy magent url', mode=cb.Clipboard)

    @property
    def current_row_content_url(self):
        row = self.parent.content.currentRow()
        row_u = self.parent.content.item(row, 7)
        row_u = row_u.text() if row_u else None
        return self._self_url or row_u

    def _update_title(self, name, size):
        FORMAT = "<u><b>{} ({})</b></u>".format(name, size)
        self.name_label.setText(FORMAT)

    def _update_keywords(self, keywords):
        if not keywords: keywords = []
        form = '<b style="color: green;">{}</b>'
        FORMAT = [form.format(key) for key in keywords]
        self.keywords.setText(' '.join(FORMAT))

    def _update_se_le(self, se, le):
        FORMAT = 'SE/LE: <b style="color: green;">{}</b>/<b style="color: red;">{}</b>'
        self.se_le.setText(FORMAT)

    def _update_downloads(self, count):
        FORMAT = 'DOWNLOADS: <b style="color: green;">{}</b>'.format(count)
        self.downloads.setText(FORMAT)

    def _update_language(self, lang):
        FORMAT = 'LANGUAGES: {}'.format(lang.title())
        self.languages.setText(FORMAT)

    def _update_category(self, category):
        FORMAT = 'CATEGORY: {}'.format(category)
        self.category.setText(FORMAT)

    def _update_types(self, types):
        FORMAT = 'TYPE: {}'.format(types)
        self.types.setText(FORMAT)

    def update_screen(self, data):
        self._update_title(
            data.get('name'), data.get('size')
        )
        self._update_category(data.get('category'))
        self._update_downloads(data.get('downloads'))
        self._update_language(data.get('languages', '-'))
        self._update_keywords(data.get('keywords'))
        self._update_keywords(data.get('keywords'))

    def on_load(self, **kwargs):
        print(kwargs, self.current_row_content_url)
        self.download_details_thread = DetailDownloadThread(get_details, url=self.current_row_content_url)
        self.download_details_thread.job_done.connect(self.update_screen)
        self.download_details_thread.start()


class TableContentWidget(QTableWidget):

    def __init__(self, parent=None):
        super(TableContentWidget, self).__init__()
        self.parent = parent

    def keyPressEvent(self, event):
        # pretttty close both keys
        if event.key() in (QtCore.Qt.Key_Shift, QtCore.Qt.Key_Return):
            self.parent.goto('details')
        else:
            super().keyPressEvent(event)


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
        'url',
    ]

    thread_safe_func = {
        'thrending': get_trending_movies,
        'top': get_top_movies,
    }

    def __init__(self, parent=None):
        super().__init__(parent)

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
        refresh = qta.icon('fa5s.sync-alt')
        refresh_button = QPushButton(refresh, "")
        refresh_button.clicked.connect(self.refresh)

        # progress widget
        self.progress = QMovieLabel('img/loading.gif')
        self.progress.setAlignment(Qt.AlignCenter)

        # main contents
        self.content = TableContentWidget(self)
        self.content.setColumnCount(len(self.headers))
        self.content.verticalHeader().setVisible(False)
        self.content.setHorizontalHeaderLabels(self.headers)
        self.content.resizeColumnsToContents()
        self.content.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        self.content.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
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
        self.turn_on_progress()
        for thread in self.threads:
            thread.start()

        # connection button check
        self.connection_thread.start()

    def update_row(self, cell_no, data):
        for index, key in enumerate(self.headers):
            self.content.setItem(
                cell_no,
                index,
                QTableWidgetItem(
                    data.get(key, '-')
                )
            )

    def _clear_table(self, **kwargs):
        if kwargs.get('force', False):
            while self.content.rowCount() > 0:
                self.content.removeRow(0)

        if kwargs.get('dtype'):
            count = self.content.rowCount()
            dtype = kwargs['dtype']
            while count >= 0:
                value = self.content.item(count, 1)
                if value and value.text() == dtype:
                    self.content.removeRow(count)
                    count = self.content.rowCount()
                count -= 1

    def update_counter_label(self):
        label = str(COUNT_LABEL % self.content.rowCount())
        self.counter_label.setText(label)

    def update_screen(self, data, dtype):
        if not data:
            self.turn_off_progress()
            return

        self._clear_table(dtype=dtype)

        previous_count = self.content.rowCount()
        data_count = len(data)

        # set the current dtype indexs
        max_length = previous_count + data_count

        self.content.setRowCount(max_length)
        for i, item in enumerate(data):
            item.update({'dtype': dtype})
            self.update_row(previous_count + i, item)

        self.update_counter_label()

        self.turn_off_progress()

    def turn_on_progress(self):
        self.content.hide()
        self.progress.show()

    def turn_off_progress(self):
        self.progress.hide()
        self.content.show()


class Window(QMainWindow):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.stacked_widget = QtWidgets.QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        self.setWindowTitle("Trending/Top Torrent")
        self.frames = {}

        self.setFixedSize(*SIZE)
        self.set_to_bottom_right_corner()

        self.tray_icon = SystemTrayIcon(QtGui.QIcon('img/tray.png'), self)
        self.tray_icon.show()

        # system app setup
        self.setWindowFlag(Qt.WindowMinimizeButtonHint, False)
        self.setFont(QFont('Courier', 9))

        # register all widgets
        self.register(MainWindow(self))
        self.register(ContentDetailsWindow(self))

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
            if name == 'details': widget.on_load()
            self.stacked_widget.setCurrentWidget(widget)

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

    @property
    def content(self):
        return self.frames['main'].content


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Window()
    if DEBUG: window.show()
    sys.exit(app.exec_())
