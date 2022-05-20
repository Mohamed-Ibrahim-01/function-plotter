import sys
import qdarktheme
from Plotter import Plotter
from PyQt5 import QtWidgets as qtw
from PyQt5 import uic


class MainApp(qtw.QApplication):
    """The main application object"""

    def __init__(self, argv):
        super().__init__(argv)

        self.main_window = MainWindow()
        self.main_window.setStyleSheet(qdarktheme.load_stylesheet())
        self.main_window.show()


class MainWindow(qtw.QMainWindow):
    """The main application window"""

    def __init__(self):
        super().__init__()
        uic.loadUi("src/main.ui", self)
        self.initBody()

    def initBody(self):
        self.centralWidget().setLayout(qtw.QVBoxLayout())
        self.central_layout = self.centralWidget().layout()

        self.plotter = Plotter()
        self.central_layout.addWidget(self.plotter)


if __name__ == '__main__':
    app = MainApp(sys.argv)
    sys.exit(app.exec_())
