import os
import json
from pathlib import Path
from PIL import Image
import numpy as np

def get_nearest_pivot_frames(session_dir, frame_id, memory_size):
    if not os.path.isdir(session_dir):
        return None, False

    pivot_masks_dir = os.path.join(session_dir, 'pivot_masks')
    lst = []
    for frame_dir in Path(pivot_masks_dir).glob("*.png"):
        pivot_frame_id = int(os.path.splitext(str(frame_dir.parts[-1]))[0])
        lst.append((pivot_frame_id, str(frame_dir)))

    lst.sort(key=lambda x: abs(frame_id - x[0]))
    nearest_frames = [
        np.asarray(Image.open(frame_dir))
        for _, frame_dir in lst[:min(memory_size, len(lst))]
    ]
    return nearest_frames, bool(lst[0][0] == frame_id)

def get_n_objects(session_dir):
    with open(os.path.join(session_dir, 'objects.json')) as f:
        data = json.load(f)
    return len(data['objects'])