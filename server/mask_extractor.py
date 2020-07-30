import numpy as np
from PIL import Image

class MaskExtractor:
    def __init__(self, N=256, color_normalized=False):
        # init color map

        def bitget(byteval, idx):
            return (byteval & (1 << idx)) != 0

        dtype = 'float32' if color_normalized else 'uint8'
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

        self.cmap = cmap / 255 if color_normalized else cmap

    def extract(self, frame, n_objects):
        images = [None]

        for object_id in range(1, n_objects + 1):
            mask = np.equal(frame, object_id)
            image = np.uint8(np.stack([mask, mask, mask, mask], axis=-1))
            image[mask == True] = list(self.cmap[object_id]) + [64]
            
            image = Image.fromarray(image, mode='RGBA')
            images.append(image)

        return images
