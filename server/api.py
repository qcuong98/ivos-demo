from flask import Flask, request, jsonify, render_template, send_file, send_from_directory
import json
import os
import io

from mask_extractor import MaskExtractor
import utils
# from propagation.STM.main import STM_Model

with open('server/config.json', 'r') as f:
    config = json.load(f)
extractor = MaskExtractor()

app = Flask(__name__)
stm = None
# stm = STM_Model("propagation/STM/STM_weights.pth", config['memory_size'],
#                 config['gpu_id'])


@app.route('/', methods=['GET'])
def homepage():
    return send_from_directory('static', 'index.html')


@app.route('/<uuid:session_key>', methods=['GET'])
def session_page(session_key):
    return send_from_directory('static', 'video.html')


@app.route('/sessions', methods=['GET'])
def get_list_sessions():
    list_sessions_path = [
        f.path for f in os.scandir(config['sessions_dir']) if f.is_dir()
    ]
    list_sessions = [
        os.path.split(session_path)[1] for session_path in list_sessions_path
    ]
    data = {}
    data['sessions'] = list_sessions
    return jsonify(data), 200


@app.route('/<uuid:session_key>/<int:frame_id>/<int:object_id>.png',
           methods=['GET'])
def get_obj_mask(session_key, frame_id, object_id):
    session_dir = os.path.join(config['sessions_dir'], str(session_key))
    list_pivot_frames, is_exists = utils.get_nearest_pivot_frames(
        session_dir, frame_id, config['memory_size'])

    if list_pivot_frames is None:
        return 'Video Not Found', 404

    if is_exists:
        frame = list_pivot_frames[0]
    else:
        return 'Need to propagated', 200
        # frame = model.run_propagation(session_key, frame_id)

    images = extractor.extract(frame, utils.get_n_objects(session_dir))
    output = io.BytesIO()
    images[object_id].save(output, 'PNG')
    output.seek(0)
    return send_file(output,
                     mimetype='image/png',
                     as_attachment=True,
                     attachment_filename=f'{frame_id:06}-{object_id}.png'), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=20408, debug=True)
