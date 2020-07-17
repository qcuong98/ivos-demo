import cv2
import numpy as np
from PIL import Image
import torch
import argparse

from .interactive_demo.controller import InteractiveController

from .isegm.utils import exp
from .isegm.inference import utils

def parse_args():
    args = {}
    args['checkpoint'] = 'segmentation/fbrs/weights/resnet50_dh128_lvis.pth'
    args['norm_radius'] = 260
    args['cfg'] = "segmentation/fbrs/config.yml"

    cfg = exp.load_config_file(args['cfg'], return_edict=True)

    return args, cfg

def create_controller(gpu_id):
    print("[LOADING] FBRS")
    args, cfg = parse_args()
    args['device'] = torch.device(f'cuda:{gpu_id}')

    torch.backends.cudnn.deterministic = True
    checkpoint_path = utils.find_checkpoint(cfg.INTERACTIVE_MODELS_PATH, args['checkpoint'])
    model = utils.load_is_model(checkpoint_path, args['device'], cpu_dist_maps=True, norm_radius=args['norm_radius'])
    _controller = InteractiveController(model, args['device'],
                                                predictor_params={'brs_mode': 'NoBRS'},
                                                update_image_callback=None)
                                                # update_image_callback=self._update_image)
    return _controller