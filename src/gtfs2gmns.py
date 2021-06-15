# -*- coding: utf-8 -*-
import os
import math
import numpy as np
import pandas as pd

def split_ignore_separators_in_quoted(s, separator=',', quote_mark='"'):
    result = []
    quoted = False
    current = ''
    for i in range(len(s)):
        if quoted:
            current += s[i]
            if s[i] == quote_mark:
                quoted = False
            continue
        if s[i] == separator:
            result.append(current.strip())
            current = ''
        else:
            current += s[i]
            if s[i] == quote_mark:
                quoted = True
    result.append(current)
    return result
 
def readtxt(filename):
    Filepath = filename +'.txt'
    data = []
    with open(Filepath, 'r', encoding='utf-8-sig') as f:
        lines = f.readlines()
        first_line = lines[0].split('\n')[0].split(',')
        for line in lines:
            if len(line.split('\n')[0].split(',')) == len(first_line):
                data.append(line.split('\n')[0].split(','))
            else:
                data.append(split_ignore_separators_in_quoted(line))
    df_data = pd.DataFrame(data[1:], columns=data[0])
    return df_data

def LLs2Dist(lon1, lat1, lon2, lat2): #WGS84 transfer coordinate system to distance(meter) #xy
    R = 6371
    dLat = (lat2 - lat1) * math.pi / 180.0
    dLon = (lon2 - lon1) * math.pi / 180.0

    a = math.sin(dLat / 2) * math.sin(dLat/2) + math.cos(lat1 * math.pi / 180.0) * math.cos(lat2 * math.pi / 180.0) * math.sin(dLon/2) * math.sin(dLon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distance = R * c * 1000
    return distance

def time_convert(in_str): 
    hour = int(in_str[:-6])
    return str(hour % 24)+in_str[-6:]

def convert_gmns(gtfs_path,gmns_path,NUM,node_num):
    '''1. READ FILES'''
    #1.1 Initialized
    m_PT_StopMap = readtxt(gtfs_path + os.sep + 'stops')
    m_PT_RouteMap = readtxt(gtfs_path + os.sep + 'routes')
    m_PT_TripMap = readtxt(gtfs_path + os.sep + 'trips')
    TransitStopTime = readtxt(gtfs_path + os.sep + 'stop_times')
    m_PT_Agency = readtxt(gtfs_path + os.sep + 'agency')
    
    agency_name = m_PT_Agency['agency_name'][0]
    if '"' in agency_name:
        agency_name = eval(agency_name)
    #1.2 Processing data stored as dataframe
    m_PT_TripMap_directed_route_id = m_PT_TripMap['route_id'].astype(str).str.cat(m_PT_TripMap['direction_id'].astype(str), sep='.')
    m_PT_TripMap['directed_route_id'] = m_PT_TripMap_directed_route_id
    
    m_PT_DirectedRouteStopMap = pd.merge(m_PT_TripMap,TransitStopTime,on='trip_id')
    m_PT_DirectedRouteStopMap_directed_route_stop_id = m_PT_DirectedRouteStopMap['directed_route_id'].astype(str).str.cat(m_PT_DirectedRouteStopMap['stop_id'].astype(str), sep='.')
    m_PT_DirectedRouteStopMap['directed_route_stop_id'] = m_PT_DirectedRouteStopMap_directed_route_stop_id
    
    
    '''2. NODE'''
    #2.1 physical node
    node_csv = pd.DataFrame()
    
    ##2.1.1 Extract the coordinates of the site corresponding to the stop_id information appearing in the stop time
    df_m_PT_Direct = m_PT_DirectedRouteStopMap[['stop_id','directed_route_stop_id','directed_route_id']]
    df_m_PT_StopMap = m_PT_StopMap[['stop_id','stop_lat','stop_lon','zone_id']]
    df_merge_StopMap = pd.merge(df_m_PT_Direct,df_m_PT_StopMap, on='stop_id').drop_duplicates(subset=['stop_id'])
     
    ##2.1.2 Constructing physical node
    node_csv['name'] = df_merge_StopMap['stop_id']
    node_csv['x_coord'] = df_merge_StopMap['stop_lon']
    node_csv['y_coord'] = df_merge_StopMap['stop_lat']
    node_csv['node_type'] = 'stop'
    node_csv['directed_route_id'] = None
    node_csv['ctrl_type'] = None
    node_csv['zone_id'] = 0
    node_csv['production'] = 0.00
    node_csv['attraction'] = 0.00
    node_csv['agency_name'] = agency_name
    node_csv['geometry'] = 'POINT (' + df_merge_StopMap['stop_lon'] + ' ' + df_merge_StopMap['stop_lat'] +')'
    
    ##2.1.3 Sorting and modifying indexes
    node_csv = node_csv.sort_values(by=['name'])
    node_csv.index = pd.RangeIndex(len(node_csv.index))
    node_csv.index.name = 'node_id'
    node_csv.index += node_num
    #2.2 route stop node
    route_stop_csv = pd.DataFrame()
    
    ##2.2.1 Remove duplicate directed_route_stop_id
    df_merge_StopMap = pd.merge(df_m_PT_Direct,df_m_PT_StopMap, on='stop_id').drop_duplicates(subset=['directed_route_stop_id'])
    
    ##2.2.2 modifying route stop node
    route_stop_csv['name'] = df_merge_StopMap['directed_route_stop_id']
    route_stop_csv['x_coord'] = df_merge_StopMap['stop_lon'].astype(float)-0.000100
    route_stop_csv['y_coord'] = df_merge_StopMap['stop_lat'].astype(float)-0.000100
    route_stop_csv['node_type'] = 'directed_route_stop'
    route_stop_csv['directed_route_id'] = df_merge_StopMap['directed_route_id'].astype(str) # csv会吞掉0
    route_stop_csv['ctrl_type'] = None
    route_stop_csv['zone_id'] = 0
    route_stop_csv['production'] = 0.00
    route_stop_csv['attraction'] = 0.00
    route_stop_csv['agency_name'] = agency_name
    route_stop_csv['geometry'] = 'POINT (' + df_merge_StopMap['stop_lon'] + ' ' + df_merge_StopMap['stop_lat'] +')'
    
    ##2.2.3 Sorting and modifying indexes
    route_stop_csv = route_stop_csv.sort_values(by=['name'])
    route_stop_csv.index = pd.RangeIndex(len(route_stop_csv.index))
    route_stop_csv.index.name = 'node_id'
    route_stop_csv.index += int('{}00001'.format(NUM)) # 多个agency的序号体现在首位
    

    '''3. LINK NO VDF'''
    #3.1 virtual link: physical node & route stop node
    df_merge_StopMap_NodeMap = pd.merge(df_merge_StopMap,node_csv.copy().reset_index()[['node_id','name']],left_on='stop_id',right_on='name',how='left').rename(columns={'node_id':'physical_node_id','name':'physical_name'})
    df_merge_StopMap_NodeMap = pd.merge(df_merge_StopMap_NodeMap.copy(),route_stop_csv.copy().reset_index()[['node_id','name','x_coord','y_coord']],left_on='directed_route_stop_id',right_on='name',how='left').rename(columns={'node_id':'route_stop_node_id','name':'route_stop_name'})
    
    tranfer_link_list = []
    df_merge_StopMap_NodeMap = df_merge_StopMap_NodeMap.sort_values(by=['directed_route_stop_id'])
    for index, row in df_merge_StopMap_NodeMap.iterrows():
        active_agency = agency_name
        ative_directed_route_id = row.directed_route_id
        active_route_stop_name = row.directed_route_stop_id
        active_route_stop_node_id = row.route_stop_node_id
        active_physical_node_id = row.physical_node_id
        active_distance = LLs2Dist(float(row.stop_lon),float(row.stop_lat),float(row.x_coord),float(row.y_coord))
        active_geometry_entrance = 'LINESTRING (' + str(row.stop_lon)+' '+str(row.stop_lat)+', '+str(row.x_coord)+' '+str(row.y_coord)+')'
        active_geometry_exit = 'LINESTRING (' + str(row.x_coord)+' '+str(row.y_coord)+', '+str(row.stop_lon)+' '+str(row.stop_lat)+')'       
        tranfer_link_list.append([active_route_stop_name+'.entrance',
                                  active_physical_node_id,active_route_stop_node_id,ative_directed_route_id,active_agency,
                                  active_distance,active_geometry_entrance])
        tranfer_link_list.append([active_route_stop_name+'.exit',
                                  active_route_stop_node_id,active_physical_node_id,ative_directed_route_id,active_agency,
                                  active_distance,active_geometry_exit])
    transfer_link_csv = pd.DataFrame(tranfer_link_list, columns=['name','from_node_id','to_node_id','directed_route_id','agency_name','length','geometry'])
    
    #3.2 service link: route stop node & route stop node
    df_PT_DirectedRouteStopMap = m_PT_DirectedRouteStopMap[['stop_id','directed_route_stop_id','route_id','trip_id','arrival_time','departure_time','stop_sequence']].copy()
    
    
    df_PT_DirectedRouteStopMap['arrival_time'] = df_PT_DirectedRouteStopMap['arrival_time'].apply(lambda x: np.NaN if x == '' else x)
    df_PT_DirectedRouteStopMap['arrival_time'] = df_PT_DirectedRouteStopMap['arrival_time'].dropna()
    df_PT_DirectedRouteStopMap['departure_time'] = df_PT_DirectedRouteStopMap['departure_time'].apply(lambda x: np.NaN if x == '' else x)
    df_PT_DirectedRouteStopMap['departure_time'] = df_PT_DirectedRouteStopMap['departure_time'].dropna()
    
    #####
    conv_arr_time_series = df_PT_DirectedRouteStopMap['arrival_time'].dropna().apply(lambda x: time_convert(str(x)))
    conv_dep_time_series = df_PT_DirectedRouteStopMap['departure_time'].dropna().apply(lambda x: time_convert(str(x)))
    df_PT_DirectedRouteStopMap['arrival_time_min'] = pd.to_datetime(pd.Series(conv_arr_time_series)).apply(lambda x: x.hour*60 + x.minute)
    df_PT_DirectedRouteStopMap['departure_time_min'] = pd.to_datetime(pd.Series(conv_dep_time_series)).apply(lambda x: x.hour*60 + x.minute)
    
    df_PT_DirectedRouteStopMap_service = pd.merge(df_PT_DirectedRouteStopMap.copy(),route_stop_csv.copy().reset_index()[['node_id','name']],left_on='directed_route_stop_id',right_on='name',how='left')
    gp = df_PT_DirectedRouteStopMap_service.groupby('trip_id')
    dataList_trip = {}
    def convert_time_sequence(time_sequence): #change format: 13:22:00 --> 1322:00
        time = []
        for i in np.unique(time_sequence):
            i=i.replace(':', '', 1)
            time.append(i)
        return time
    for key, form in gp: # trip 14482330      
        temp = form['arrival_time'].dropna()
        temp = convert_time_sequence(temp)
        dataList_trip[key] = {
            'route_id': form['route_id'].iloc[0],
            'route_stop_id_sequence': form['directed_route_stop_id'].tolist(),
            'arrival_time_min_sequence':form['arrival_time_min'].tolist(),
            'node_id_sequence':form['node_id'].tolist(),
            'time_sequence':temp
            } 
    
    route_stop_id_name_series = pd.Series(route_stop_csv['name'].index.tolist(), index=route_stop_csv['name'].values.tolist())
    route_stop_x_series = route_stop_csv['x_coord']
    route_stop_y_series = route_stop_csv['y_coord']
    
    service_link_list = []
    for key in dataList_trip.keys():
        # key = '14485720'
        active_node_sequence_size = len(dataList_trip[key]['route_stop_id_sequence'])
        for i in range(active_node_sequence_size-1):
            active_agency = agency_name
            active_from_route_stop_id = dataList_trip[key]['route_stop_id_sequence'][i] # 3.0.897
            active_to_route_stop_id = dataList_trip[key]['route_stop_id_sequence'][i+1]
            active_name = active_from_route_stop_id+'->'+active_to_route_stop_id
            active_from_route_stop_index = route_stop_id_name_series[active_from_route_stop_id]
            ative_directed_route_id = active_from_route_stop_id[:active_from_route_stop_id.rfind('.')]
            active_from_route_stop_id_x = route_stop_x_series[active_from_route_stop_index]
            active_from_route_stop_id_y = route_stop_y_series[active_from_route_stop_index]
            active_to_route_stop_index = route_stop_id_name_series[active_to_route_stop_id]
            active_to_route_stop_id_x = route_stop_x_series[active_to_route_stop_index]
            active_to_route_stop_id_y = route_stop_y_series[active_to_route_stop_index]
            
            active_distance = LLs2Dist(active_from_route_stop_id_x,active_from_route_stop_id_y,active_to_route_stop_id_x,active_to_route_stop_id_y)
            active_geometry = 'LINESTRING (' + str(active_from_route_stop_id_x)+' '+str(active_from_route_stop_id_y)+','+str(active_to_route_stop_id_x)+' '+str(active_to_route_stop_id_y)+')'
    
            service_link_list.append([active_name,active_from_route_stop_index,active_to_route_stop_index,
                                      ative_directed_route_id,active_agency,
                                      active_distance,active_geometry])
    
    service_link_csv = pd.DataFrame(service_link_list, columns=['name','from_node_id','to_node_id','directed_route_id','agency_name','length','geometry']).drop_duplicates(subset=['name'])    
    
    #3.3 physical link
    df_PT_DirectedRouteStopMap_physical = pd.merge(df_PT_DirectedRouteStopMap.copy(),node_csv.copy().reset_index()[['node_id','name']],left_on='stop_id',right_on='name',how='left')
    gp = df_PT_DirectedRouteStopMap_physical.groupby('trip_id')
    
    dataList_phy = {}
    for key, form in gp:
        dataList_phy[key] = {
            'route_stop_id_sequence': form['directed_route_stop_id'].tolist(),
            'name_sequence':form['name'].tolist(),
            'node_id_sequence':form['node_id'].tolist()
            } 
    
    node_x = node_csv['x_coord']
    node_y = node_csv['y_coord']
    physical_link_list = []
    for key in dataList_phy.keys():
        active_node_sequence_size = len(dataList_trip[key]['node_id_sequence'])
                
        for i in range(active_node_sequence_size-1):
    
            active_from_node_id = dataList_phy[key]['node_id_sequence'][i] # 7231 node_id
            active_to_node_id = dataList_phy[key]['node_id_sequence'][i+1]
            
            active_from_node_name = dataList_phy[key]['name_sequence'][i]
            active_to_node_name = dataList_phy[key]['name_sequence'][i+1]
            active_name = active_from_node_name+'->'+active_to_node_name
            
            from_node_id_x = node_x[active_from_node_id]
            from_node_id_y = node_y[active_from_node_id]
            to_node_id_x = node_x[active_to_node_id]
            to_node_id_y = node_y[active_to_node_id]
            
            active_route_id = dataList_phy[key]['route_stop_id_sequence'][i+1][:dataList_phy[key]['route_stop_id_sequence'][i+1].rfind('.')]
            active_agency = agency_name
            active_distance = LLs2Dist(float(from_node_id_x),float(from_node_id_y),float(to_node_id_x),float(to_node_id_y))
            active_geometry = 'LINESTRING (' + str(from_node_id_x)+' '+str(from_node_id_y)+', '+str(to_node_id_x)+' '+str(to_node_id_y)+')'
    
            physical_link_list.append([active_name,active_from_node_id,active_to_node_id,active_route_id,active_agency,active_distance,active_geometry])
    physical_link_csv = pd.DataFrame(physical_link_list, columns=['name','from_node_id','to_node_id','directed_route_id','agency_name','length','geometry']).drop_duplicates(subset=['name'])
    
    #3.3 merge link
    Link_df = pd.concat([physical_link_csv,transfer_link_csv,service_link_csv])
    
    
    '''4. TRIP'''
    route_name_series = pd.Series(m_PT_RouteMap['route_long_name'].tolist(), index=m_PT_RouteMap['route_id'].tolist())
    directed_route_id_series = pd.Series(m_PT_TripMap['directed_route_id'].tolist(), index=m_PT_TripMap['trip_id'].tolist())
    
    trip_csv = pd.DataFrame()
    length_temp = np.array(service_link_csv['length'])
    from_node_temp = np.array(service_link_csv['from_node_id'])
    to_node_temp = np.array(service_link_csv['to_node_id'])
    trip_csv_list = []
    for key in dataList_trip.keys():
        active_length_list = []
        active_node_sequence_size = len(dataList_trip[key]['route_stop_id_sequence'])
        flag = 1
        
        for i in range(active_node_sequence_size-1):
            active_from_node_id = dataList_trip[key]['node_id_sequence'][i]
            active_to_node_id = dataList_trip[key]['node_id_sequence'][i+1]
            temp1 = np.array(from_node_temp == active_from_node_id)
            temp2 = np.array(to_node_temp == active_to_node_id)
            temp = temp1 & temp2
            if not any(temp):
                flag = 0
                break
            
            active_length = length_temp[temp]
            active_length = active_length[0]
            active_length_list.append(active_length)
        
        if flag == 1:
            active_length = sum(active_length_list)    
            active_time_sequence = dataList_trip[key]['time_sequence']
            if '' in active_time_sequence:
                active_time_sequence.remove('')
            
            active_time_first_temp = dataList_trip[key]['arrival_time_min_sequence'][0]
            active_time_last_temp = dataList_trip[key]['arrival_time_min_sequence'][-1]
        
            active_time = active_time_last_temp - active_time_first_temp
            if active_time < 0:
                active_time = active_time+1440
        
            node_sequence_temp = ';'.join(list(map(str, dataList_trip[key]['node_id_sequence'])))+';'
            time_sequence_temp = ';'.join(active_time_sequence)+';'
            
            trip_csv_list.append([key,route_name_series[dataList_trip[key]['route_id']],
                                  directed_route_id_series[key],active_time,active_length,
                                  node_sequence_temp,time_sequence_temp])
    
    trip_csv = pd.DataFrame(trip_csv_list, columns=['trip_id','route_id_short_name','directed_route_id','travel_time','distance','node_sequence','time_sequence'])
    trip_csv.insert(0, 'agent_type', 'transit')
    trip_csv.insert(4, 'o_zone_id', '1')
    trip_csv.insert(5, 'd_zone_id', '2')
    trip_csv.insert(6, 'agency_name', agency_name)
    
    def trip_geometry(x): # input node list
        x = x.split(';')
    
        geometry = ''
        for i in x[:-1]:
            active_from_route_stop_id_x = route_stop_x_series[int(i)]
            active_from_route_stop_id_y = route_stop_y_series[int(i)]
            geometry += str(active_from_route_stop_id_x)+' '+str(active_from_route_stop_id_y)+','
        geometry = 'LINESTRING (' + geometry[:-1] + ')'
        return geometry
    
    trip_csv['geometry'] = trip_csv['node_sequence'].apply(lambda x: trip_geometry(x)) # Speed can be optimized

    
    '''5. ROUTE'''
    route_csv = trip_csv.drop(['trip_id'],axis=1)
    route_csv['directed_route_id'] = route_csv['directed_route_id'].copy().apply(lambda x: x.split('.')[0])
    route_csv = route_csv.drop_duplicates(subset=['directed_route_id'])

    return node_csv,route_stop_csv,Link_df,trip_csv,route_csv



def converting(path,gmns_path):
    # start_time = time.time()
    files= os.listdir(path) 
    s = []
    for file in files: #Traversing folders
        path_sub =  path + '/' + file
        if os.path.isdir(path_sub):
            s.append(path_sub)
            # files1 = os.listdir(path_sub)
    if len(s) == 0:
        s.append(path)

    Physical_Node_List = []
    Route_Stop_List = []
    Link_List = []
    Trip_List = []
    Route_List = []
    node_num = 1
    
    
    for i in range(len(s)):
        
        print('For Agency{}...'.format(i+1))     
        gtfs_path = s[i]
        
        node_csv,route_stop_csv,Link_df,trip_csv,route_csv = convert_gmns(gtfs_path,gmns_path,i+1,node_num)
        node_num = len(node_csv) + 1
        
        Physical_Node_List.append(node_csv)
        Route_Stop_List.append(route_stop_csv)
        Link_List.append(Link_df)
        Trip_List.append(trip_csv)
        Route_List.append(route_csv)
     
    Physical_Node = pd.concat(Physical_Node_List)
    Physical_Node.index = pd.RangeIndex(len(Physical_Node.index))
    Physical_Node.index.name = 'node_id'
    Physical_Node.index += 1
    
    Route_Stop = pd.concat(Route_Stop_List)
    NODE = pd.concat([Physical_Node,Route_Stop])
    NODE_order = ['name','x_coord','y_coord','node_type','directed_route_id','ctrl_type','zone_id','production','attraction','agency_name','geometry']
    NODE = NODE[NODE_order]
    NODE.to_csv(gmns_path + os.sep + 'node.csv')
    
    LINK = pd.concat(Link_List)
    LINK.index = pd.RangeIndex(len(LINK.index))
    LINK.index.name = 'link_id'
    LINK.index += 1
    LINK.to_csv(gmns_path + os.sep + 'link.csv')
    
    TRIP = pd.concat(Trip_List)
    TRIP.index = pd.RangeIndex(len(TRIP.index))
    TRIP.index.name = 'trip_id'
    TRIP.index += 1
    TRIP.to_csv(gmns_path + os.sep + 'trip.csv')

    ROUTE = pd.concat(Route_List)
    ROUTE.index = pd.RangeIndex(len(ROUTE.index))
    ROUTE.index.name = 'route_id'
    ROUTE.index += 1
    ROUTE.to_csv(gmns_path + os.sep + 'route.csv')
    # print('run time -->',time.time()-start_time)
