from PyQt5 import QtCore
import requests
import time

CONNECT_CHECK_INTERVAL = 3600


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
