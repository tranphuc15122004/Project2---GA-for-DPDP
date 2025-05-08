import os
import traceback
import datetime
import sys
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
        self.output_queue = Queue()
        self.scores = []
        self.log_file_path = None
        
    def start_log_streaming(self, log_file_path):
        """Stream log file to clients via Socket.IO"""
        self.log_file_path = log_file_path
        
        def stream_log():
            # Import socketio ở đây để tránh circular import
            from api.server import socketio
            
            try:
                with open(log_file_path, 'r') as log_file:
                    # Di chuyển đến cuối file
                    log_file.seek(0, 2)
                    
                    while self.running:
                        if not self.paused:
                            line = log_file.readline()
                            if line:
                                timestamp = datetime.datetime.now().strftime('%H:%M:%S')
                                log_entry = {
                                    'time': timestamp,
                                    'message': line.strip(),
                                    'instance': self.current_instance
                                }
                                socketio.emit('log_update', log_entry)
                        else:
                            # Nếu đang tạm dừng, ngủ một lúc để giảm tải CPU
                            time.sleep(0.5)
                            
                        # Ngủ một chút để giảm tải CPU
                        time.sleep(0.1)
            except Exception as e:
                print(f"Error streaming log: {e}")
                
        # Chạy streaming trong một thread riêng
        log_thread = Thread(target=stream_log, daemon=True)
        log_thread.start()
    
    def run_simulation(self, instance_id):
        """Run simulation for a specific instance"""
        self.current_instance = instance_id
        self.running = True
        self.paused = False
        
        # Tạo log file và bắt đầu streaming
        log_file_name = f"dpdp_{datetime.datetime.now().strftime('%y%m%d%H%M%S')}.log"
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        log_file_path = os.path.join(log_dir, log_file_name)
        ini_logger(log_file_name)
        
        # Bắt đầu streaming log
        self.start_log_streaming(log_file_path)
        
        try:
            logger.info(f"Starting simulation for {instance_id}")
            
            # Sử dụng OutputCapturer để capture stdout
            with OutputCapturer(self.output_queue, instance_id) as _:
                score = simulate(
                    SimulatorConfigs.factory_info_file,
                    SimulatorConfigs.route_info_file,
                    instance_id
                )
                self.scores.append(score)
                logger.info(f"Score of {instance_id}: {score}")
                
        except Exception as e:
            logger.error(f"Simulation failed: {e}\n{traceback.format_exc()}")
            self.scores.append(sys.maxsize)
        finally:
            remove_file_handler_of_logging(log_file_name)
            self.running = False

    def get_state(self):
        """Get current simulation state"""
        output_list = []
        while not self.output_queue.empty():
            output_list.append(self.output_queue.get())
            
        return {
            'running': self.running,
            'paused': self.paused,
            'current_instance': self.current_instance,
            'current_time': 0,  # Placeholder, update with actual time if available
            'scores': self.scores,
            'output': output_list
        }

class OutputCapturer:
    """Context manager to capture simulator output"""
    def __init__(self, queue, instance_id):
        self.queue = queue
        self.instance_id = instance_id
        self.original_stdout = None
        
    def __enter__(self):
        self.original_stdout = sys.stdout
        sys.stdout = self
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout = self.original_stdout
        
    def write(self, text):
        """Capture stdout writes"""
        if text.strip():
            timestamp = datetime.datetime.now().strftime('%H:%M:%S')
            log_entry = {
                'time': timestamp,
                'message': text.strip(),
                'instance': self.current_instance
            }
            
            # Thêm vào queue để lưu lịch sử
            self.queue.put(log_entry)
            
            # Gửi trực tiếp qua socket.io
            try:
                from api.server import socketio
                socketio.emit('log_update', log_entry)
            except Exception as e:
                print(f"Error sending log via socketio: {e}")
            
            # Ghi ra stdout gốc
            self.original_stdout.write(text)
            
    def flush(self):
        self.original_stdout.flush()