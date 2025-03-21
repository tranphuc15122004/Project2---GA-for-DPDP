import sys
import time
from typing import Dict , List
from algorithm.In_and_Out import *
from algorithm.Object import *
from algorithm.engine import *


input_directory = r'algorithm\data_interaction'

def main():
    begin_time = time.time()
    id_to_factory , route_map ,  id_to_vehicle , id_to_unlocated_items ,  id_to_ongoing_items , id_to_allorder = Input()
    
    vehicleid_to_plan: Dict[str , List[Node]]= {}
    vehicleid_to_destination : Dict[str , Node] = {}

    new_order_itemIDs : List[str] = []
    new_order_itemIDs = restore_scene_with_single_node(vehicleid_to_plan , id_to_ongoing_items, id_to_unlocated_items  , id_to_vehicle , id_to_factory ,id_to_allorder)

    new_order_itemIDs = [item for item in new_order_itemIDs if item]

    dispatch_new_orders(vehicleid_to_plan , id_to_factory , route_map , id_to_vehicle , id_to_unlocated_items , new_order_itemIDs)
    
    
    used_time = time.time() - begin_time
    update_solution_json(id_to_ongoing_items , id_to_unlocated_items , id_to_vehicle , vehicleid_to_plan , vehicleid_to_destination , route_map , used_time)
    
    merge_node(id_to_vehicle , vehicleid_to_plan)
    
    get_output_solution(id_to_vehicle , vehicleid_to_plan , vehicleid_to_destination)
    
    print( f"Destination: {vehicleid_to_destination}", file = sys.stderr)
    write_destination_json_to_file(vehicleid_to_destination   , input_directory)
    
    
    print(f"Route: {vehicleid_to_plan}", file = sys.stderr)
    write_route_json_to_file(vehicleid_to_plan  , input_directory) 

if __name__ == '__main__':
    main()