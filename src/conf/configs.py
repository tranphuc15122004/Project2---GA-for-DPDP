import os


class Configs(object):
    MAX_SCORE = 9999999999

    # 算法切片的时间间隔, time interval of simulator
    ALG_RUN_FREQUENCY = 10  # 单位分钟

    # 多目标权重之间的系数
    LAMDA = 10000

    # different pallet types of orders
    PALLET_TYPE_LABELS = ["PALLET", "HALF_PALLET", "BOX"]
    LABEL_TO_DEMAND_UNIT = {"PALLET": 1, "HALF_PALLET": 0.5, "BOX": 0.25}
    STANDARD_PALLET_LABEL = "PALLET"
    SMALL_PALLET_LABEL = "HALF_PALLET"
    BOX_LABEL = "BOX"

    # 订单状态 0: 初始(initialization), 1: 已生成(generated), 2: 进行中(ongoing), 3: 完成(Completed)
    ORDER_STATUS_TO_CODE = {"INITIALIZATION": 0, "GENERATED": 1, "ONGOING": 2, "COMPLETED": 3}

    # loading and unloading, 装卸货速度
    LOAD_SPEED = 0.25  # 大板/min, unit is standard pallet per minute
    UNLOAD_SPEED = 0.25  # 大板/min, unit is standard pallet per minute

    # 靠台时间
    DOCK_APPROACHING_TIME = 30 * 60  # unit: second

    # 文件路径
    root_folder_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    benchmark_folder_path = os.path.join(root_folder_path, "benchmark")
    src_folder_path = os.path.join(root_folder_path, "src")
    algorithm_folder_path = os.path.join(root_folder_path, "algorithm")
    output_folder = os.path.join(src_folder_path, "output")
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    route_info_file = "route_info.csv"
    factory_info_file = "factory_info.csv"
    customed_route_info_file = "route_info_customed.csv"
    customed_factory_info_file = "factory_info_customed.csv"
    route_info_file_path = os.path.join(benchmark_folder_path, route_info_file)
    factory_info_file_path = os.path.join(benchmark_folder_path, factory_info_file)

    algorithm_data_interaction_folder_path = os.path.join(algorithm_folder_path, "data_interaction")
    if not os.path.exists(algorithm_data_interaction_folder_path):
        os.makedirs(algorithm_data_interaction_folder_path)
    algorithm_vehicle_input_info_path = os.path.join(algorithm_data_interaction_folder_path, "vehicle_info.json")
    algorithm_unallocated_order_items_input_path = os.path.join(algorithm_data_interaction_folder_path,
                                                                "unallocated_order_items.json")
    algorithm_ongoing_order_items_input_path = os.path.join(algorithm_data_interaction_folder_path,
                                                            "ongoing_order_items.json")

    algorithm_output_destination_path = os.path.join(algorithm_data_interaction_folder_path, 'output_destination.json')
    algorithm_output_planned_route_path = os.path.join(algorithm_data_interaction_folder_path, 'output_route.json')

    # 算法入口文件名，不含扩展名
    ALGORITHM_ENTRY_FILE_NAME = 'main_algorithm'

    # 算法语言映射表
    ALGORITHM_LANGUAGE_MAP = {'py': 'python',
                              'class': 'java',
                              'exe': 'c',
                              'out': 'c',
                              }

    # 随机种子
    RANDOM_SEED = 0

    # 算法运行超时时间
    MAX_RUNTIME_OF_ALGORITHM = 600

    # 算法成功标识
    ALGORITHM_SUCCESS_FLAG = 'SUCCESS'

    # 日志文件的最大数量
    MAX_LOG_FILE_NUM = 100

    # 一天的秒数
    A_DAY_TIME_SECONDS = 24 * 60 * 60

    # 数据集选项，列表为空则选择所有数据集，如[]，[1], [1, 2, 3], [64]
    selected_instances = [79]
    """ selected_instances = [65 , 66 , 67 , 68 , 69 ,70 , 71, 72, 73, 74, 75, 76, 77, 78, 79, 80,
                          65 , 66 , 67 , 68 , 69 ,70 , 71, 72, 73, 74, 75, 76, 77, 78, 79, 80] """
    all_test_instances = [1 , 2 , 3 , 4 , 5 , 6 , 7 , 8 , 9 , 10, 11 , 12 , 13 , 14 , 15 , 16,
                            65 ,66 ,67 ,68 ,69 ,70 ,71,72 , 73 , 74 , 75 , 76 , 77 ,78 ,79 ,80]
    
    all_algorithms = ["GA","GA1LS","GA5LS","ACO","ACO5LS"]
