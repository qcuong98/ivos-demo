import numpy as np
import torch
from PIL import Image


class DataHelper():
    def __init__(self):
        self.K = 11

    def To_onehot(self, mask):
        M = np.zeros((self.K, mask.shape[0], mask.shape[1]), dtype=np.uint8)
        for k in range(self.K):
            M[k] = (mask == k).astype(np.uint8)
        return M

    def All_to_onehot(self, masks):
        Ms = np.zeros((self.K, masks.shape[0], masks.shape[1], masks.shape[2]),
                      dtype=np.uint8)
        for n in range(masks.shape[0]):
            Ms[:, n] = self.To_onehot(masks[n])
        return Ms

    def get_data(self,
                 frame_imgs,
                 mask_imgs,
                 n_objects,
                 frame_id,
                 last_id,
                 dir,
                 N=2,
                 annotated_frames=[]):
        n_frames, height, width = mask_imgs.shape

        if dir == 0:  # refine
            list_frames = [frame_id] * N
        elif dir == -1:  # reverse
            list_frames = list(range(frame_id, last_id - 1, -1))
        else:
            list_frames = list(range(frame_id, last_id + 1))

        N_frames = np.empty((len(list_frames), height, width, 3),
                            dtype=np.float32)
        N_masks = np.empty((len(list_frames), height, width), dtype=np.float32)

        for i, f in enumerate(list_frames):
            N_frames[i] = frame_imgs[f] / 255.
            if (len(annotated_frames) == 0
                    and i != 0) or (len(annotated_frames) != 0
                                    and f not in annotated_frames):
                N_masks[i] = 255
            else:
                N_masks[i] = mask_imgs[f]

        Fs = torch.from_numpy(
            np.transpose(N_frames.copy(), (3, 0, 1, 2)).copy()).float()
        Ms = torch.from_numpy(self.All_to_onehot(N_masks).copy()).float()
        Fs = Fs.unsqueeze(0)
        Ms = Ms.unsqueeze(0)
        return Fs, Ms
