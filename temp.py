import traceback
import datetime
import numpy as np
import sys
from api.server import app, socketio
from src.common.dispatch_result import DispatchResult
from src.conf.configs import Configs
from src.simulator.simulate_api import __initialize, simulate
from src.utils.json_tools import get_output_of_algorithm
from src.utils.log_utils import ini_logger, remove_file_handler_of_logging
from src.utils.logging_engine import logger
# from naie.metrics import report
import argparse

if __name__ == "__main__":
    instance = "instance_65"
    simulate_env = __initialize(Configs.customed_factory_info_file, Configs.customed_route_info_file,  instance)
    if simulate_env is not None:
        # 模拟器仿真过程
        simulate_env.run('GA5LS')
        
    vehicle_id_to_destination, vehicle_id_to_planned_route = get_output_of_algorithm(self.id_to_order_item)
    dispatch_result = DispatchResult(vehicle_id_to_destination, vehicle_id_to_planned_route)