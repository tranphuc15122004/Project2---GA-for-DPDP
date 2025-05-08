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

@socketio.on('get_instances')
def handle_get_instances(data):
    from src.conf.configs import Configs
    instances = [f"instance_{idx}" for idx in Configs.all_test_instances]
    selected = [f"instance_{idx}" for idx in (Configs.selected_instances or [])]
    return {
        'instances': selected or instances
    }

@socketio.on('start_simulation')
def handle_start_simulation(data):
    instance_id = data.get('instance_id')
    
    if not instance_id:
        return {'error': 'No instance ID provided'}
    
    if not sim_wrapper.running:
        try:
            thread = threading.Thread(
                target=sim_wrapper.run_simulation,
                args=(instance_id, socketio),
                daemon=True
            )
            thread.start()
            
            # Emit event to all clients
            socketio.emit('simulation_started', {
                'instance_id': instance_id,
                'timestamp': time.time()
            })
            
            return {'status': 'started'}
        except Exception as e:
            print(f"Error starting simulation: {e}")
            return {'error': str(e)}
    else:
        return {'error': 'Simulation already running'}

@socketio.on('pause_simulation')
def handle_pause_simulation(data):
    try:
        # Toggle pause state
        sim_wrapper.paused = not sim_wrapper.paused
        
        # Emit event to all clients
        socketio.emit('simulation_paused', {
            'paused': sim_wrapper.paused,
            'timestamp': time.time()
        })
        
        return {'status': 'paused' if sim_wrapper.paused else 'resumed'}
    except Exception as e:
        print(f"Error pausing simulation: {e}")
        return {'error': str(e)}


def background_updater():
    while True:
        socketio.emit('state_update', sim_wrapper.get_state())
        time.sleep(0.5)

threading.Thread(target=background_updater, daemon=True).start()

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000)