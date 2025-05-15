import traceback
from src.utils.logging_engine import logger
from algorithm.main import  main
import argparse

# Khởi tạo ArgumentParser
parser = argparse.ArgumentParser(description='DPDP Simulator')
parser.add_argument('--algorithm', type=str, default='default', help='Tên thuật toán sử dụng')

# Phân tích các tham số dòng lệnh
args = parser.parse_args()

if __name__ == '__main__':
    try:
        # Lấy tên thuật toán từ tham số dòng lệnh
        algorithm_name = args.algorithm
        main(algorithm_name)
        print("SUCCESS")
    except Exception as e:
        logger.error("Failed to run algorithm")
        logger.error(f"Error: {e}, {traceback.format_exc()}")
        print("FAIL")
