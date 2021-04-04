import os
import ctypes
import numpy as np
import pandas as pd
from sys import platform

# some functions --> credit to path4gmns   
def _optimal_label_correcting_CAPI(node_size,
                        from_node_no_array,
                        to_node_no_array,
                        first_link_from,
                        last_link_from,
                        sorted_link_no_array, 
                        link_cost_array,
                        node_label_cost,
                        node_predecessor,
                        link_predecessor,
                        queue_next, from_node_id,
                        internal_node_seq_no_dict, _cdll):
    """ input : origin_node,destination_node,departure_time
        output : the shortest path
    """
    origin_node_no = internal_node_seq_no_dict[from_node_id]

    _cdll.shortest_path(origin_node_no,
                        node_size,
                        from_node_no_array,
                        to_node_no_array,
                        first_link_from,
                        last_link_from,
                        sorted_link_no_array, 
                        link_cost_array,
                        node_label_cost,
                        node_predecessor,
                        link_predecessor,
                        queue_next)


def output_path_sequence(internal_node_seq_no_dict, node_predecessor, external_node_id_dict, link_predecessor, from_node_id, to_node_id):
    """ output shortest path in terms of node sequence or link sequence
    
    Note that this function returns GENERATOR rather than list.
    """
    path = []
    current_node_seq_no = internal_node_seq_no_dict[to_node_id]

    while current_node_seq_no >= 0:  
        path.append(current_node_seq_no)
        current_node_seq_no = node_predecessor[current_node_seq_no]
        # reverse the sequence
    for node_seq_no in reversed(path):
        yield external_node_id_dict[node_seq_no]


def find_shortest_path(node_size,
                       from_node_no_array,
                       to_node_no_array,
                       first_link_from,
                       last_link_from,
                       sorted_link_no_array, 
                       link_cost_array,
                       node_label_cost,
                       node_predecessor,
                       link_predecessor,
                       queue_next, internal_node_seq_no_dict, from_node_id, to_node_id, external_node_id_dict, _cdll):
    if from_node_id not in internal_node_seq_no_dict.keys():
        raise Exception(f"Node ID: {from_node_id} not in the network")
    if to_node_id not in internal_node_seq_no_dict.keys():
        raise Exception(f"Node ID: {to_node_id} not in the network")

    _optimal_label_correcting_CAPI(node_size,
                                   from_node_no_array,
                                   to_node_no_array,
                                   first_link_from,
                                   last_link_from,
                                   sorted_link_no_array, 
                                   link_cost_array,
                                   node_label_cost,
                                   node_predecessor,
                                   link_predecessor,
                                   queue_next, from_node_id, internal_node_seq_no_dict, _cdll)

    return list(output_path_sequence(internal_node_seq_no_dict, node_predecessor, external_node_id_dict, link_predecessor, from_node_id, to_node_id))



def shortest_path(node_size, link_size, from_node_no_array, to_node_no_array, from_node_id, to_node_id,
                  link_road, internal_node_seq_no_dict, external_node_id_dict, _cdll):
    
    ### allocate
    node_predecessor = np.full(node_size, -1, np.int32)
    link_predecessor = np.full(node_size, -1, np.int32)

    # initialize others as numpy arrays directly
    queue_next = np.full(node_size, 0, np.int32)
    first_link_from = np.full(node_size, -1, np.int32)
    last_link_from = np.full(node_size, -1, np.int32)
    sorted_link_no_array = np.full(link_size, -1,np.int32)
    
    
    # count the size of outgoing links for each node
    outgoing_link_list = [0] * node_size
    for link in range(link_size):
        outgoing_link_list[from_node_no_array[link]] += 1
    
    cumulative_count = 0
    for i in range(node_size):
        first_link_from[i] = cumulative_count
        last_link_from[i] = (
            first_link_from[i] + outgoing_link_list[i]
        )
        cumulative_count += outgoing_link_list[i]
    
    # reset the counter # need to construct sorted_link_no_vector
    # we are converting a 2 dimensional dynamic array to a fixed size 
    # one-dimisonal array, with the link size 
    for i in range(node_size):
        outgoing_link_list[i] = 0
    
    # count again the current size of outgoing links for each node
    for j in range(link_size):
        # fetch the curent from node seq no of this link
        from_node_seq_no = from_node_no_array[j]
        # j is the link sequence no in the original link block
        k = (first_link_from[from_node_seq_no] 
             + outgoing_link_list[from_node_seq_no])
        sorted_link_no_array[k] = j
        # continue to count, increase by 1
        outgoing_link_list[from_node_no_array[j]] += 1
       
    MAX_LABEL_COST = 10000
    link_cost = link_road['length'].tolist()
    link_cost_array = np.array(link_cost, np.float64)
    node_label_cost = np.full(node_size, MAX_LABEL_COST,np.float64)
    
    shortest_path_node_sequence_result = find_shortest_path(node_size,
                                                            from_node_no_array,
                                                            to_node_no_array,
                                                            first_link_from,
                                                            last_link_from,
                                                            sorted_link_no_array, 
                                                            link_cost_array,
                                                            node_label_cost,
                                                            node_predecessor,
                                                            link_predecessor,
                                                            queue_next, internal_node_seq_no_dict, from_node_id, to_node_id,
                                                            external_node_id_dict, _cdll)
    
    return  shortest_path_node_sequence_result
    

def Create_TransitRoute(gmns_path):
    
    print('creating transit routes...')
    # print('reading gmns data...')
    link_transit = pd.read_csv(gmns_path + os.sep +'/link_transit.csv')
    
    node_combine = pd.read_csv(gmns_path + os.sep +'/node.csv', encoding='gbk')
    link_road = pd.read_csv(gmns_path + os.sep +'/link_osm_connector.csv',low_memory=False) 
    
    
    # print('building node id and node index dict...')
    node_size = len(node_combine) # transit node and osm node
    link_size = len(link_road) # osm link and connector link
    
    # node_list = node_combine['node_id']
    # link_list = link_road['link_id'].tolist()
    internal_node_seq_no_dict = {} # node id --> node index
    external_node_id_dict = {} # node index --> node id
    
    node_combine['node_id'] = node_combine.copy()['node_id'].astype(float)
    external_node_id = node_combine.copy()['node_id']
    node_seq_no = 0
    for i in range(node_size):
        internal_node_seq_no_dict[external_node_id[i]] = node_seq_no
        external_node_id_dict[node_seq_no] = external_node_id[i]
        node_seq_no += 1
    
    # prepare
    from_node_no_array = []
    to_node_no_array = []
    
    for i in range(len(link_road['from_node_id'])):
        a = internal_node_seq_no_dict[link_road.copy()['from_node_id'].iloc[i]]
        from_node_no_array.append(a)
    
    for i in range(len(link_road['to_node_id'])):
        a = internal_node_seq_no_dict[link_road.copy()['to_node_id'].iloc[i]]
        to_node_no_array.append(a)
    
    from_node_no_array = np.array(from_node_no_array, np.int32)
    to_node_no_array = np.array(to_node_no_array, np.int32)
    
    
    
    # print('shortest path cdll initializing...')
    
    # get cdll
    _pkg_path = os.path.abspath(__file__)
    
    if platform.startswith('win32'):
        _dll_file = os.path.join(os.path.dirname(_pkg_path), './bin/path_engine.dll')
    elif platform.startswith('linux'):
        _dll_file = os.path.join(os.path.dirname(_pkg_path), './bin/path_engine.so')
    elif platform.startswith('darwin'):
        _dll_file = os.path.join(os.path.dirname(_pkg_path), './bin/path_engine.dylib')
    else:
        raise Exception('Please build the shared library compatible to your OS\
                        using source files in engine_cpp!')
    
    _cdll = ctypes.cdll.LoadLibrary(_dll_file)
    
    # set up the argument types for the shortest path function in dll.
    _cdll.shortest_path.argtypes = [
        ctypes.c_int, 
        ctypes.c_int, 
        np.ctypeslib.ndpointer(dtype=np.int32),
        np.ctypeslib.ndpointer(dtype=np.int32),
        np.ctypeslib.ndpointer(dtype=np.int32),
        np.ctypeslib.ndpointer(dtype=np.int32),
        np.ctypeslib.ndpointer(dtype=np.int32), 
        np.ctypeslib.ndpointer(dtype=np.float64),   
        np.ctypeslib.ndpointer(dtype=np.float64),                                    
        np.ctypeslib.ndpointer(dtype=np.int32),
        np.ctypeslib.ndpointer(dtype=np.int32),
        np.ctypeslib.ndpointer(dtype=np.int32),
    ]
    
    
    # a_temp = shortest_path(node_size, link_size, from_node_no_array, to_node_no_array, from_node_id, to_node_id)
    from_node_temp = np.array(link_road['from_node_id'])
    to_node_temp = np.array(link_road['to_node_id'])
    
    length_temp = np.array(link_road['length'])
    
    node_dict_x = dict(zip(node_combine['node_id'],node_combine['x_coord']))
    node_dict_y = dict(zip(node_combine['node_id'],node_combine['y_coord']))
    
    # print('finding shortest path for each transit route...')
    with open('log.txt', 'w') as f:
        f.write('Cannot find shortest path [from_node_id,to_node_id]...'+ '\n')
            
    
    for i in range(len(link_transit['link_id'])):
        from_node_id = link_transit.copy()['from_node_id'].iloc[i]
        to_node_id = link_transit.copy()['to_node_id'].iloc[i]
        
        active_shortest_node_sequence = []
        active_length_list =[]
        
        active_shortest_node_sequence = shortest_path(node_size, link_size, from_node_no_array, to_node_no_array, from_node_id, to_node_id,
                                                      link_road, internal_node_seq_no_dict, external_node_id_dict, _cdll)
        if len(active_shortest_node_sequence) == 1:
           
            with open('log.txt', 'a') as f:
                temp = [str(from_node_id),str(to_node_id)]
                f.write(','.join(temp) + '\n')
            # print('Cannot find shortest path...',from_node_id,'-->',to_node_id)
            continue
        
        
        for j in range(len(active_shortest_node_sequence)-1):
            active_from_node_id = active_shortest_node_sequence[j]
            active_to_node_id = active_shortest_node_sequence[j+1]
            temp1 = np.array(from_node_temp == active_from_node_id)
            temp2 = np.array(to_node_temp == active_to_node_id)
            temp = temp1 & temp2
            if not any(temp):
                # print('Cannot find length...', active_from_node_id, '-->', active_to_node_id)
                break
            
            active_length = length_temp[temp]
            active_length = active_length[0]
            active_length_list.append(active_length)
            
        link_transit['length'].iloc[i] = sum(active_length_list)
        
        geometry = ''
        for j in range(len(active_shortest_node_sequence)):
            if (j == len(active_shortest_node_sequence)-1):
                geometry = geometry + str(node_dict_x[active_shortest_node_sequence[j]]) + ' ' + str(node_dict_y[active_shortest_node_sequence[j]])
            else:
                geometry = geometry + str(node_dict_x[active_shortest_node_sequence[j]]) + ' ' + str(node_dict_y[active_shortest_node_sequence[j]]) + ', '
            
        geometry = 'LINESTRING (' + geometry+ ')'
        link_transit['geometry'].iloc[i] = geometry
    
    link_transit.to_csv(gmns_path + os.sep +'/link_transit.csv', index=False)
    
    combined_link = pd.concat([link_road,link_transit], axis=0, ignore_index=True)
    combined_link.to_csv(gmns_path + os.sep +'/link.csv', index=False)
    return combined_link
