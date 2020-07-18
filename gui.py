import sys
from PyQt5.QtWidgets import (QWidget, QApplication, QMainWindow, QComboBox,
                             QDialog, QDialogButtonBox, QFormLayout,
                             QGridLayout, QGroupBox, QHBoxLayout, QLabel,
                             QLineEdit, QMenu, QMenuBar, QPushButton, QSpinBox,
                             QTextEdit, QVBoxLayout, QMessageBox, QAction,
                             QInputDialog, QColorDialog, QSizePolicy, QSlider,
                             QLCDNumber, QSpinBox)

from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor, QPen
from PyQt5.QtCore import pyqtSlot, QTimer
from PyQt5.QtCore import Qt
from PyQt5 import QtCore

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

import argparse
import cv2
import matplotlib.pyplot as plt
from PIL import Image
import numpy as np
import math
import time
import os
import copy
import random
import uuid
import shutil
import glob

from model import model
from utils import pascal_color_map, load_frames, overlay_davis, overlay_checker, overlay_color, overlay_fade


class App(QWidget):
    def __init__(self, sequence, n_objects, memory_size, fbrs_gpu, stm_gpu):
        super().__init__()

        self.session_id = uuid.uuid1().hex
        print(f'Sesssion ID: {self.session_id}')

        self.sequence = sequence
        self.n_objects = n_objects
        self.memory_size = memory_size
        self.frames = load_frames(self.sequence)
        self.num_frames, self.height, self.width = self.frames.shape[:3]
        # init model
        self.model = model(self.frames, self.n_objects, self.memory_size, fbrs_gpu, stm_gpu)

        # get color map
        self.cmap = pascal_color_map(normalized=True)

        # set window
        self.setWindowTitle('[Demo] Interaction Video Object Segmentation')
        self.setGeometry(100, 100, self.width, self.height + 100)

        # buttons
        self.prev_button = QPushButton('Prev')
        self.prev_button.clicked.connect(self.on_prev)
        self.next_button = QPushButton('Next')
        self.next_button.clicked.connect(self.on_next)
        self.play_button = QPushButton('Play')
        self.play_button.clicked.connect(self.on_play)
        self.run_button = QPushButton('Propagate!')
        self.run_button.clicked.connect(self.on_run)
        self.visualize_button = QPushButton('Get Interactive Video')
        self.visualize_button.clicked.connect(self.on_visualize)

        # LCD
        self.lcd = QTextEdit()
        self.lcd.setReadOnly(True)
        self.lcd.setMaximumHeight(28)
        self.lcd.setMaximumWidth(100)
        self.lcd.setText('{: 3d} / {: 3d}'.format(0, self.num_frames - 1))

        # slide
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(self.num_frames - 1)
        self.slider.setValue(0)
        self.slider.setTickPosition(QSlider.TicksBelow)
        self.slider.setTickInterval(1)
        self.slider.valueChanged.connect(self.slide)

        # combobox
        self.overlay_combo = QComboBox(self)
        self.overlay_combo.addItem("fade")
        self.overlay_combo.addItem("davis")
        self.overlay_combo.addItem("checker")
        self.overlay_combo.addItem("color")
        self.overlay_combo.currentTextChanged.connect(self.set_viz_mode)

        # spinbox
        self.object_spin = QSpinBox(self)
        self.object_spin.setMinimum(1)
        self.object_spin.setValue(1)

        # canvas
        self.fig = plt.Figure()
        self.ax = plt.Axes(self.fig, [0., 0., 1., 1.])
        self.ax.set_axis_off()
        self.fig.add_axes(self.ax)

        self.canvas = FigureCanvas(self.fig)

        self.cidpress = self.fig.canvas.mpl_connect('button_press_event',
                                                    self.on_press)
        self.cidrelease = self.fig.canvas.mpl_connect('button_release_event',
                                                      self.on_release)
        self.cidmotion = self.fig.canvas.mpl_connect('motion_notify_event',
                                                     self.on_motion)

        # navigator
        navi = QHBoxLayout()
        navi.addWidget(self.lcd)
        navi.addWidget(self.prev_button)
        navi.addWidget(self.play_button)
        navi.addWidget(self.next_button)
        navi.addStretch(1)
        navi.addWidget(QLabel('Overlay Mode'))
        navi.addWidget(self.overlay_combo)
        navi.addStretch(1)
        navi.addWidget(QLabel('Object Strokes'))
        navi.addWidget(self.object_spin)
        navi.addStretch(1)
        navi.addWidget(self.run_button)
        navi.addStretch(1)
        navi.addWidget(self.visualize_button)

        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        layout.addWidget(self.slider)
        layout.addLayout(navi)
        layout.setStretchFactor(navi, 1)
        layout.setStretchFactor(self.canvas, 0)
        self.setLayout(layout)

        # timer
        self.timer = QTimer()
        self.timer.setSingleShot(False)
        self.timer.timeout.connect(self.on_time)

        # initialize visualize
        self.viz_mode = 'fade'
        self.cursur = 0
        self.on_showing = None
        self.show_current()

        # initialize action
        self.reset_scribbles()
        self.pressed = False
        self.on_drawing = None
        self.drawn_strokes = []

        self.show()

    def show_current(self):
        if self.viz_mode == 'fade':
            viz = overlay_fade(self.frames[self.cursur],
                               self.model.current_masks[self.cursur])
        elif self.viz_mode == 'davis':
            viz = overlay_davis(self.frames[self.cursur],
                                self.model.current_masks[self.cursur],
                                rgb=[0, 0, 128])
        elif self.viz_mode == 'checker':
            viz = overlay_checker(self.frames[self.cursur],
                                  self.model.current_masks[self.cursur])
        elif self.viz_mode == 'color':
            viz = overlay_color(self.frames[self.cursur],
                                self.model.current_masks[self.cursur],
                                rgb=[223, 0, 223])
        else:
            raise NotImplementedError

        if self.on_showing:
            self.on_showing.remove()
        self.on_showing = self.ax.imshow(viz)
        self.canvas.draw()
        self.lcd.setText('{: 3d} / {: 3d}'.format(self.cursur,
                                                  self.num_frames - 1))
        self.slider.setValue(self.cursur)

    def reset_scribbles(self):
        self.scribbles = {}
        self.scribbles['scribbles'] = [[] for _ in range(self.num_frames)]
        self.scribbles['sequence'] = self.sequence

    def clear_strokes(self):
        # clear drawn scribbles
        if len(self.drawn_strokes) > 0:
            for line in self.drawn_strokes:
                line.pop(0).remove()
            self.drawn_strokes = []
            self.canvas.draw()

    def set_viz_mode(self):
        self.viz_mode = self.overlay_combo.currentText()
        self.show_current()

    def slide(self):
        self.clear_strokes()
        self.reset_scribbles()
        self.cursur = self.slider.value()
        self.show_current()
        # print('slide')

    def on_run(self):
        self.model.run_propagation()
        # clear scribble and reset
        self.show_current()
        self.reset_scribbles()
        self.clear_strokes()

    def on_visualize(self):
        frames_dir = os.path.join('visualized', self.session_id, 'frames')
        masks_dir = os.path.join('visualized', self.session_id, 'masks')

        if not os.path.isdir(frames_dir):
            os.makedirs(frames_dir)
            fnames = glob.glob(os.path.join(self.sequence, '*.jpg'))
            fnames.sort()
            for i, fname in enumerate(fnames):
                frame_ext = os.path.splitext(fname)[1]
                shutil.copy2(fname, os.path.join(frames_dir, f'{i:06}{frame_ext}'))

        if not os.path.isdir(masks_dir):
            os.makedirs(masks_dir)
        for i, mask in enumerate(self.model.current_masks):
            Image.fromarray(mask).save(os.path.join(masks_dir, f'{i:06}.png'))

    def on_prev(self):
        self.clear_strokes()
        self.reset_scribbles()
        self.cursur = max(0, self.cursur - 1)
        self.show_current()
        # print('prev')

    def on_next(self):
        self.clear_strokes()
        self.reset_scribbles()
        self.cursur = min(self.cursur + 1, self.num_frames - 1)
        self.show_current()
        # print('next ')

    def on_time(self):
        self.clear_strokes()
        self.reset_scribbles()
        self.cursur += 1
        if self.cursur > self.num_frames - 1:
            self.cursur = 0
        self.show_current()

    def on_play(self):
        if self.timer.isActive():
            self.timer.stop()
        else:
            self.timer.start(1000 / 10)

    def on_press(self, event):
        if event.xdata and event.ydata:
            self.pressed = True
            self.stroke = {}
            self.stroke['path'] = []
            self.stroke['path'].append(
                [event.xdata / self.width, event.ydata / self.height])
            if event.button == Qt.LeftButton:
                self.stroke['object_id'] = self.object_spin.value()
            else:
                self.stroke['object_id'] = 0
            self.stroke['start_time'] = time.time()

    def on_motion(self, event):
        if self.pressed and event.xdata and event.ydata:
            self.stroke['path'].append(
                [event.xdata / self.width, event.ydata / self.height])

            x = [p[0] * self.width for p in self.stroke['path']]
            y = [p[1] * self.height for p in self.stroke['path']]
            if self.on_drawing:
                self.on_drawing.pop(0).remove()

            color = self.cmap[self.stroke['object_id']].tolist()
            self.on_drawing = self.ax.plot(x, y, linewidth=5, color=color)
            self.canvas.draw()

    def on_release(self, event):
        self.pressed = False
        if event.xdata and event.ydata:
            self.stroke['path'].append(
                [event.xdata / self.width, event.ydata / self.height])

        self.stroke['end_time'] = time.time()
        self.scribbles['annotated_frame'] = self.cursur

        self.scribbles['scribbles'][self.cursur].append(self.stroke)

        self.drawn_strokes.append(self.on_drawing)
        self.on_drawing = None

        self.model.run_interaction(self.scribbles)
        self.show_current()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="args")
    parser.add_argument("--seq", type=str, help='video sequence directory', required=True)
    parser.add_argument("--nobjects", type=int, help='number of objects', default=5)
    parser.add_argument("--mem", type=int, help='memory size of memory-based model', default=5)
    parser.add_argument("--gpus", nargs='+', type=int, help='gpu ids need for modules', default=[0])
    args = parser.parse_args()

    fbrs_gpu = args.gpus[0]
    stm_gpu = args.gpus[1] if len(args.gpus) > 1 else args.gpus[0]

    app = QApplication(sys.argv)
    ex = App(args.seq, args.nobjects, args.mem, fbrs_gpu, stm_gpu)
    sys.exit(app.exec_())
