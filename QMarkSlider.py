from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

import sys


class QMarkSlider(QWidget):
    valueChanged = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.opt = QStyleOptionSlider()
        self.setSizePolicy(
            QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed, QSizePolicy.Slider)
        )

    def setRangeLimit(self, minimum: int, maximum: int):
        self.opt.minimum = minimum
        self.opt.maximum = maximum
        self.mark = [False for i in range(maximum - minimum + 1)]

    def addMarkInterval(self, left, right):
        for x in range(left, right + 1):
            self.mark[x] = True
        self.repaint()

    def getMaximumRange(self):
        left, right = self.opt.minimum, self.opt.maximum
        minv, maxv = left, right
        for x in range(left, right + 1):
            if not self.mark[x]:
                minv = x
                break
        for x in range(right, left - 1, -1):
            if not self.mark[x]:
                maxv = x
                break
        return minv, maxv

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        color = self.palette().color(QPalette.Dark)
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.NoPen)

        # Draw rule
        self.opt.initFrom(self)
        self.opt.rect = self.rect()
        self.opt.sliderPosition = 0
        self.opt.subControls = QStyle.SC_SliderGroove

        # Draw GROOVE
        self.drawRectangle(painter, self.opt.minimum, self.opt.maximum)

        # Draw INTERVAL

        first_mark = -1
        painter.setBrush(QColor(0, 127, 0, 160))
        for i in range(len(self.mark)):
            if self.mark[i]:
                if i == 0 or self.mark[i - 1] == False:
                    first_mark = i
                if i == len(self.mark) - 1 or self.mark[i + 1] == False:
                    self.drawRectangle(painter, first_mark, i)

    def drawRectangle(self, painter, left, right):
        self.opt.sliderPosition = left
        x_left_handle = (
            self.style()
            .subControlRect(QStyle.CC_Slider, self.opt, QStyle.SC_SliderHandle)
            .left()
        )
        self.opt.sliderPosition = right
        x_right_handle = (
            self.style()
            .subControlRect(QStyle.CC_Slider, self.opt, QStyle.SC_SliderHandle)
            .right()
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

    w = QMarkSlider()
    w.setRangeLimit(0, 10 - 1)
    w.show()

    app.exec_()