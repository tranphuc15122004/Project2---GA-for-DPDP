import sys
import math
from typing import Dict , List
import copy
import time
from algorithm.Object import Node, Vehicle, OrderItem
from algorithm.algorithm_config import *
from algorithm.engine import *
from algorithm.local_search import * 


def inter_couple_exchange(vehicleid_to_plan: Dict[str , List[Node]], id_to_vehicle: Dict[str , Vehicle] , route_map: Dict[tuple , tuple] , is_limited : bool = False ):    
    is_improved = False

    dis_order_super_node , _ = get_UnongoingSuperNode(vehicleid_to_plan , id_to_vehicle)
    
    ls_node_pair_num = len(dis_order_super_node)
    
    if ls_node_pair_num == 0:
        return False
    vehicleID = ""
    pdg_Map : Dict[str , List[Node]] = {}
    
    for idx, pdg in dis_order_super_node.items():
        pickup_node = None
        delivery_node = None
        node_list: List[Node] = []
        pos_i = 0
        pos_j = 0
        d_num = len(pdg) // 2
        index = 0

        if pdg:
            for v_and_pos_str, node in pdg.items():
                if index % 2 == 0:
                    vehicleID = v_and_pos_str.split(",")[0]
                    pos_i = int(v_and_pos_str.split(",")[1])
                    pickup_node = node
                    node_list.insert(0, pickup_node)
                    index += 1
                else:
                    pos_j = int(v_and_pos_str.split(",")[1])
                    delivery_node = node
                    node_list.append(delivery_node)
                    index += 1
                    pos_j = pos_j - d_num + 1

            k : str = f"{vehicleID},{int(pos_i)}+{int(pos_j)}"
            pdg_Map[k] = node_list
            
    if len(pdg_Map) < 2:
        return False
    #print(pdg_Map, file = sys.stderr)
    
    vehicle = id_to_vehicle.get(vehicleID , None)
    route_node_list = vehicleid_to_plan.get(vehicleID)
    cost0 = cost_of_a_route(route_node_list, vehicle , id_to_vehicle , route_map , vehicleid_to_plan)
    min_cost = cost0

    min_cost_pdg1_key_str : str = None
    min_cost_pdg2_key_str :str = None
    min_cost_pdg1 : List[Node]= None
    min_cost_pdg2 : List[Node]= None

    idx_i = 0
    idx_j = 0
    for before_key , before_DPG in pdg_Map.items():
        before_vehicle = id_to_vehicle.get(before_key.split(",")[0])
        before_posI = int(before_key.split(",")[1].split("+")[0])
        before_posJ = int(before_key.split(",")[1].split("+")[1])
        d1num = len(before_DPG) // 2
        
        idx_j = 0
        for next_key , next_DPG in pdg_Map.items():
            if idx_i >= idx_j:
                idx_j += 1
                continue
            
            next_vehicle = id_to_vehicle.get(next_key.split(",")[0])
            next_posI = int(next_key.split(",")[1].split("+")[0])
            next_posJ = int(next_key.split(",")[1].split("+")[1])
            d2num = len(next_DPG) // 2
            if before_vehicle is next_vehicle:
                continue
            
            route_node_list1 = vehicleid_to_plan.get(before_vehicle.id , [])
            route_node_list2 = vehicleid_to_plan.get(next_vehicle.id , [])
            
            temp1 = route_node_list1[before_posI: before_posI + d1num]
            temp11 = route_node_list1[before_posJ: before_posJ + d1num]
            temp2 = route_node_list2[next_posI: next_posI + d2num]
            temp22 = route_node_list2[next_posJ: next_posJ + d2num]
            
            del route_node_list1[before_posI: before_posI + d1num]
            del route_node_list2[next_posI: next_posI + d2num]
            route_node_list1[before_posI:before_posI] = temp2
            route_node_list2[next_posI:next_posI] = temp1
            
            real_before_post_j = before_posJ + (d2num - d1num)
            real_next_post_j = next_posJ + (d1num - d2num)
            
            del route_node_list1[real_before_post_j: real_before_post_j + d1num]
            if len(route_node_list2) < real_next_post_j + d2num:
                print(222 , file= sys.stderr)
            del route_node_list2[real_next_post_j: real_next_post_j + d2num]
            
            route_node_list1[real_before_post_j:real_before_post_j] = temp22
            route_node_list2[real_next_post_j:real_next_post_j] = temp11
            
            carry_items = next_vehicle.carrying_items if next_vehicle.des else []
            cost1 = float('inf') if not isFeasible(route_node_list2 , carry_items , next_vehicle.board_capacity) else cost_of_a_route(route_node_list1, before_vehicle , id_to_vehicle , route_map , vehicleid_to_plan)
            
            if cost1 < min_cost:
                min_cost = cost1
                is_improved = True
                min_cost_pdg1_key_str = before_key
                min_cost_pdg2_key_str = next_key
                min_cost_pdg1 = before_DPG[:]
                min_cost_pdg2 = next_DPG[:]
            
            del route_node_list1[real_before_post_j: real_before_post_j + d2num]
            del route_node_list2[real_next_post_j: real_next_post_j + d1num]
            route_node_list1[real_before_post_j:real_before_post_j] = temp11
            route_node_list2[real_next_post_j:real_next_post_j] = temp22
            
            del route_node_list1[before_posI: before_posI + d2num]
            del route_node_list2[next_posI: next_posI + d1num]
            route_node_list1[before_posI:before_posI] = temp1
            route_node_list2[next_posI:next_posI] = temp2
            
            idx_j += 1
            if is_improved and is_limited:
                break
        
        if is_improved and is_limited:
            break    
        
        idx_i += 1
    
    if is_improved:
        before_DPG = min_cost_pdg1
        before_key = min_cost_pdg1_key_str
        before_vehicle = id_to_vehicle.get(before_key.split(",")[0])
        before_posI = int(before_key.split(",")[1].split("+")[0])
        before_posJ = int(before_key.split(",")[1].split("+")[1])
        d1num = len(before_DPG) // 2
        
        next_key = min_cost_pdg2_key_str
        next_DPG = min_cost_pdg2
        next_vehicle = id_to_vehicle.get(next_key.split(",")[0])
        next_posI = int(next_key.split(",")[1].split("+")[0])
        next_posJ = int(next_key.split(",")[1].split("+")[1])
        d2num = len(next_DPG) // 2
        
        route_node_list1 = vehicleid_to_plan.get(before_vehicle.id , [])
        route_node_list2 = vehicleid_to_plan.get(next_vehicle.id , [])
        
        temp1 = route_node_list1[before_posI: before_posI + d1num]
        temp11 = route_node_list1[before_posJ: before_posJ + d1num]
        temp2 = route_node_list2[next_posI: next_posI + d2num]
        temp22 = route_node_list2[next_posJ: next_posJ + d2num]
        
        del route_node_list1[before_posI: before_posI + d1num]
        del route_node_list2[next_posI: next_posI + d2num]
        
        route_node_list1[before_posI:before_posI] = temp2
        route_node_list2[next_posI:next_posI] = temp1
        
        real_before_post_j = before_posJ + (d2num - d1num)
        real_next_post_j = next_posJ + (d1num - d2num)
        
        del route_node_list1[real_before_post_j: real_before_post_j + d1num]
        del route_node_list2[real_next_post_j: real_next_post_j + d2num]
        
        route_node_list1[real_before_post_j:real_before_post_j] = temp22
        route_node_list2[real_next_post_j:real_next_post_j] = temp11
        
        vehicleid_to_plan[before_vehicle.id] = route_node_list1
        vehicleid_to_plan[next_vehicle.id] = route_node_list2

    return is_improved

def block_exchange(vehicleid_to_plan: Dict[str , List[Node]], id_to_vehicle: Dict[str , Vehicle] , route_map: Dict[tuple , tuple] , is_limited : bool = False):
    is_improved = False
    dis_order_super_node , _ = get_UnongoingSuperNode(vehicleid_to_plan , id_to_vehicle)
    
    ls_node_pair_num = len(dis_order_super_node)
    if ls_node_pair_num == 0:
        return False
    
    vehicleID = None
    block_map : Dict[str , List[Node]] = {}
    for idx , pdg in dis_order_super_node.items():
        pickup_node : Node = None
        delivery_node : Node = None
        node_list :List[Node] = []
        posI :int =0 ; posJ : int= 0
        dNum : int= len(pdg) // 2
        index :int= 0
        if pdg:
            for v_and_pos_str, node in pdg.items():
                if index % 2 == 0:
                    vehicleID = v_and_pos_str.split(",")[0]
                    posI = int(v_and_pos_str.split(",")[1])
                    pickup_node = node
                    node_list.insert(0, pickup_node)
                    index += 1
                else:
                    posJ = int(v_and_pos_str.split(",")[1])
                    delivery_node = node
                    node_list.append(delivery_node)
                    index += 1
                    posJ = posJ - dNum + 1
                    
            vehicle_node_route : List[Node] = vehicleid_to_plan.get(vehicleID , [])
            for i in range(posI + dNum , posJ):
                node_list.insert(i - posI , vehicle_node_route[i])
            k : str = f"{vehicleID},{posI}+{posJ + dNum - 1}"    
            block_map[k] = node_list
    if len(block_map)  <2:
        return False
    
    origin_cost = total_cost(id_to_vehicle , route_map , vehicleid_to_plan)
        
    min_cost = origin_cost
    min_cost_block1_key_str : str = None
    min_cost_block2_key_str :str = None
    min_cost_block1 : List[Node] = None
    min_cost_block2 : List[Node] = None
    idxI = 0
    idxJ = 0
    
    for before_key , before_block in block_map.items():
        before_vehicle = id_to_vehicle.get(before_key.split(",")[0])
        before_posI = int(before_key.split(",")[1].split("+")[0])
        before_posJ = int(before_key.split(",")[1].split("+")[1])
        block1_len = len(before_block)
        
        idxJ = 0
        for next_key , next_block in block_map.items():
            if idxI >= idxJ: 
                idxJ +=1
                continue
            
            next_vehicle = id_to_vehicle.get(next_key.split(",")[0])
            next_posI = int(next_key.split(",")[1].split("+")[0])
            next_posJ = int(next_key.split(",")[1].split("+")[1])
            block2_len = len(next_block) 
            
            route_node_list1 = vehicleid_to_plan.get(before_vehicle.id , [])
            route_node_list2 = vehicleid_to_plan.get(next_vehicle.id , [])
            
            if before_vehicle is not next_vehicle: 
                temp1 : List[Node]= route_node_list1[before_posI : before_posI + block1_len]
                temp2 : List[Node]= route_node_list2[next_posI : next_posI + block2_len]
                
                del route_node_list1[before_posI : before_posI + block1_len]
                del route_node_list2[next_posI : next_posI + block2_len]
                route_node_list1[before_posI: before_posI] = temp2
                route_node_list2[next_posI: next_posI] = temp1
                
                carrying_items : List[OrderItem] = []
                cost1 = 0.0
                if next_vehicle.des is not None: 
                    carrying_items = next_vehicle.carrying_items
                if not isFeasible(route_node_list2, carrying_items , next_vehicle.board_capacity):
                    cost1 = math.inf
                else:
                    cost1 = cost_of_a_route(route_node_list1 , before_vehicle , id_to_vehicle , route_map , vehicleid_to_plan)
                
                if cost1 < min_cost:
                    is_improved = True
                    min_cost_block1_key_str = before_key
                    min_cost_block2_key_str = next_key
                    min_cost_block1  = before_block[:]
                    min_cost_block2 = next_block[:]

                del route_node_list1[before_posI : before_posI + block2_len]
                del route_node_list2[next_posI : next_posI + block1_len]
                route_node_list1 [before_posI: before_posI] = temp1
                route_node_list2 [next_posI: next_posI] = temp2
            else:
                if before_posJ < next_posI or next_posJ < before_posI:
                    if before_posJ < before_posI:
                        before_posI, next_posI = next_posI, before_posI
                        before_posJ, next_posJ = next_posJ, before_posJ
                        block1_len, block2_len = block2_len, block1_len

                    temp1 = route_node_list1[before_posI: before_posI + block1_len]
                    temp2 = route_node_list1[next_posI: next_posI + block2_len]

                    del route_node_list1[next_posI: next_posI + block2_len]
                    del route_node_list1[before_posI: before_posI + block1_len]

                    route_node_list1[before_posI:before_posI] = temp2
                    real_next_post_i = next_posI + (block2_len - block1_len)
                    route_node_list1[real_next_post_i:real_next_post_i] = temp1

                    cost1 = cost_of_a_route(route_node_list1, before_vehicle , id_to_vehicle , route_map , vehicleid_to_plan )
                    if cost1 < min_cost:
                        is_improved = True
                        min_cost_block1_key_str = before_key
                        min_cost_block2_key_str = next_key
                        min_cost_block1 = before_block[:]
                        min_cost_block2 = next_block[:]

                    del route_node_list1[real_next_post_i: real_next_post_i + block1_len]
                    del route_node_list1[before_posI: before_posI + block2_len]
                    route_node_list1[before_posI:before_posI] = temp1
                    route_node_list1[next_posI:next_posI] = temp2
            
            if is_improved and is_limited:
                break
            idxJ +=1
        if is_improved and is_limited:
            break
        idxI +=1
    
    if is_improved:
        before_key = min_cost_block1_key_str
        before_vid, before_positions = before_key.split(",")
        before_post_i, before_post_j = map(int, before_positions.split("+"))
        before_block = min_cost_block1[:]
        block1_len = len(before_block)

        next_key = min_cost_block2_key_str
        next_vid, next_positions = next_key.split(",")
        next_post_i, next_post_j = map(int, next_positions.split("+"))
        next_dpg = min_cost_block2[:]
        block2_len = len(next_dpg)

        route_node_list1 = vehicleid_to_plan.get(before_vid, [])
        if before_vid != next_vid:
            route_node_list2 = vehicleid_to_plan.get(next_vid, [])
            temp1 = route_node_list1[before_post_i:before_post_j + 1]
            temp2 = route_node_list2[next_post_i:next_post_j + 1]

            del route_node_list1[before_post_i:before_post_i + block1_len]
            del route_node_list2[next_post_i:next_post_i + block2_len]
            
            route_node_list1[before_post_i:before_post_i] = temp2
            route_node_list2[next_post_i:next_post_i] = temp1
            
            vehicleid_to_plan[before_vid] = route_node_list1
            vehicleid_to_plan[next_vid] = route_node_list2
        else:
            temp1 = route_node_list1[before_post_i:before_post_i + block1_len]
            temp2 = route_node_list1[next_post_i:next_post_i + block2_len]

            del route_node_list1[next_post_i:next_post_i + block2_len]
            del route_node_list1[before_post_i:before_post_i + block1_len]

            route_node_list1[before_post_i:before_post_i] = temp2
            real_next_post_i = next_post_i + (block2_len - block1_len)
            route_node_list1[real_next_post_i:real_next_post_i] = temp1
            
            vehicleid_to_plan[before_vid] = route_node_list1

    return is_improved


def block_relocate(vehicleid_to_plan: Dict[str , List[Node]], id_to_vehicle: Dict[str , Vehicle] , route_map: Dict[tuple , tuple] , is_limited: bool = False ):
    is_improved = False
    dis_order_super_node ,_ = get_UnongoingSuperNode(vehicleid_to_plan , id_to_vehicle)
    ls_node_pair_num = len(dis_order_super_node)
    if ls_node_pair_num == 0:
        return False
    
    vehicleID = None
    block_map : Dict[str , List[Node]] = {}
    for idx , pdg in dis_order_super_node.items():
        pickup_node : Node = None
        delivery_node : Node = None
        node_list :List[Node] = []
        posI :int =0 ; posJ : int= 0
        dNum : int= len(pdg) // 2
        index :int= 0
        if pdg:
            for v_and_pos_str, node in pdg.items():
                if index % 2 == 0:
                    vehicleID = v_and_pos_str.split(",")[0]
                    posI = int(v_and_pos_str.split(",")[1])
                    pickup_node = node
                    node_list.insert(0, pickup_node)
                    index += 1
                else:
                    posJ = int(v_and_pos_str.split(",")[1])
                    delivery_node = node
                    node_list.append(delivery_node)
                    index += 1
                    posJ = posJ - dNum + 1
                    
            vehicle_node_route : List[Node] = vehicleid_to_plan.get(vehicleID , [])
            for i in range(posI + dNum , posJ):
                node_list.insert(i - posI , vehicle_node_route[i])
            k : str = f"{vehicleID},{posI}+{posJ + dNum - 1}"    
            block_map[k] = node_list
    
    if len(block_map)  <2:
        return False
    
    origin_cost = total_cost(id_to_vehicle , route_map , vehicleid_to_plan)

    min_cost = origin_cost
    best_relocate_vehicleID : str = None
    best_relocate_pos : int = 0
    min_cost_block1_key_str:  str = None
    best_relocate_block : List[Node] = None
    for before_key , before_block in block_map.items():
        before_vid, before_pos = before_key.split(",")
        before_post_i, before_post_j = map(int, before_pos.split("+"))
        before_vehicle = id_to_vehicle.get(before_vid)
        block1_len = len(before_block)
        route_node_list1 = vehicleid_to_plan.get(before_vid, [])
        
        del route_node_list1[before_post_i: before_post_i + block1_len]
        
        for index, (vehicle_id, vehicle) in enumerate(id_to_vehicle.items(), start=1):
            vehicle_id = f"V_{index}"
            route_node_list = vehicleid_to_plan.get(vehicle_id, [])
            node_list_size = len(route_node_list)
            insert_pos = 1 if vehicle.des else 0
            
            for i in range(insert_pos, node_list_size + 1):
                route_node_list[i:i] = before_block  # Chèn block vào vị trí i
                current_cost = cost_of_a_route(route_node_list, vehicle , id_to_vehicle , route_map , vehicleid_to_plan )
                
                if current_cost < min_cost:
                    min_cost = current_cost
                    is_improved = True
                    min_cost_block1_key_str = before_key
                    best_relocate_block = list(before_block)
                    best_relocate_vehicleID = vehicle_id
                    best_relocate_pos = i
                
                del route_node_list[i:i + block1_len]  # Xóa block sau khi kiểm tra
                if is_improved and is_limited:
                    break
        
        route_node_list1[before_post_i:before_post_i] = before_block  # Khôi phục dữ liệu ban đầu
        if is_improved and is_limited: 
            break

    if is_improved:
        before_vid, before_pos = min_cost_block1_key_str.split(",")
        before_post_i, before_post_j = map(int, before_pos.split("+"))
        origin_route_node_list = vehicleid_to_plan.get(before_vid, [])
        del origin_route_node_list[before_post_i: before_post_i + len(best_relocate_block)]
        
        vehicleid_to_plan[before_vid] = origin_route_node_list

        best_relocate_route = vehicleid_to_plan.get(best_relocate_vehicleID, [])
        best_relocate_route[best_relocate_pos:best_relocate_pos] = best_relocate_block
        
        vehicleid_to_plan[best_relocate_vehicleID] = best_relocate_route

    return is_improved

def multi_pd_group_relocate(vehicleid_to_plan: Dict[str , List[Node]], id_to_vehicle: Dict[str , Vehicle] , route_map: Dict[tuple , tuple] , is_limited : bool = False):
    is_improved = False
    cp_vehicle_id2_planned_route : Dict [str , List [Node]]= {}
    for key , value in vehicleid_to_plan.items():
        cp_vehicle_id2_planned_route[key] = []
        for node in value:
            cp_vehicle_id2_planned_route[key].append(node)
    #cp_vehicle_id2_planned_route = copy.deepcopy(vehicleid_to_plan)
    dis_order_super_node,  _ = get_UnongoingSuperNode(vehicleid_to_plan , id_to_vehicle)
    ls_node_pair_num = len(dis_order_super_node)
    if ls_node_pair_num == 0:
        return False
    formal_super_node : Dict[int, Dict[str , List[Node]]]= {}
    new_formal_super_node : Dict[int, Dict[str , List[Node]]]= {}
    new_cost_delta = [math.inf] * ls_node_pair_num
    
    for idx, pdg in dis_order_super_node.items():
        if not pdg or len(pdg) == 0:
            continue
        
        pickup_node : Node = None ; delivery_node : Node = None
        node_list = []
        index = 0
        d_num = len(pdg) // 2
        vehicle_id = None
        pos_i, pos_j = 0, 0
        
        if pdg: 
            # Them toan cac super node vao nodelist
            for v_and_pos_str , node in pdg.items():
                if index % 2 == 0:
                    vehicle_id, pos_i = v_and_pos_str.split(",")
                    pos_i = int(pos_i)
                    pickup_node =  node
                    node_list.insert(0, pickup_node)
                else:
                    pos_j = int(v_and_pos_str.split(",")[1])
                    delivery_node = node
                    node_list.append(delivery_node)
                    pos_j = pos_j - d_num + 1
                index += 1
            
            k = f"{vehicle_id},{pos_i}+{pos_j}"
            pdg_hash_map : Dict[str , List[Node]] = {k: node_list}
            formal_super_node[idx] = pdg_hash_map
            new_formal_super_node[idx] = pdg_hash_map
        
        
        route_node_list : List[Node] = cp_vehicle_id2_planned_route.get(vehicle_id , [])
        vehicle = id_to_vehicle.get(vehicle_id)
        
        cost_after_insertion = single_vehicle_cost(route_node_list , vehicle , route_map )
        
        del route_node_list[pos_i : pos_i + d_num]
        del route_node_list[pos_j - d_num : pos_j]
        cp_vehicle_id2_planned_route[vehicle_id] = route_node_list
        
        cost_before_insertion = single_vehicle_cost(route_node_list , vehicle , route_map )
        curr_cost_detal = cost_after_insertion - cost_before_insertion
        
        min_cost_delta, best_insert_pos_i, best_insert_pos_j, best_insert_vehicle_id = dispatch_order_to_best(node_list , cp_vehicle_id2_planned_route , id_to_vehicle , route_map)
        
        if min_cost_delta < curr_cost_detal:
            new_cost_delta[idx] = min_cost_delta
            pdg_hash_map : Dict[str , List[Node]] = {}
            k = f"{best_insert_vehicle_id},{best_insert_pos_i}+{best_insert_pos_j}"
            pdg_hash_map[k] = node_list
            new_formal_super_node[idx] = pdg_hash_map
        
        route_node_list[pos_i:pos_i] = node_list[0 : len(node_list) // 2]
        route_node_list[pos_j:pos_j] = node_list[len(node_list) // 2 : len(node_list)]

    cost_delta_temp : List[float] = new_cost_delta[:]
    sort_index = sorted(range(ls_node_pair_num), key=lambda k: cost_delta_temp[k])
    mask = [False] * len(id_to_vehicle)
    orgin_cost = -1.0
    final_cost = -1.0
    is_improved = False
    for i in range(ls_node_pair_num):
        if new_cost_delta[i] != math.inf:
            before_super_node_map = formal_super_node[sort_index[i]]
            new_super_node_map = new_formal_super_node[sort_index[i]]

            before_key = next(iter(before_super_node_map))
            before_vid, before_pos = before_key.split(',')
            before_post_i, before_post_j = map(int, before_pos.split('+'))
            before_dpg = before_super_node_map[before_key]
            d_num = len(before_dpg) // 2
            before_vehicle_idx = int(before_vid.split('_')[1]) - 1

            new_key = next(iter(new_super_node_map))
            new_vid, new_pos = new_key.split(',')
            new_post_i, new_post_j = map(int, new_pos.split('+'))
            new_dpg = new_super_node_map[new_key]
            new_vehicle_idx = int(new_vid.split('_')[1]) - 1

            if not mask[before_vehicle_idx] and not mask[new_vehicle_idx]:
                before_route_node_list = copy.deepcopy(vehicleid_to_plan.get(before_vid, []))
                before_vehicle = id_to_vehicle[before_vid]
                cost0 = cost_of_a_route(before_route_node_list, before_vehicle , id_to_vehicle , route_map , vehicleid_to_plan )
                if orgin_cost < 0:
                    orgin_cost = cost0

                del before_route_node_list[before_post_i:before_post_i + d_num]
                del before_route_node_list[before_post_j - d_num:before_post_j]
                vehicleid_to_plan[before_vid] = before_route_node_list

                new_route_node_list = copy.deepcopy(vehicleid_to_plan.get(new_vid, []))
                new_vehicle = id_to_vehicle[new_vid]

                new_route_node_list[new_post_i:new_post_i] = new_dpg[:d_num]
                new_route_node_list[new_post_j:new_post_j] = new_dpg[d_num:]
                cost1 = cost_of_a_route(new_route_node_list, new_vehicle , id_to_vehicle , route_map , vehicleid_to_plan)

                if cost0 <= cost1:
                    before_route_node_list[before_post_i:before_post_i] = before_dpg[:d_num]
                    before_route_node_list[before_post_j:before_post_j] = before_dpg[d_num:]
                    vehicleid_to_plan[before_vid] = before_route_node_list
                else:
                    final_cost = cost1
                    mask[before_vehicle_idx] = True
                    mask[new_vehicle_idx] = True
                    is_improved = True
                    vehicleid_to_plan[new_vid] = new_route_node_list
                    
                    if is_limited:
                        break
    
    return is_improved
