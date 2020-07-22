from .data_helper import DataHelper
from .model import STM

import torch
import torch.nn as nn
import torch.nn.functional as F

import numpy as np
import tqdm

import config


class STM_Model():
    def __init__(self, pth_path, memory_size, gpu_id=0):
        print("[LOADING] STM")

        cuda = torch.cuda.is_available()
        self.model = nn.DataParallel(STM(gpu_id), device_ids=[gpu_id])
        if cuda:
            self.model.to(torch.device(f'cuda:{gpu_id}'))
        self.model.load_state_dict(torch.load(pth_path))
        self.model.eval()
        self.data_helper = DataHelper()
        self.Mem_number = memory_size

    @torch.no_grad()
    def Run_video(self, Fs, Ms, num_frames, num_objects, _keys, _values,
                  n_keys):
        # initialize storage tensors
        to_memorize = []
        if n_keys < self.Mem_number:
            to_memorize = [
                int(round(i)) for i in np.linspace(
                    0, num_frames, num=self.Mem_number - n_keys + 1)[:-1]
            ]

        if _keys is not None:
            keys, values = _keys.clone(), _values.clone()
        else:
            keys, values = None, None

        Es = torch.zeros_like(Ms)
        Es[:, :, 0] = Ms[:, :, 0]

        for t in tqdm.tqdm(range(1, num_frames)):
            # memorize
            with torch.no_grad():
                prev_key, prev_value = self.model(Fs[:, :, t - 1], Es[:, :,
                                                                      t - 1],
                                                  torch.tensor([num_objects]))

            if keys is not None:
                this_keys = torch.cat([keys, prev_key], dim=3)
                this_values = torch.cat([values, prev_value], dim=3)
            else:
                this_keys, this_values = prev_key, prev_value

            # segment
            with torch.no_grad():
                logit = self.model(Fs[:, :, t], this_keys, this_values,
                                   torch.tensor([num_objects]))
                Es[:, :, t] = F.softmax(logit, dim=1)

            # update
            if t - 1 in to_memorize:
                keys, values = this_keys, this_values

        pred = np.argmax(Es[0].cpu().numpy(), axis=0).astype(np.uint8)
        return pred, Es

    def init_memory_pool(self, frame_imgs, frame_mask, n_objects,
                         annotated_frames):
        n_frames, height, width = frame_mask.shape

        pred = np.copy(frame_mask)
        annotated_frame_id = annotated_frames[-1]

        # Get key and value from prev annotated frames
        self.keys, self.values = None, None
        self.cnt_key = 0
        if len(annotated_frames) > 1:
            Fs, Ms = self.data_helper.get_data(
                frame_imgs,
                pred,
                n_objects,
                0,
                n_frames - 1,
                1,
                annotated_frames=annotated_frames[:-1])
            for frame_id in reversed(annotated_frames[:-1]):
                if self.cnt_key + 1 < self.Mem_number:
                    with torch.no_grad():
                        _key, _value = self.model(Fs[:, :, frame_id],
                                                  Ms[:, :, frame_id],
                                                  torch.tensor([n_objects]))
                    if self.keys is not None:
                        self.keys = torch.cat([self.keys, _key], dim=3)
                        self.values = torch.cat([self.values, _value], dim=3)
                    else:
                        self.keys, self.values = _key, _value  # only prev memory
                    self.cnt_key += 1
        print(f'Number of STM Key-Value Pairs: {self.cnt_key + 1}')

    def self_refine(self, frame_imgs, frame_mask, n_objects, annotated_frames):
        n_frames, height, width = frame_mask.shape

        pred = np.copy(frame_mask)
        annotated_frame_id = annotated_frames[-1]

        self.init_memory_pool(frame_imgs, frame_mask, n_objects,
                              annotated_frames)

        # Self-Refine
        Fs, Ms = self.data_helper.get_data(frame_imgs,
                                           pred,
                                           n_objects,
                                           annotated_frame_id,
                                           annotated_frame_id,
                                           0,
                                           N=config.N_REFINES)
        _pred, _Es = self.Run_video(Fs, Ms, config.N_REFINES, n_objects,
                                    self.keys, self.values, self.cnt_key)
        return _pred[-1]

    def propagate(self, frame_imgs, frame_mask, n_objects, annotated_frames, range):
        n_frames, height, width = frame_mask.shape

        pred = np.copy(frame_mask)
        annotated_frame_id = annotated_frames[-1]

        self.init_memory_pool(frame_imgs, frame_mask, n_objects,
                              annotated_frames)

        # Propagate
        _left = range[0]

        Fs, Ms = self.data_helper.get_data(frame_imgs, pred, n_objects,
                                           annotated_frame_id, _left, -1)
        _pred, _Es = self.Run_video(Fs, Ms, annotated_frame_id - _left + 1,
                                    n_objects, self.keys, self.values,
                                    self.cnt_key)
        pred[_left:annotated_frame_id + 1] = np.flip(_pred, 0)

        _right = range[1]

        Fs, Ms = self.data_helper.get_data(frame_imgs, pred, n_objects,
                                           annotated_frame_id, _right, 1)
        _pred, _Es = self.Run_video(Fs, Ms, _right - annotated_frame_id + 1,
                                    n_objects, self.keys, self.values,
                                    self.cnt_key)
        pred[annotated_frame_id:_right + 1] = _pred

        return pred
