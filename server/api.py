from flask import Flask, request, jsonify, render_template, send_file, send_from_directory
from dateutil.parser import parse as parse_date
import json
import os
import io
import time
import sys

sys.path.insert(1, os.path.join(sys.path[0], '..'))

from mask_extractor import MaskExtractor
import api_utils
from propagation.STM.main import STM_Model

with open('server/config.json', 'r') as f:
    config = json.load(f)
extractor = MaskExtractor()

app = Flask(__name__, template_folder="static")
stm = STM_Model("propagation/STM/STM_weights.pth", config['memory_size'],
                config['gpu_id'])


@app.route('/', methods=['GET'])
def homepage():
    list_sessions_path = [
        f.path for f in os.scandir(config['sessions_dir']) if f.is_dir()
    ]
    list_sessions = [
        os.path.split(session_path)[1] for session_path in list_sessions_path
    ]

    video_list = []
    for video_id in list_sessions:
        with open(config["sessions_dir"] + f"/{video_id}/objects.json") as f:
            meta = json.load(f)
            created_at = parse_date(meta["created_at"])
            meta["formatted_upload_date"] = created_at.strftime("%B %d, %Y")
            video_list.append({"id": video_id, "metadata": meta})
    return render_template("index.html", video_list=video_list)


@app.route('/<uuid:session_key>', methods=['GET'])
def session_page(session_key):
    video_id = session_key
    with open(config["sessions_dir"] + f"/{video_id}/objects.json") as f:
        meta = json.load(f)
        created_at = parse_date(meta["created_at"])
        meta["formatted_upload_date"] = created_at.strftime("%B %d, %Y")
        video = {"id": video_id, "metadata": meta}
    return render_template("video.html", video=video)


@app.route('/about', methods=['GET'])
def about_page():
    return render_template("about.html")


@app.route('/<uuid:session_key>/<int:frame_id>/<int:object_id>.png',
           methods=['GET'])
def get_obj_mask(session_key, frame_id, object_id):
    session_dir = os.path.join(config['sessions_dir'], str(session_key))
    list_pivot_pairs, cur_frame, is_exists = api_utils.get_memory_query(
        session_dir, frame_id, config['memory_size'])

    if list_pivot_pairs is None:
        return 'Video Not Found', 404

    if is_exists:
        multi_mask = list_pivot_pairs[0][1]
    else:
        multi_mask = stm.lazy_propagation(list_pivot_pairs,
                                          cur_frame,
                                          api_utils.get_n_objects(session_dir),
                                          height=480)

    single_masks = extractor.extract(multi_mask,
                                     api_utils.get_n_objects(session_dir))
    output = io.BytesIO()
    single_masks[object_id].save(output, 'PNG')
    output.seek(0)
    return send_file(output,
                     mimetype='image/png',
                     as_attachment=True,
                     attachment_filename=f'{frame_id:06}-{object_id}.png'), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=20408, debug=True)
