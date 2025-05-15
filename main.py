import traceback
import datetime
import numpy as np
import sys
from api.server import app, socketio
from src.conf.configs import Configs
from src.simulator.simulate_api import simulate
from src.utils.log_utils import ini_logger, remove_file_handler_of_logging
from src.utils.logging_engine import logger
# from naie.metrics import report
import argparse

# Khởi tạo ArgumentParser
parser = argparse.ArgumentParser(description='DPDP Simulator')
parser.add_argument('--algorithm', type=str, default='GA5LS', help='Tên thuật toán sử dụng')
parser.add_argument('--api', action='store_true', help='Chạy API server')

# Phân tích các tham số dòng lệnh
args = parser.parse_args()

if __name__ == "__main__":
    if args.api:
        print("Starting API server...")
        socketio.run(app, host='0.0.0.0', port=5000, debug=True)
    else:
        # Lấy tên thuật toán từ tham số dòng lệnh
        algorithm_name = args.algorithm
        
        print(f"Using algorithm: {algorithm_name}")
        
        # if you want to traverse all instances, set the selected_instances to []
        selected_instances = Configs.selected_instances

        if selected_instances:
            test_instances = selected_instances
        else:
            test_instances = Configs.all_test_instances

        score_list = []
        for idx in test_instances:
            # Initial the log
            log_file_name = f"dpdp_{datetime.datetime.now().strftime('%y%m%d%H%M%S')}.log"
            ini_logger(log_file_name)

            instance = "instance_%d" % idx
            logger.info(f"Start to run {instance}")

            try:
                if idx <= 64:
                    score = simulate(Configs.factory_info_file, Configs.route_info_file, instance , algorithm_name)
                else:
                    score = simulate(Configs.customed_factory_info_file, Configs.customed_route_info_file, instance , algorithm_name)
                
                score_list.append(score)
                logger.info(f"Score of {instance}: {score}")
            except Exception as e:
                logger.error("Failed to run simulator")
                logger.error(f"Error: {e}, {traceback.format_exc()}")
                score_list.append(sys.maxsize)

            remove_file_handler_of_logging(log_file_name)

        avg_score = np.mean(score_list)
        # with report(True) as logs:
        #     logs.log_metrics('score', [avg_score])
        print(score_list)
        print(avg_score)
        print("Happy Ending")
