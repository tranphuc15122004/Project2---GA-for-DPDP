from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from src.wapper import SimulationWrapper
import threading
import time

app = Flask(__name__ , static_folder='../frontend' ,static_url_path='')
CORS(app)
# Đảm bảo socketio được khởi tạo đúng cách
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

sim_wrapper = SimulationWrapper()

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/api/instances', methods=['GET'])
def get_instances():
    from src.conf.configs import Configs
    instances = [f"instance_{idx}" for idx in Configs.all_test_instances]
    selected = [f"instance_{idx}" for idx in (Configs.selected_instances or [])]
    return jsonify({
        'all': instances,
        'selected': selected or instances
    })

@app.route('/api/start', methods=['POST'])
def start_simulation():
    data = request.json
    instance_id = data.get('instance_id')
    
    if not sim_wrapper.running:
        thread = threading.Thread(
            target=sim_wrapper.run_simulation,
            args=(instance_id,),
            daemon=True
        )
        thread.start()
        return jsonify({'status': 'started'})
    return jsonify({'status': 'already running'})

@app.route('/api/pause', methods=['POST'])
def pause_simulation():
    sim_wrapper.paused = not sim_wrapper.paused
    return jsonify({'status': 'paused' if sim_wrapper.paused else 'resumed'})

@app.route('/api/state', methods=['GET'])
def get_state():
    return jsonify(sim_wrapper.get_state())

@socketio.on('connect')
def handle_connect():
    emit('state_update', sim_wrapper.get_state())

def background_updater():
    while True:
        socketio.emit('state_update', sim_wrapper.get_state())
        time.sleep(0.5)

threading.Thread(target=background_updater, daemon=True).start()

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000)