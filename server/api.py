from flask import Flask, request, jsonify, render_template, send_file, send_from_directory
from dateutil.parser import parse as parse_date
import json
import os
import io
import time
import sys
import threading
import time
from queue import Empty, Queue

sys.path.insert(1, os.path.join(sys.path[0], '..'))

from .mask_extractor import MaskExtractor
from . import api_utils
from propagation.STM.main import STM_Model

with open('server/config.json', 'r') as f:
    config = json.load(f)
extractor = MaskExtractor()

stm = STM_Model("propagation/STM/STM_weights.pth", config['memory_size'],
                config['gpu_id'])

BATCH_SIZE = 20
BATCH_TIMEOUT = 0.1
CHECK_INTERVAL = 0.001

requests_queue = Queue()

app = Flask(__name__, template_folder="static")


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


def handle_requests_by_batch():
    while True:
        requests_batch = []
        while not (len(requests_batch) > BATCH_SIZE or
                   (len(requests_batch) > 0 and
                    time.time() - requests_batch[0]['time'] > BATCH_TIMEOUT)):
            try:
                requests_batch.append(
                    requests_queue.get(timeout=CHECK_INTERVAL))
            except Empty:
                continue

        prev_predict = {}
        for request in requests_batch:
            session_key, frame_id = request['input']

            if (session_key, frame_id) in prev_predict:
                request['output'] = prev_predict[(session_key, frame_id)]
                continue

            session_dir = os.path.join(config['sessions_dir'],
                                       str(session_key))
            list_pivot_pairs, cur_frame, is_exists = api_utils.get_memory_query(
                session_dir, frame_id, config['memory_size'])

            if list_pivot_pairs is None:
                request['output'] = None
            elif is_exists:
                request['output'] = list_pivot_pairs[0][1]
            else:
                request['output'] = stm.lazy_propagation(
                    list_pivot_pairs,
                    cur_frame,
                    api_utils.get_n_objects(session_dir),
                    height=480)

            prev_predict[(session_key, frame_id)] = request['output']


threading.Thread(target=handle_requests_by_batch).start()

@app.route('/<uuid:session_key>/<int:frame_id>/<int:object_id>.png',
           methods=['GET'])
def get_obj_mask(session_key, frame_id, object_id):
    request = {'input': (session_key, frame_id), 'time': time.time()}
    requests_queue.put(request)

    while 'output' not in request:
        time.sleep(CHECK_INTERVAL)
    multi_mask = request['output']

    if multi_mask is None:
        return 'Video Not Found', 404

    session_dir = os.path.join(config['sessions_dir'], str(session_key))
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
    app.run(host='0.0.0.0', port=8000, debug=False)
