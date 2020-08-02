import os
import json
from pathlib import Path
from PIL import Image
import numpy as np
import cv2

def get_memory_query(session_dir, frame_id, memory_size):
    if not os.path.isdir(session_dir):
        return None, False

    video = cv2.VideoCapture(os.path.join(session_dir, 'video.mp4'))
    if not video.isOpened():
        return None, None, False

    pivot_masks_dir = os.path.join(session_dir, 'pivot_masks')
    lst = []
    for mask_dir in Path(pivot_masks_dir).glob("*.png"):
        pivot_mask_id = int(os.path.splitext(str(mask_dir.parts[-1]))[0])
        lst.append((pivot_mask_id, str(mask_dir)))
    lst.sort(key=lambda x: abs(frame_id - x[0]))

    nearest_pairs = []
    for pair_id, mask_dir in lst[:min(memory_size, len(lst))]:
        video.set(cv2.CAP_PROP_POS_FRAMES, pair_id)
        success, frame = video.read()
        if not success:
            return None, None, False
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mask = np.asarray(Image.open(mask_dir))

        nearest_pairs.append((frame, mask))

    video.set(cv2.CAP_PROP_POS_FRAMES, frame_id)
    success, frame = video.read()
    if not success:
        return None, None, False
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    return nearest_pairs, frame, bool(lst[0][0] == frame_id)

def get_n_objects(session_dir):
    with open(os.path.join(session_dir, 'objects.json')) as f:
        data = json.load(f)
    return len(data['objects'])