import numpy as np
import scipy.optimize as optimize
from random import randint
import sys

def init_simulation(num_nodes, 
                    num_days, 
                    icu_capacities = None, 
                    transport_capacities = None, 
                    ini_path = None, 
                    demand_min = 80, 
                    demand_max = 90,
                    icu_min = 10,
                    icu_max = 300,
                    transport_min = 20,
                    transport_max = 30):
    if ini_path:
        print("you can also upload an .ini file")
        raise NotImplemented
    else:
        demand = []
        for node in range(num_nodes):
            demand.append(list(np.random.randint(demand_min, demand_max, size = num_days)))
        
        icu_capacities = icu_capacities if icu_capacities else list(np.random.randint(icu_min, 
                                                                                      icu_max, 
                                                                                      size = num_nodes))
        transport_capacities = transport_capacities if transport_capacities else list(np.random.randint(transport_min, 
                                                                                                        transport_max, 
                                                                                                        size = num_nodes)) 
    return icu_capacities, transport_capacities, demand


def calculate_outgoing(array,day,node):
    """
    Returns the total movements from a given node on a given day.
    Arguments: Movement Array, Day, Node
    """
    
    return sum(array[day][node])


def calculate_incoming(array,day,node):
    """
    Returns the total movements to a given node on a given day.
    Arguments: Movement Array, Day, Node
    """
    num_nodes = array.shape[1]
    
    total_outgoing = 0
    for n in range(num_nodes):
        total_outgoing = total_outgoing + array[day][n][node]
    return total_outgoing


def demand_day_node_raw(node_capacity, demand_day, left_day, received_day, demand_previous_days, left_previous_days, received_previous_days):
    return demand_day - left_day + received_day+ min(demand_previous_days-left_previous_days+received_previous_days, node_capacity)


def demand_day_node(movements, scenario_info, day, node):
    num_days = scenario_info['num_days']
    num_nodes = scenario_info['num_nodes']
    
    movements_res = np.reshape(movements,(num_days,num_nodes,num_nodes))
    total_received_patients = 0
    total_outbound_patients = 0
    accumulated_demand = 0
    for d in range(day):
        total_received_patients = total_received_patients + calculate_incoming(movements_res, d, node)
        total_outbound_patients = total_outbound_patients + calculate_outgoing(movements_res, d, node)
    accumulated_demand = sum(scenario_info['demands'][node][:day])
    
    demand = max(0, demand_day_node_raw(scenario_info['node_capacities'][node],
                                        scenario_info['demands'][node][day], 
                                        calculate_outgoing(movements_res,day,node),
                                        calculate_incoming(movements_res,day,node),
                                        accumulated_demand, 
                                        total_outbound_patients, 
                                        total_received_patients                
                ))
    return demand

def calc_daily_deaths(movements, scenario_info):
    """
    Returns deaths per death type:
    * unattended: deaths because of lack of bed
    * transport: deaths due to transport
    * total: total deaths
    
    each is a ndarray, time as one dimension, hospital/node as another.
    For transport, the originating node is considered as source of death
    """
    num_days = scenario_info['num_days']
    num_nodes = scenario_info['num_nodes']
    
    deaths = { 'unattended' : np.zeros((num_days, num_nodes))
              , 'transport' : np.zeros((num_days, num_nodes))
              , 'total' : np.zeros((num_days, num_nodes))}
    
    total = 0
    movements_res = np.reshape(movements,(num_days,num_nodes,num_nodes))
    for node in range(num_nodes):
        for day in range(num_days):
            deaths_not_attended = max(0, demand_day_node(movements, scenario_info, day,node) - scenario_info['node_capacities'][node])
            deaths_transport = movements_res[day, node].sum()
            deaths['unattended'][day, node] = deaths_not_attended
            deaths['transport'][day, node] = deaths_transport
            deaths['total'][day, node] = deaths_not_attended + deaths_transport
    return deaths

def calc_total_deaths(movements, scenario_info):
    num_days = scenario_info['num_days']
    num_nodes = scenario_info['num_nodes']
    total = 0
    movements_res = np.reshape(movements,(num_days,num_nodes,num_nodes))
    for node in range(num_nodes):
        for day in range(num_days):
            deaths_not_attended = max(0, demand_day_node(movements, scenario_info, day,node) - scenario_info['node_capacities'][node])
            deaths_transport = scenario_info['prob_death_transport'] * movements_res[day, node].sum()
            total = total + deaths_not_attended + deaths_transport
    return total


def outgoing_list(movements):
    num_days = movements.shape[0]
    num_nodes = movements.shape[1]
    
    movements_res = np.reshape(movements,(num_days,num_nodes,num_nodes))
    outgoing_list = list()
    for day in range(num_days):
        for node in range(num_nodes):
            outgoing_list.append(calculate_outgoing(movements_res,day,node))
    return outgoing_list

def generate_bounds(scenario_info):
    outgoing_list = list()
    for day in range(scenario_info['num_days']):
        for outgoing_node in range(scenario_info['num_nodes']):
            for incoming_node in range(scenario_info['num_nodes']):
                outgoing_list.append((0,scenario_info['transport_capacities'][outgoing_node]))
    return outgoing_list

def f_cons(node_id, day, scenario_info):
    return lambda x: scenario_info['transport_capacities'][node_id] - calculate_outgoing(np.reshape(x,(scenario_info['num_days'],scenario_info['num_nodes'],scenario_info['num_nodes'])),day ,node_id)



