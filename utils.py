from davisinteractive import utils

import torch
from torch.autograd import Variable
from torch.utils import data

import torch.nn as nn
import torch.nn.functional as F
import torch.nn.init as init
import torch.utils.model_zoo as model_zoo
from torchvision import models

# general libs
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import os
import copy
import cv2
import random
import glob

def get_fps(video):
    return video.get(cv2.CAP_PROP_FPS)

def pascal_color_map(N=256, normalized=False):
    """
        Python implementation of the color map function for the PASCAL VOC data set.
        Official Matlab version can be found in the PASCAL VOC devkit
        http://host.robots.ox.ac.uk/pascal/VOC/voc2012/index.html#devkit
        """
    def bitget(byteval, idx):
        return (byteval & (1 << idx)) != 0

    dtype = 'float32' if normalized else 'uint8'
    cmap = np.zeros((N, 3), dtype=dtype)
    for i in range(N):
        r = g = b = 0
        c = i
        for j in range(8):
            r = r | (bitget(c, 0) << 7 - j)
            g = g | (bitget(c, 1) << 7 - j)
            b = b | (bitget(c, 2) << 7 - j)
            c = c >> 3

        cmap[i] = np.array([r, g, b])

    cmap = cmap / 255 if normalized else cmap
    return cmap


def load_frames(video, size=None):
    frame_list = []

    while True:
        success, image = video.read()
        if not success:
            break
        frame_list.append(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

    frames = np.stack(frame_list, axis=0)
    return frames


def overlay_davis(image, mask, rgb=[255, 0, 0], cscale=2, alpha=0.5):
    im_overlay = utils.visualization.overlay_mask(image, mask, alpha=alpha)
    return im_overlay.astype(image.dtype)

def checkerboard(img_size, block_size):
    width = int(
        np.maximum(np.ceil(img_size[0] / block_size),
                   np.ceil(img_size[1] / block_size)))
    b = np.zeros((block_size, block_size), dtype=np.uint8) + 32
    w = np.zeros((block_size, block_size), dtype=np.uint8) + 255 - 32
    row1 = np.hstack([w, b] * width)
    row2 = np.hstack([b, w] * width)
    board = np.vstack([row1, row2] * width)
    board = np.stack([board, board, board], axis=2)
    return board[:img_size[0], :img_size[1], :]


BIG_BOARD = checkerboard([1000, 1000], 20)


def overlay_checker(image, mask):
    from scipy.ndimage.morphology import binary_erosion, binary_dilation

    im_overlay = image.copy()
    object_ids = np.unique(mask)

    # board = checkerboard(image.shape[:2], block_size=20)
    board = BIG_BOARD[:im_overlay.shape[0], :im_overlay.shape[1], :].copy()
    binary_mask = (mask != 0)
    # Compose image
    board[binary_mask] = im_overlay[binary_mask]
    return board.astype(image.dtype)


def overlay_color(image, mask, rgb=[255, 0, 255]):
    from scipy.ndimage.morphology import binary_erosion, binary_dilation

    im_overlay = image.copy()
    object_ids = np.unique(mask)

    board = np.ones(image.shape, dtype=np.uint8) * np.array(
        rgb, dtype=np.uint8)[None, None, :]
    binary_mask = (mask != 0)
    # Compose image
    board[binary_mask] = im_overlay[binary_mask]
    return board.astype(image.dtype)


def overlay_fade(image, mask):
    from scipy.ndimage.morphology import binary_erosion, binary_dilation
    im_overlay = image.copy()

    # Overlay color on  binary mask
    binary_mask = mask != 0
    not_mask = mask == 0

    # Compose image
    im_overlay[not_mask] = 0.4 * im_overlay[not_mask]

    countours = binary_dilation(binary_mask) ^ binary_mask
    im_overlay[countours, 0] = 0
    im_overlay[countours, 1] = 255
    im_overlay[countours, 2] = 255

    return im_overlay.astype(image.dtype)
