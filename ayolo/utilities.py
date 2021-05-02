
from PyQt5 import QtWidgets, QtCore, QtGui


class PropagableLineEdit(QtWidgets.QLineEdit):
    '''Whatever ... just trying to make shortcuts propagable when focus is on QLineEdit'''

    def eventFilter(self, source, event):
        modifiers = QtWidgets.QApplication.keyboardModifiers()
        if event.type() == QtGui.QKeyEvent and modifiers == QtCore.Qt.KeyboardModifier.ControlModifier or event.type() == QtGui.QWheelEvent:
            return True
        return super().eventFilter(source, event)
