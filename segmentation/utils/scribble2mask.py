from davisinteractive import utils

import math
import numpy as np
import cv2
import pickle
import subprocess
from sklearn.cluster import SpectralClustering

import config
from segmentation.fbrs import fbrs_nogui
from . import superpixel


class FBRS:
    def __init__(self, visualizer=None, external=False):
        self.visualizer = visualizer
        self.external = external
        if not self.external:
            self.fbrs_seg = fbrs_nogui.create_controller()

    @staticmethod
    def scribbles2points(scribbles_dict,
                         height,
                         width,
                         max_points,
                         boundary_mask,
                         min_step=25,
                         length_th=70):
        scribbles = scribbles_dict['scribbles']

        paths = []
        obj_ids = []
        boundary_paths = []
        cnt_points = 0
        for list_objects in scribbles:
            if len(list_objects) > 0:
                # collect paths by object id
                for obj in list_objects:
                    points = [(int(point[0] * (width - 1)),
                               int(point[1] * (height - 1)))
                              for point in obj['path']]
                    sum_point = 0
                    for point in points:
                        sum_point += boundary_mask[point[1], point[0]] / 255
                    avg_point = sum_point / len(points)

                    if avg_point <= 0.1:
                        paths.append(points)
                        obj_ids.append(obj['object_id'])
                        cnt_points += len(obj['path'])
                    else:
                        boundary_paths.append((points, obj['object_id']))

        keypoint_indices = []
        keypoint_objs = []

        if max_points >= len(paths):
            step = max(min_step, cnt_points // max_points)
            keypoint_indices = []
            keypoint_objs = []
            for i in range(len(paths)):
                path = paths[i]
                keypoint_indices += [
                    path[x] for x in range(0, len(path), step)
                ]
                keypoint_objs += [
                    obj_ids[i] for x in range(0, len(path), step)
                ]
        else:
            obj_points = {}
            for i in range(len(paths)):
                path = paths[i]
                point = path[(len(path) - 1) // 2]

                obj_id = obj_ids[i]
                if obj_id in obj_points:
                    obj_points[obj_id].append(point)
                else:
                    obj_points[obj_id] = [point]

            for obj_id, obj_point in obj_points.items():
                num_points = len(obj_point)
                num_element = max(1, (num_points * max_points) // len(path))
                for i in range(num_element):
                    if num_element == 1:
                        point = obj_point[(num_points - 1) // 2]
                    else:
                        point = obj_point[((num_points - 1) * i) //
                                          (num_element - 1)]
                    keypoint_indices.append(point)
                    keypoint_objs.append(obj_id)

        return keypoint_indices, keypoint_objs, boundary_paths

    @staticmethod
    def dilate_boundary_mask(mask, obj_id, width=config.DILATED_SIZE):
        mask = np.uint8(np.where(mask == obj_id, 255, 0))
        kernel = np.ones((width, width), np.uint8)
        gradient = cv2.morphologyEx(mask, cv2.MORPH_GRADIENT, kernel)
        return gradient

    def scribble2mask(self, mask, scribbles, image, frame_id, n_objects,
                      first_scribble):
        height, width = tuple(mask.shape)

        superpixel_mask = SuperPixel.scribble2mask(mask, scribbles, image,
                                                   frame_id)

        boundary_mask = np.zeros((height, width), dtype=np.uint8)
        if not first_scribble:
            for obj_id in range(1, n_objects + 1):
                boundary_obj = FBRS.dilate_boundary_mask(mask, obj_id)
                boundary_mask = np.maximum(boundary_mask, boundary_obj)

        keypoint_indices, keypoint_objs, boundary_paths = FBRS.scribbles2points(
            scribbles, height, width, config.MAX_SCRIBBLE_POINTS,
            boundary_mask)

        if self.visualizer:
            self.visualizer.keypoints(image, keypoint_indices, keypoint_objs)

        ratio = config.MAX_FBRS_IMAGE_SIZE / width
        resized_image = cv2.resize(image, (0, 0), fx=ratio, fy=ratio)

        obj_mask = np.zeros((n_objects + 1, 1, height, width),
                            dtype=np.float32)
        n_points = len(keypoint_indices)

        if not self.external:
            self.fbrs_seg.set_image(resized_image)

        for obj_id in range(n_objects + 1):
            clicks = []
            for idx in range(n_points):
                x, y = keypoint_indices[idx][0], keypoint_indices[idx][1]
                clicks.append((int(x * ratio), (y * ratio),
                               keypoint_objs[idx] == obj_id))
            if self.external:
                pkl_data = {
                    "image": resized_image,
                    "clicks": clicks,
                }
                pickle.dump(pkl_data, open("pickles/fbrs_input.pkl", "wb"))
                cnt = 0
                while cnt < 2:
                    fbrs = subprocess.run([
                        "python", "segmentation/fbrs/haha.py",
                        "pickles/fbrs_input.pkl", "pickles/fbrs_output.npy"
                    ])
                    if fbrs.returncode == 0:
                        break
                    print("FBRS crashed!!!")
                    cnt += 1
                if cnt < 2:
                    fbrs_output = np.load("pickles/fbrs_output.npy")
                    obj_mask[obj_id, 0] = cv2.resize(fbrs_output,
                                                     (width, height))
                else:
                    obj_mask[obj_id, 0] = np.where(superpixel_mask == obj_id,
                                                   1, 0)
            else:
                self.fbrs_seg.add_clicks(clicks)
                fbrs_output = self.fbrs_seg.current_object_prob
                obj_mask[obj_id, 0] = cv2.resize(fbrs_output, (width, height))
                self.fbrs_seg.reset_last_object(update_image=False)

        if first_scribble:
            annotated_mask = utils.mask.combine_masks(obj_mask[1:])[0]
        else:
            scribbles_mask = utils.mask.combine_masks(obj_mask)[0]
            annotated_mask = np.where(scribbles_mask != 0, scribbles_mask - 1,
                                      mask)

            # Dilate boundary scribbles
            for path, obj_id in boundary_paths:
                _path = np.asarray(path)
                cv2.polylines(annotated_mask,
                              np.int32([_path]),
                              isClosed=False,
                              color=obj_id,
                              thickness=config.DILATED_SIZE)

        return annotated_mask


class SuperPixel:
    def __init__(self):
        super().__init__()

    @staticmethod
    def scribble2mask(mask, scribbles, image, frame_id, first_scribble=True):
        height, width = tuple(mask.shape)

        scribbles_mask = utils.scribbles.scribbles2mask(
            scribbles, output_resolution=(height, width))[frame_id]
        scribbles_mask = SuperPixel.expand_scribbles_mask(
            image, scribbles_mask)

        if first_scribble:
            annotated_mask = np.where(scribbles_mask != -1, scribbles_mask, 0)
        else:
            annotated_mask = np.where(scribbles_mask != -1, scribbles_mask,
                                      mask)
        return annotated_mask

    @staticmethod
    def expand_scribbles_mask(img, scribbles_mask):
        expanded_mask = np.copy(scribbles_mask)

        segments = superpixel.main(img, config.N_CLUSTERS)
        for segment_id in range(config.N_CLUSTERS):
            segment_pixels = scribbles_mask[segments == segment_id]
            scribble_pixels = segment_pixels[segment_pixels != -1]
            if scribble_pixels.shape != (0, ):
                # Find mode of obj_id in current segment
                counts = np.bincount(scribble_pixels)
                obj_id = np.argmax(counts)
                # Change all segment pixels to obj_id
                expanded_mask[segments == segment_id] = obj_id

        return expanded_mask
