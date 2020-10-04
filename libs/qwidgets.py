from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore


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


class TableContentWidget(QtWidgets.QTableWidget):

    def __init__(self, parent=None):
        super(TableContentWidget, self).__init__()
        self.parent = parent

    def keyPressEvent(self, event):
        # pretttty close both keys
        if event.key() in (QtCore.Qt.Key_Shift, QtCore.Qt.Key_Return) and self.currentRow() >= 0:
            self.parent.goto('details')
        else:
            super().keyPressEvent(event)
