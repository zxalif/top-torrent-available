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
        if event.key() in (QtCore.Qt.Key_Shift, QtCore.Qt.Key_Return):
            self.parent.goto('details')
        else:
            super().keyPressEvent(event)


class RelatedListWidget(QtWidgets.QListWidget):
    def __init__(self, parent=None, widget=None):
        super(RelatedListWidget, self).__init__()
        self.parent = parent
        self._widget = widget
        self.data = []

    def keyPressEvent(self, event):
        # pretttty close both keys
        if event.key() in (QtCore.Qt.Key_Shift, QtCore.Qt.Key_Return) and self.data and self._widget:
            row = self.currentRow()
            _data = self.data[row]
            widget = self._widget(self_url=_data.get('url'))
            widget.on_load()
            widget.show()
        else:
            super().keyPressEvent(event)
