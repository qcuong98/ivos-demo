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
from QRangeSlider import QRangeSlider

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
import json

from model import model
from utils import get_fps, pascal_color_map, load_frames, overlay_davis, overlay_checker, overlay_color, overlay_fade
import config


class App(QWidget):
    def __init__(self, video, video_dir, step, n_objects, config, memory_size,
                 fbrs_gpu, stm_gpu):
        super().__init__()

        self.session_id = str(uuid.uuid1())
        print(f'Sesssion ID: {self.session_id}')

        self.video = video
        self.video_dir = video_dir
        self.step = step

        self.raw_height = int(self.video.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.raw_width = int(self.video.get(cv2.CAP_PROP_FRAME_WIDTH))

        height = 480
        width = int(self.raw_width / self.raw_height * height)

        self.n_objects = n_objects
        self.config = config
        self.memory_size = memory_size
        self.frames, self.frame_ids = load_frames(self.video, self.step,
                                                  (width, height))
        self.num_frames, self.height, self.width = self.frames.shape[:3]
        # init model
        self.model = model(self.frames, self.n_objects, self.memory_size,
                           fbrs_gpu, stm_gpu)

        # get color map
        self.cmap = pascal_color_map(normalized=True)

        # set window
        self.setWindowTitle('VOS Annotation Tool')
        self.setGeometry(100, 100, self.width + 200, self.height + 100)

        # buttons
        self.prev_button = QPushButton('Prev')
        self.prev_button.clicked.connect(self.on_prev)
        self.next_button = QPushButton('Next')
        self.next_button.clicked.connect(self.on_next)
        self.play_button = QPushButton('Play')
        self.play_button.clicked.connect(self.on_play)
        self.reset_button = QPushButton('Reset')
        self.reset_button.clicked.connect(self.on_reset)
        self.run_button = QPushButton('Propagate')
        self.run_button.clicked.connect(self.on_run)
        self.visualize_button = QPushButton('Visualize')
        self.visualize_button.clicked.connect(self.on_visualize)

        # LCD
        self.lcd = QTextEdit()
        self.lcd.setReadOnly(True)
        self.lcd.setMaximumHeight(28)
        self.lcd.setMaximumWidth(150)
        self.lcd.setText(f'{0: 3d} / {0: 3d} / {self.num_frames - 1: 3d}')

        # slide
        self.slider = QRangeSlider()
        self.slider.setRangeLimit(0, self.num_frames - 1)
        self.slider.setRange(0, self.num_frames - 1)
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
        self.object_spin.setMaximum(self.n_objects)
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
        # navi.addStretch(1)
        # navi.addWidget(self.reset_button)
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
        self.range = (0, self.num_frames - 1)
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
        l, r = self.slider.getRange()
        self.lcd.setText(f'{l: 3d} / {self.cursur: 3d} / {r: 3d}')
        self.slider.setValue(self.cursur)

    def reset_scribbles(self):
        self.scribbles = {}
        self.scribbles['scribbles'] = [[] for _ in range(self.num_frames)]

    def clear_strokes(self):
        # clear drawn scribbles
        if len(self.drawn_strokes) > 0:
            for line in self.drawn_strokes:
                if line is not None:
                    line.pop(0).remove()
            self.drawn_strokes = []
            self.canvas.draw()

    def set_viz_mode(self):
        self.viz_mode = self.overlay_combo.currentText()
        self.show_current()

    def slide(self):
        self.clear_strokes()
        self.reset_scribbles()
        self.range = self.slider.getRange()
        self.cursur = self.slider.getValue()
        self.show_current()
        # print('slide')

    def on_run(self):
        self.run_button.setEnabled(False)
        self.model.run_propagation(self.range)
        self.run_button.setEnabled(True)
        # clear scribble and reset
        self.show_current()
        self.reset_scribbles()
        self.clear_strokes()

    def on_visualize(self):
        video_dir = os.path.join('visualized', self.session_id, 'video.mp4')
        masks_dir = os.path.join('visualized', self.session_id, 'pivot_masks')
        json_dir = os.path.join('visualized', self.session_id, 'objects.json')

        if not os.path.isdir(masks_dir):
            os.makedirs(masks_dir)
        for i, mask in enumerate(self.model.current_masks):
            Image.fromarray(mask).resize(
                (self.raw_width, self.raw_height), Image.NEAREST).save(
                    os.path.join(masks_dir, f'{self.frame_ids[i]:06}.png'))

        shutil.copy2(self.video_dir, video_dir)

        self.config['fps'] = get_fps(self.video)
        with open(json_dir, 'w') as outfile:
            json.dump(self.config, outfile)

        # np.save(npy_dir, self.model.current_masks)

    def on_prev(self):
        self.clear_strokes()
        self.reset_scribbles()
        self.cursur = max(self.range[0], self.cursur - 1)
        self.show_current()
        # print('prev')

    def on_next(self):
        self.clear_strokes()
        self.reset_scribbles()
        self.cursur = min(self.cursur + 1, self.range[1])
        self.show_current()
        # print('next ')

    def on_time(self):
        self.clear_strokes()
        self.reset_scribbles()
        self.cursur += 1
        if self.cursur > self.range[1]:
            self.cursur = self.range[0]
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

        self.run_button.setEnabled(False)
        self.model.run_interaction(self.scribbles, self.range)
        self.run_button.setEnabled(True)
        self.show_current()

    def on_reset(self):
        self.show_current()
        self.reset_scribbles()
        self.clear_strokes()


def read_config(config_dir):
    with open(config_dir, 'r') as json_file:
        data = json.load(json_file)
        return data


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="args")
    parser.add_argument("--video",
                        type=str,
                        help='directory of video file (mp4)',
                        required=True)
    parser.add_argument(
        "--step",
        type=int,
        help='number of frames stepped (max number of annotated frames = 1000)',
        default=1)
    parser.add_argument("--config",
                        type=str,
                        help='directory of objects config file',
                        required=False)
    parser.add_argument("--mem",
                        type=int,
                        help='memory size of memory-based model',
                        default=5)
    parser.add_argument("--gpus",
                        nargs='+',
                        type=int,
                        help='gpu ids need for modules',
                        default=[0])
    args = parser.parse_args()

    video = cv2.VideoCapture(args.video)
    if not video.isOpened():
        raise "Can't open video file"

    n_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    step = args.step
    if n_frames // step > config.MAX_ANNOTATED_FRAMES:
        step = n_frames // config.MAX_ANNOTATED_FRAMES
    print(f'Number of frames: {n_frames} - Step: {step}')

    fbrs_gpu = args.gpus[0]
    stm_gpu = args.gpus[1] if len(args.gpus) > 1 else args.gpus[0]

    if args.config is not None:
        config = read_config(args.config)
    else:
        config = {
            'objects':
            [f'object_{i}' for i in range(1, config.DEFAULT_N_OBJECTS + 1)]
        }

    n_objects = len(config['objects'])

    app = QApplication(sys.argv)
    ex = App(video, args.video, step, n_objects, config, args.mem, fbrs_gpu,
             stm_gpu)
    sys.exit(app.exec_())
