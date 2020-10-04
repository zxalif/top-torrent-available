from PyQt5 import QtWidgets
from PyQt5 import QtCore


class SystemTrayIcon(QtWidgets.QSystemTrayIcon):

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
        # fix for windows bring back
        self.parent.setWindowFlag(QtCore.Qt.WindowStaysOnTopHint)
        self.parent.setFocus(True)
        self.parent.show()
        self.parent.raise_()
        self.parent.activateWindow()

    def closeVisibleWindow(self):

        qm = QtWidgets.QMessageBox
        ret = qm.question(self.parent,
                          '?', "Are you sure, you want to exist?", qm.Yes | qm.No)
        if ret != qm.No:
            self.parent.fromTray = True
            self.parent.close()
