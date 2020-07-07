from segmentation.fbrs import fbrs_nogui

import argparse
import pickle
import numpy as np

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input_pkl')
    parser.add_argument('output_npy')
    args = parser.parse_args()

    pkl_data = pickle.load(open(args.input_pkl, "rb"))

    fbrs_model = fbrs_nogui.create_controller()
    fbrs_model.set_image(pkl_data["image"])
    fbrs_model.add_clicks(pkl_data["clicks"])
    mask = fbrs_model.current_object_prob

    ok = False
    for x, y, is_pos in pkl_data["clicks"]:
        if is_pos:
            ok = True
    if not ok:
        mask[:] = 0

    np.save(args.output_npy, mask)