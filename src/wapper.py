import os
import threading
import traceback
import datetime
import sys
import logging
from threading import Thread
from queue import Queue
import time
from src.conf.configs import Configs as SimulatorConfigs
from src.simulator.simulate_api import simulate
from src.utils.log_utils import ini_logger, remove_file_handler_of_logging
from src.utils.logging_engine import logger


class SimulationWrapper:
    def __init__(self):
        self.running = False
        self.paused = False
        self.current_instance = None
        self.current_algorithm = None
        self.output_queue = Queue()
        self.scores = []
        self.log_file_path = None
        
        # Thêm các biến theo dõi từ log
        self.simulation_cur_time = None  # Thời gian hiện tại trong mô phỏng
        self.simulation_pre_time = None  # Thời gian trước đó trong mô phỏng
        self.unallocated_orders = 0      # Số đơn hàng chưa phân bổ
        self.ongoing_orders = 0          # Số đơn hàng đang xử lý
        self.completed_orders = 0        # Số đơn hàng đã hoàn thành
            
    def run_simulation(self, instance_id , algorithm_name = 'GA', socketio=None  ):
        """Run simulation for a specific instance"""
        self.current_instance = instance_id
        self.current_algorithm = algorithm_name
        self.running = True
        self.paused = False
        
        # Tạo log file
        log_file_name = f"dpdp_{datetime.datetime.now().strftime('%y%m%d%H%M%S')}.log"
        log_dir = "src/output/log"
        os.makedirs(log_dir, exist_ok=True)
        self.log_file_path = os.path.join(log_dir, log_file_name)
        ini_logger(log_file_name)
        
        # Thêm handler tùy chỉnh để bắt log
        log_handler = SocketIOHandler(self.output_queue, instance_id, socketio, self.log_file_path)
        logging.getLogger().addHandler(log_handler)
        
        # Emit event khi bắt đầu
        if socketio:
            socketio.emit('simulation_started', {
                'instance_id': instance_id,
                'timestamp': time.time()
            })
        
        try:
            logger.info(f"Starting simulation for {instance_id}")
            logger.info(f"Using algorithm: {algorithm_name}")
            
            # Sử dụng OutputCapturer để capture stdout và stderr
            with OutputCapturer(self.output_queue, instance_id, socketio, self.log_file_path) as _:
                idx = int(instance_id.split('_')[1])
                if idx <= 64:
                    score = simulate(
                        SimulatorConfigs.factory_info_file,
                        SimulatorConfigs.route_info_file,
                        instance_id,
                        algorithm_name
                    )
                else:
                    score = simulate(
                        SimulatorConfigs.customed_factory_info_file,
                        SimulatorConfigs.customed_route_info_file,
                        instance_id,
                        algorithm_name
                    )
                self.scores.append(score)
                logger.info(f"Score of {instance_id}: {score}")
                
                # Emit event khi hoàn thành
                if socketio:
                    socketio.emit('simulation_completed', {
                        'instance_id': instance_id,
                        'score': score,
                        'timestamp': time.time()
                    })
                
        except Exception as e:
            logger.error(f"Simulation failed: {e}\n{traceback.format_exc()}")
            self.scores.append(sys.maxsize)
            
            # Emit event khi có lỗi
            if socketio:
                socketio.emit('simulation_error', {
                    'error': str(e),
                    'timestamp': time.time()
                })
                
        finally:
            # Xóa handler tùy chỉnh
            logging.getLogger().removeHandler(log_handler)
            remove_file_handler_of_logging(log_file_name)
            self.running = False

    def parse_log_entry(self, log_entry):
        """Trích xuất thông tin từ log entry"""
        if not log_entry or 'message' not in log_entry:
            return
            
        message = log_entry['message']
        
        # Trích xuất thời gian mô phỏng (cur time và pre time)
        time_match = re.search(r'cur time: ([\d-]+ [\d:]+), pre time: ([\d-]+ [\d:]+)', message)
        if time_match:
            self.simulation_cur_time = time_match.group(1)
            self.simulation_pre_time = time_match.group(2)
        
        # Trích xuất thông tin đơn hàng
        orders_match = re.search(r'Get (\d+) unallocated order items, (\d+) ongoing order items, (\d+) completed order items', message)
        if orders_match:
            self.unallocated_orders = int(orders_match.group(1))
            self.ongoing_orders = int(orders_match.group(2))
            self.completed_orders = int(orders_match.group(3))

    def get_state(self):
        """Get current simulation state"""
        output_list = []
        while not self.output_queue.empty():
            output_list.append(self.output_queue.get())
        
        return {
            'running': self.running,
            'paused': self.paused,
            'current_instance': self.current_instance,
            'current_time': time.time(),
            'scores': self.scores,
            'output': output_list
        }


class OutputCapturer:
    """Context manager to capture simulator output (stdout and stderr)"""
    def __init__(self, queue, instance_id, socketio=None, log_file_path=None):
        self.queue = queue
        self.instance_id = instance_id
        self.socketio = socketio
        self.log_file_path = log_file_path
        self.original_stdout = None
        self.original_stderr = None
        self.log_file = None
        
    def __enter__(self):
        # Mở file log để ghi
        if self.log_file_path:
            self.log_file = open(self.log_file_path, 'a', encoding='utf-8')
        
        # Thay thế stdout và stderr
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        sys.stdout = self
        sys.stderr = self
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Khôi phục stdout và stderr
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr
        if self.log_file:
            self.log_file.close()
        
    def write(self, text):
        """Capture stdout and stderr writes"""
        if text:
            # Tách text thành các dòng
            lines = text.split('\n')
            timestamp = datetime.datetime.now().strftime('%H:%M:%S')
            
            for line in lines:
                if line.strip():  # Chỉ xử lý các dòng không rỗng
                    log_entry = {
                        'time': timestamp,
                        'message': line,
                        'instance': self.instance_id,
                        'level': 'info'
                    }
                    
                    # Phát hiện level log
                    if "ERROR" in line.upper() or "CRITICAL" in line.upper():
                        log_entry['level'] = 'error'
                    elif "WARNING" in line.upper():
                        log_entry['level'] = 'warning'
                    
                    # Thêm vào queue (sẽ được SocketIOHandler xử lý)
                    self.queue.put(log_entry)
                    
                    # Ghi vào file log
                    if self.log_file:
                        self.log_file.write(line + '\n')
                        self.log_file.flush()
            
            # Ghi ra stdout/stderr gốc
            self.original_stdout.write(text)
            self.original_stderr.write(text)
    
    def flush(self):
        self.original_stdout.flush()
        self.original_stderr.flush()
        if self.log_file:
            self.log_file.flush()


class SocketIOHandler(logging.Handler):
    """Custom logging handler to send logs to SocketIO"""
    def __init__(self, queue, instance_id, socketio=None, log_file_path=None):
        super().__init__()
        self.queue = queue
        self.instance_id = instance_id
        self.socketio = socketio
        self.log_file_path = log_file_path
        self.log_file = open(log_file_path, 'a', encoding='utf-8') if log_file_path else None
        self.log_buffer = []  # Buffer để gửi log theo lô
        self.last_flush = time.time()
        
    def handle_queue(self):
        """Process logs from queue"""
        while not self.queue.empty():
            log_entry = self.queue.get()
            if log_entry and all(key in log_entry for key in ['time', 'message', 'instance', 'level']):
                self.log_buffer.append(log_entry)
                
    def emit(self, record):
        """Handle logging record and queue items"""
        try:
            # Xử lý log từ logging
            msg = self.format(record)
            lines = msg.split('\n')
            timestamp = datetime.datetime.now().strftime('%H:%M:%S')
            
            for line in lines:
                if line.strip():
                    log_entry = {
                        'time': timestamp,
                        'message': line,
                        'instance': self.instance_id,
                        'level': record.levelname.lower()
                    }
                    self.log_buffer.append(log_entry)
                    
                    # Ghi vào file log
                    if self.log_file:
                        self.log_file.write(line + '\n')
                        self.log_file.flush()
            
            # Xử lý log từ queue (từ OutputCapturer)
            self.handle_queue()
            
            # Gửi buffer nếu đủ lớn hoặc sau 0.5 giây
            current_time = time.time()
            if len(self.log_buffer) >= 10 or (current_time - self.last_flush) >= 0.5:
                if self.socketio:
                    self.socketio.emit('log_update', self.log_buffer)
                self.log_buffer.clear()
                self.last_flush = current_time
                
        except Exception as e:
            print(f"Error in SocketIOHandler: {e}", file=sys.stderr)
            
    def close(self):
        # Gửi các log còn lại trong buffer
        if self.socketio and self.log_buffer:
            self.socketio.emit('log_update', self.log_buffer)
            self.log_buffer.clear()
        if self.log_file:
            self.log_file.close()
        super().close()