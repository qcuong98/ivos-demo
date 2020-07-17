import numpy as np

from segmentation.utils.scribble2mask import FBRS
from propagation.STM.main import STM_Model


class model():
    def __init__(self, frames, n_objects, memory_size, fbrs_gpu, stm_gpu):
        self.frames = frames
        self.memory_size = memory_size
        self.n_objects = n_objects

        self.n_frames, self.height, self.width = self.frames.shape[:3]
        self.current_masks = np.zeros(self.frames.shape[:3], dtype=np.uint8)
        self.annotated_frames = []
        self.first_interation = False

        self.fbrs = FBRS(fbrs_gpu, visualizer=None, external=False)
        self.stm = STM_Model("propagation/STM/STM_weights.pth", memory_size, stm_gpu)

    def run_interaction(self, scribbles):
        target = scribbles['annotated_frame']
        if len(self.annotated_frames
               ) == 0 or self.annotated_frames[-1] != target:
            self.annotated_frames.append(target)

        annotated_mask = self.fbrs.scribble2mask(self.current_masks[target],
                                                 scribbles,
                                                 self.frames[target], target,
                                                 self.n_objects,
                                                 self.first_interation)
        self.current_masks[target] = annotated_mask

        refined_mask = self.stm.self_refine(self.frames, self.current_masks,
                                            self.n_objects,
                                            self.annotated_frames)
        self.current_masks[target] = refined_mask

        print(f'[Interaction] User Interaction on frame {target}')

    def run_propagation(self):
        self.first_interation = False

        new_masks = self.stm.propagate(self.frames, self.current_masks,
                                       self.n_objects, self.annotated_frames)
        self.current_masks = np.copy(new_masks)
        print(f'[Propagation] Done')