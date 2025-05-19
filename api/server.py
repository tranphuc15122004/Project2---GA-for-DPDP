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
        'selected': instances or selected
    })



@app.route('/api/start', methods=['POST'])
def start_simulation():
    data = request.json
    instance_id = data.get('instance_id')
    algorithm_name = data.get('algorithm')
    
    if not sim_wrapper.running:
        thread = threading.Thread(
            target=sim_wrapper.run_simulation,
            args=(instance_id,algorithm_name, socketio),
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


#----------------- SocketIO Events ----------------

@socketio.on('connect')
def handle_connect():
    #emit('state_update', sim_wrapper.get_state())
    # Gửi trạng thái hiện tại khi client kết nối
    emit('state_update', sim_wrapper.get_state())
    return {'status': 'connected'}


@socketio.on('get_instances')
def handle_get_instances(data):
    from src.conf.configs import Configs
    instances = []
    for idx in Configs.all_test_instances:
        if idx <= 64:
            instances.append(f"instance_{idx}")
        else:
            instances.append(f"customed_instance_{idx-64}")
    selected = [f"instance_{idx}" for idx in (Configs.selected_instances or [])] 
    return {
        'instances': instances or selected
    }


@socketio.on('get_algorithms')
def handle_get_algorithms(data):
    from src.conf.configs import Configs
    algorithms = Configs.all_algorithms  # Danh sách thuật toán từ Configs
    return {
        'algorithms': algorithms
    }

@socketio.on('start_simulation')
def handle_start_simulation(data):
    instance_id = data.get('instance_id')
    algorithm_name = data.get('algorithm')
    

    if not instance_id:
        return {'error': 'No instance ID provided'}

    if not algorithm_name:
        return {'error': 'No algorithm name provided'}
    
    if not sim_wrapper.running:
        try:
            thread = threading.Thread(
                target=sim_wrapper.run_simulation,
                args=(instance_id, algorithm_name,  socketio),
                daemon=True
            )
            thread.start()
            
            # Emit event to all clients
            socketio.emit('simulation_started', {
                'instance_id': instance_id,
                'algorithm_name': algorithm_name,
                'timestamp': time.time()
            })
            
            return {'status': 'started'}
        except Exception as e:
            print(f"Error starting simulation: {e}")
            return {'error': str(e)}
    else:
        return {'error': 'Simulation already running'}

""" def background_updater():
    while True:
        socketio.emit('state_update', sim_wrapper.get_state())
        time.sleep(0.5)

threading.Thread(target=background_updater, daemon=True).start() """


""" @socketio.on('simulation_completed')
def handle_simulation_completed(data):
    try:
        # Gửi thông báo cuối cùng đến tất cả clients
        socketio.emit('simulation_completed', {
            'instance_id': data.get('instance_id'),
            'algorithm': data.get('algorithm'),
            'completed_orders': data.get('completed_orders', 0),
            'ongoing_orders': data.get('ongoing_orders', 0),
            'unallocated_orders': data.get('unallocated_orders', 0),
            'timestamp': time.time(),
            'status': 'completed'
        })
        
        # Gửi state update cuối cùng
        socketio.emit('state_update', sim_wrapper.get_state())
        
        print(f"Simulation completed for {data.get('instance_id')} with algorithm {data.get('algorithm')}")
        return {'status': 'completed'}
    except Exception as e:
        print(f"Error handling simulation completed: {e}")
        return {'error': str(e)} """

# -------------- Error Handlers --------------

@app.errorhandler(Exception)
def handle_error(e):
    print(f"Server error: {e}")
    return jsonify(error=str(e)), 500

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000)