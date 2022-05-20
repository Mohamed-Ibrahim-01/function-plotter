import numpy as np
from PyQt5 import QtCore as qtc
from PyQt5 import QtWidgets as qtw
from PyQt5 import uic
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as navigation_toolbar
from superqt import QLabeledSlider
from py_expression_eval import Parser

plt.style.use('dark_background')


class Plotter(qtw.QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi("src/plotter.ui", self)
        self.equation_parser = Parser()
        self.plotting_canvas = PlottingCanvas()

        """Get children of plotter from the loaded UI """
        self.plotter_layout = self.findChild(qtw.QVBoxLayout, "plotter_layout")
        self.min_range_layout = self.findChild(qtw.QHBoxLayout, "min_range")
        self.max_range_layout = self.findChild(qtw.QHBoxLayout, "max_range")
        self.equation_input = self.findChild(qtw.QLineEdit, "equation_input")
        self.plot_button = self.findChild(qtw.QPushButton, "plot_btn")
        self.min_slider_limit = self.findChild(qtw.QSpinBox, "min_limit")
        self.max_slider_limit = self.findChild(qtw.QSpinBox, "max_limit")
        self.update_limits = self.findChild(qtw.QPushButton, "update_limits")
        self.plotting_resolution = self.findChild(qtw.QSpinBox, "resolution")

        """Complete the UI components"""
        self.toolbar = navigation_toolbar(self.plotting_canvas, self)

        self.min_range_slider = QLabeledSlider()
        self.min_range_slider.setRange(-50, 50)
        self.min_range_slider.setValue(-50)
        self.min_range_slider.setOrientation(qtc.Qt.Orientation.Horizontal)

        self.max_range_slider = QLabeledSlider()
        self.max_range_slider.setRange(-50, 50)
        self.max_range_slider.setValue(50)
        self.max_range_slider.setOrientation(qtc.Qt.Orientation.Horizontal)

        self.plotter_layout.insertWidget(0, self.plotting_canvas)
        self.plotter_layout.insertWidget(0, self.toolbar)
        self.min_range_layout.insertWidget(-1, self.min_range_slider)
        self.max_range_layout.insertWidget(-1, self.max_range_slider)

        """Signals and Slots connections"""
        self.plot_button.clicked.connect(self.plotEquation)
        self.update_limits.clicked.connect(self.updateSlidersRanges)

        self.equation_input.textChanged.connect(self.interactivePlot)
        self.min_range_slider.valueChanged.connect(self.interactivePlot)
        self.max_range_slider.valueChanged.connect(self.interactivePlot)
        self.plotting_resolution.valueChanged.connect(self.interactivePlot)

        self.min_range_slider._slider.sliderReleased.connect(self.SliderMovement)
        self.max_range_slider._slider.sliderReleased.connect(self.SliderMovement)

    @qtc.pyqtSlot()
    def plotEquation(self):
        plotting_params = self.getEquationParams()
        x_values, y_values, independent_variable = self.evaluateEquation(*plotting_params)
        if len(x_values) in {0, 1}:
            return

        equation = self.equation_input.displayText()
        self.plotting_canvas.plot(x_values, y_values, independent_variable, equation)

    @qtc.pyqtSlot()
    def interactivePlot(self):
        if not self.interactive.isChecked():
            return
        equation = self.equation_input.displayText()
        if self.validateEquation(equation)[0]:
            self.setStyleSheet("QLineEdit#equation_input { color:  }")
            self.plotEquation()
        else:
            self.invalidateEquationText()

    def invalidateEquationText(self):
        self.setStyleSheet("QLineEdit#equation_input { color: #e02c2c; font-weight: bold; }")

    @qtc.pyqtSlot()
    def SliderMovement(self):
        min_input = self.min_range_slider.value()
        max_input = self.max_range_slider.value()
        if min_input >= max_input:
            qtw.QMessageBox.warning(self, "Invalid Input", "Min limit cannot exceed max")
            self.resetSliders()

    @qtc.pyqtSlot()
    def updateSlidersRanges(self):
        min_limit = self.min_slider_limit.value()
        max_limit = self.max_slider_limit.value()
        if min_limit >= max_limit:
            qtw.QMessageBox.warning(self, "Invalid Input", "Min limit cannot exceed max")
            return
        self.min_range_slider.setRange(min_limit, max_limit)
        self.max_range_slider.setRange(min_limit, max_limit)
        self.resetSliders()

    def resetSliders(self):
        min_limit = self.min_slider_limit.value()
        max_limit = self.max_slider_limit.value()
        self.min_range_slider.setValue(min_limit)
        self.max_range_slider.setValue(max_limit)

    def evaluateEquation(self, equation, min_input, max_input):
        resolution = self.plotting_resolution.value()
        number_of_points = (max_input - min_input + 1) * resolution
        if number_of_points <= 0:
            return [], [], "x"
        input_range = np.linspace(min_input, max_input, number_of_points)
        parsed_equation = self.parseEquation(equation)

        def substitute_dict(x):
            return {} if no_variables else {independent_variables[0]: x}

        if parsed_equation:
            try:
                independent_variables = parsed_equation.variables()
                no_variables = len(independent_variables) == 0
                evaluated = [parsed_equation.evaluate(substitute_dict(s)) for s in input_range]
                if all(isinstance(sub, type(evaluated[0])) and not callable(sub) for sub in evaluated):
                    return input_range, evaluated, "x" if no_variables else independent_variables[0]
            except Exception:
                self.invalidateEquationText()
                qtw.QMessageBox.warning(self, "Invalid Input", "Check your range or Equation")
        return [], [], "x"

    def validateEquation(self, equation):
        if not equation or "()" in equation:
            return False, "Empty equation", ""
        try:
            parsed_equation = self.equation_parser.parse(equation)
            if len(parsed_equation.variables()) > 1:
                return False, f"Only one variable is supported but {parsed_equation.variables()} given", ""
        except Exception as e:
            return False, str(e), ""
        return True, "Valid", parsed_equation

    def parseEquation(self, equation):
        valid, err_msg, parsed_equation = self.validateEquation(equation)
        if not valid:
            qtw.QMessageBox.warning(self, "Invalid Equation", err_msg)
        return parsed_equation

    def getEquationParams(self):
        equation_text = self.equation_input.displayText()
        min_input = self.min_range_slider.value()
        max_input = self.max_range_slider.value()
        return equation_text, min_input, max_input


class PlottingCanvas(FigureCanvas):

    def __init__(self):
        self.fig = Figure(figsize=(10, 10))
        self.fig.canvas.toolbar_visible = True
        self.axes = self.fig.add_subplot(111)

        for spine in ['right', 'top', 'left', 'bottom']:
            self.axes.spines[spine].set_color('gray')
        super().__init__(self.fig)

    def plot(self, x_values, y_values, independent_variable, equation):
        self.clear()
        self.axes.set_title(f"${equation}$")
        self.axes.set_xlabel(independent_variable)
        self.axes.set_ylabel(f"F({independent_variable})")
        self.axes.plot(x_values, y_values, '-')
        self.draw()

    def clear(self):
        self.axes.clear()
        self.draw()
