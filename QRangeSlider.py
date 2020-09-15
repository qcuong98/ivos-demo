from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

import sys


class QRangeSlider(QWidget):
    valueChanged = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.positions = [1, 5, 8]

        self.opt = QStyleOptionSlider()
        self.opt.minimum = 0
        self.opt.maximum = 10

        self.setTickPosition(QSlider.TicksAbove)
        self.setTickInterval(1)

        self.setSizePolicy(
            QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed, QSizePolicy.Slider)
        )

    def setRangeLimit(self, minimum: int, maximum: int):
        self.opt.minimum = minimum
        self.opt.maximum = maximum

    def setRange(self, start: int, end: int):
        self.positions[0] = start
        self.positions[-1] = end
        self.update()

    def getRange(self):
        return (self.positions[0], self.positions[-1])

    def setValue(self, value):
        self.positions[1] = value
        self.update()

    def getValue(self):
        return self.positions[1]

    def setTickPosition(self, position: QSlider.TickPosition):
        self.opt.tickPosition = position

    def setTickInterval(self, ti: int):
        self.opt.tickInterval = ti

    def paintEvent(self, event: QPaintEvent):

        painter = QPainter(self)

        # Draw rule
        self.opt.initFrom(self)
        self.opt.rect = self.rect()
        self.opt.sliderPosition = 0
        self.opt.subControls = QStyle.SC_SliderGroove | QStyle.SC_SliderTickmarks

        #   Draw GROOVE
        self.style().drawComplexControl(QStyle.CC_Slider, self.opt, painter)

        #  Draw INTERVAL

        color = self.palette().color(QPalette.Highlight)
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.NoPen)

        self.opt.sliderPosition = self.positions[0]
        x_left_handle = (
            self.style()
            .subControlRect(QStyle.CC_Slider, self.opt, QStyle.SC_SliderHandle)
            .right()
        )

        self.opt.sliderPosition = self.positions[-1]
        x_right_handle = (
            self.style()
            .subControlRect(QStyle.CC_Slider, self.opt, QStyle.SC_SliderHandle)
            .left()
        )

        groove_rect = self.style().subControlRect(
            QStyle.CC_Slider, self.opt, QStyle.SC_SliderGroove
        )

        selection = QRect(
            x_left_handle,
            groove_rect.y(),
            x_right_handle - x_left_handle,
            groove_rect.height(),
        ).adjusted(-1, 1, 1, -1)

        painter.drawRect(selection)

        self.opt.subControls = QStyle.SC_SliderHandle
        for i, position in enumerate(self.positions):
            self.opt.sliderPosition = position
            self.style().drawComplexControl(QStyle.CC_Slider, self.opt, painter)

    def mousePressEvent(self, event: QMouseEvent):
        self._sc = []
        for position in self.positions:
            self.opt.sliderPosition = position
            self._sc.append(self.style().hitTestComplexControl(
                QStyle.CC_Slider, self.opt, event.pos(), self
            ))

    def mouseMoveEvent(self, event: QMouseEvent):
        pos = self.style().sliderValueFromPosition(
            self.opt.minimum, self.opt.maximum, event.pos().x(), self.rect().width()
        )

        list_handles = []
        for i in range(len(self.positions)):
            if self._sc[i] == QStyle.SC_SliderHandle:
                list_handles.append(i)

        tmp = self.positions[:]

        if len(list_handles) > 0:
            left_handle = list_handles[0]
            right_handle = list_handles[-1]

            if pos < self.positions[left_handle]: # move left
                if left_handle == 0 or self.positions[left_handle - 1] <= pos: 
                    self.positions[left_handle] = pos
                    self.update()
            elif pos > self.positions[right_handle]: # move right
                if right_handle == len(self.positions) -1 or pos <= self.positions[right_handle + 1]:
                    self.positions[right_handle] = pos
                    self.update()
            
        if self.positions != tmp:
            self.valueChanged.emit()

    def sizeHint(self):
        """ override """
        SliderLength = 84
        TickSpace = 5

        w = SliderLength
        h = self.style().pixelMetric(QStyle.PM_SliderThickness, self.opt, self)

        if (
            self.opt.tickPosition & QSlider.TicksAbove
            or self.opt.tickPosition & QSlider.TicksBelow
        ):
            h += TickSpace

        return (
            self.style()
            .sizeFromContents(QStyle.CT_Slider, self.opt, QSize(w, h), self)
            .expandedTo(QApplication.globalStrut())
        )


if __name__ == "__main__":

    app = QApplication(sys.argv)

    w = QRangeSlider()
    w.show()

    app.exec_()