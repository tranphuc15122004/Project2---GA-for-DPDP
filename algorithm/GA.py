import time
from typing import Dict , List , Tuple 
from algorithm.Object import *
from algorithm.algorithm_config import *    
import random
from algorithm.engine import *

def GA(initial_vehicleid_to_plane : Dict[str , List[Node]] ,route_map: Dict[Tuple, Tuple], id_to_vehicle: Dict[str, Vehicle] ,Unongoing_super_nodes : Dict[int , Dict[str, Node]] , Base_vehicleid_to_plan : Dict[str , List[Node]]) -> Chromosome:
    population : List[Chromosome] = []
    PDG_map : Dict[str , List[Node]] = {}
    population , PDG_map = generate_random_chromosome(initial_vehicleid_to_plane , route_map , id_to_vehicle , Unongoing_super_nodes , Base_vehicleid_to_plan , POPULATION_SIZE)

    if population is None:
        print('Cant initialize the population')
        return None

    best_solution : Chromosome = None
    stagnant_generations = 0  # Biến đếm số thế hệ không cải thiện
    time_of_1_gen = 0
    population.sort(key= lambda x: x.fitness)
    best_solution = population[0]
    begintime = time.time()
    
    for gen in range(NUMBER_OF_GENERATION):
        new_population = []
        
        new_population , _ = generate_random_chromosome(initial_vehicleid_to_plane , route_map , id_to_vehicle , Unongoing_super_nodes , Base_vehicleid_to_plan , 2 *  POPULATION_SIZE)
        
        while len(new_population) < 2* POPULATION_SIZE:
            parent1, parent2 = select_parents(population)
            child = parent1.crossover(parent2, PDG_map)
            new_population.append(child)
        
        # Sắp xếp lại quần thể và lấy 20 cá thể tốt nhất
        population.extend(new_population)
        population.sort(key=lambda x: x.fitness)
        population = population[:POPULATION_SIZE]

        for c in population:
            c.mutate(True)

        # Sắp xếp lại quần thể sau đột biến
        population.sort(key=lambda x: x.fitness)

        # Cập nhật giải pháp tốt nhất từ quần thể đã đột biến
        if best_solution is None or population[0].fitness < best_solution.fitness:
            best_solution = population[0]
            stagnant_generations = 0
        else:
            stagnant_generations += 1

        # Điều kiện dừng sớm nếu không có cải thiện
        if stagnant_generations >= 5:
            print("Stopping early due to lack of improvement.")
            break

        # Xu ly truong hop timeout
        endtime = time.time()
        if time_of_1_gen == 0:
            time_of_1_gen = endtime - begintime
        used_time = endtime - begintime + time_of_1_gen
        if used_time > 10 * 60:
            print("TimeOut!!")
            break
        
        print(f'Generation {gen+1}: Best Fitness = {best_solution.fitness}')
    return best_solution    

# Chọn lọc cha mẹ bằng phương pháp tournament selection
def select_parents(population: List[Chromosome]) -> Tuple[Chromosome, Chromosome]:
    def tournament_selection():
        tournament_size = max(2, len(population) // 10)
        candidates = random.sample(population, tournament_size)
        return min(candidates, key=lambda x: x.fitness)
    return tournament_selection(), tournament_selection()

def generate_random_chromosome(initial_vehicleid_to_plan : Dict[str , List[Node]],  route_map: Dict[Tuple, Tuple], id_to_vehicle: Dict[str, Vehicle], Unongoing_super_nodes : Dict[int , Dict[str, Node]]  ,Base_vehicleid_to_plan : Dict[str , List[Node]] , quantity : int):
    ls_node_pair_num = len(Unongoing_super_nodes)
    if ls_node_pair_num == 0:
        return None , None

    #Quan the
    population : List[Chromosome] = []
    number_of_node = 0
    for plan in initial_vehicleid_to_plan.values():
        number_of_node += len(plan)
    
    pdg_Map : Dict[str , List[Node]] = {}
    
    # tao Dict cac super node
    for idx, pdg in Unongoing_super_nodes.items():
        pickup_node = None
        delivery_node = None
        node_list: List[Node] = []
        pos_i = 0
        pos_j = 0
        d_num = len(pdg) // 2
        index = 0

        if pdg:
            vehicleID = ''
            for v_and_pos_str, node in (pdg.items()):
                vehicleID = v_and_pos_str.split(",")[0]
                if index % 2 == 0:
                    pos_i = int(v_and_pos_str.split(",")[1])
                    pickup_node = node
                    node_list.insert(0, pickup_node)
                    index += 1
                else:
                    pos_j = int(v_and_pos_str.split(",")[1])
                    delivery_node = node
                    node_list.append(delivery_node)
                    index += 1
                    pos_j = int(pos_j - d_num + 1)
            
            k : str = f"{vehicleID},{int(pos_i)}+{int(pos_j)}"
            pdg_Map[k] = node_list
    if len(pdg_Map) < 2:
        return None , None
    
    # Tao quan the
    while len(population) < quantity:
        temp_route: Dict[str , List[Node]] = {}
        for vehicleID , plan in Base_vehicleid_to_plan.items():
            temp_route[vehicleID] = []
            for node in plan:
                temp_route[vehicleID].append(node)
        
        # Chen ngau nhien cac super node vao cac lo trinh cua cac xe 
        for DPG in pdg_Map.values():
            # Khai bao cac bien lien quan
            # chen theo cách tốt nhất
            if random.uniform(0 , 1) <= 0.25:
                isExhausive = False
                route_node_list : List[Node] = []
                selected_vehicleID = random.choice(list(Base_vehicleid_to_plan.keys()))
                if DPG:
                    isExhausive , bestInsertVehicleID, bestInsertPosI, bestInsertPosJ , bestNodeList = dispatch_nodePair(DPG , id_to_vehicle , temp_route , route_map , selected_vehicleID)
                
                route_node_list = temp_route.get(bestInsertVehicleID , [])

                if isExhausive:
                    route_node_list = bestNodeList[:]
                else:
                    if route_node_list is None:
                        route_node_list = []
                    
                    new_order_pickup_node = DPG[0]
                    new_order_delivery_node = DPG[1]
                    
                    route_node_list.insert(bestInsertPosI, new_order_pickup_node)
                    route_node_list.insert(bestInsertPosJ, new_order_delivery_node)
                temp_route[bestInsertVehicleID] = route_node_list
            else:
                random_dispatch_nodePair(DPG , id_to_vehicle , temp_route)
                
        # Da tao xong mot ca the moi
        if len(temp_route) == len(id_to_vehicle):
            temp = 0
            for vehicle_route in temp_route.values():
                temp += len(vehicle_route)
            if temp == number_of_node:
                population.append(Chromosome(temp_route , route_map , id_to_vehicle ))
    population.append(Chromosome(initial_vehicleid_to_plan , route_map , id_to_vehicle))
    return population , pdg_Map 