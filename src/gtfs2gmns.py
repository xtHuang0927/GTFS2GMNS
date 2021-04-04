'''Read Transit Files
required gtfs data : stop.txt, route.txt, trip.txt, stop_times.txt
'''
import os
import math
import datetime
import numpy as np
import pandas as pd
import geopandas as gpd


def create_folder(path):
    if not os.path.exists(path):
        os.makedirs(path)

# read files
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

# distance
def LLs2Dist(lon1, lat1, lon2, lat2): #WGS84 transfer coordinate system to distance(meter) #xy
    R = 6371
    dLat = (lat2 - lat1) * math.pi / 180.0
    dLon = (lon2 - lon1) * math.pi / 180.0

    a = math.sin(dLat / 2) * math.sin(dLat/2) + math.cos(lat1 * math.pi / 180.0) * math.cos(lat2 * math.pi / 180.0) * math.sin(dLon/2) * math.sin(dLon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    dist = R * c * 1000
    return dist

# time
def convert_time_sequence(time_sequence): #change format: 13:22:00 --> 1322:00
    time = []
    for i in np.unique(time_sequence):
        i=i.replace(':', '', 1)
        time.append(i)
    return time

def time_convert(input_time): #time format in GTFS is not standard, need convert: 25:00:00 --> 01:00:00
    hour = int(input_time[:-5])
    hour = hour%24
    output_time = str(hour)+input_time[-5:]
    return output_time

def time_calculate(time1,time2): #calculate the time delta
    time_a = datetime.datetime.strptime(time1, '%H%M:%S')
    time_b = datetime.datetime.strptime(time2, '%H%M:%S')
    flag = (time_b<time_a)
    active_time = (time_b-time_a).total_seconds()/60 + 1440*flag #min
    return active_time

def time(time1,time2): 
    time_a = time_convert(time1)
    time_b = time_convert(time2)
    delta = time_calculate(time_a,time_b)
    return delta


def Convert_GTFS(gtfs_path,gmns_path):
    create_folder(gmns_path)
    
    print('reading gtfs data...')
    
    df_stops = readtxt(gtfs_path + os.sep + 'stops')
    df_routes = readtxt(gtfs_path + os.sep + 'routes')
    df_trips = readtxt(gtfs_path + os.sep + 'trips')
    df_stoptimes = readtxt(gtfs_path + os.sep + 'stop_times')
    
    
    '''build node.csv'''
    print('converting gtfs data into gmns format...')
    # print('building node data...')
    node_csv = pd.DataFrame()
    
    node_csv['name'] = df_stops['stop_id']
    node_csv['x_coord'] = df_stops['stop_lon']
    node_csv['y_coord'] = df_stops['stop_lat']
    node_csv['node_type'] = 'transit'
    node_csv['ctrl_type'] = None
    node_csv['zone_id'] = None
    node_csv['geometry'] = "POINT (" + df_stops['stop_lon'] + " " + df_stops['stop_lat'] +")"
    node_csv.index.name = 'node_id'
    node_csv.index += 10000001 #index from 0
    
    # node_csv['node_id']=range(100001,100001+node_csv['name'].size,1)
    
    node_csv.to_csv(gmns_path + os.sep + '/node_transit.csv')
    # print(' node.csv done') 
    
    
    '''build link.csv'''
    # print('building link data...')
    node_csv = pd.read_csv(gmns_path + os.sep + '/node_transit.csv')
    node_csv = node_csv.rename(columns={'name':'stop_id'})
    
    combined_route = df_trips.merge(df_routes,on='route_id',how='left')
    node_csv['stop_id'] = node_csv['stop_id'].astype(str)
    df_stoptimes['stop_id'] = df_stoptimes['stop_id'].astype(str)
    combined_stop = df_stoptimes.merge(node_csv,on='stop_id',how='left' )
    combined_trip = combined_stop.merge(df_trips,on='trip_id',how='left')
    
    dataList_route = {}
    gp = combined_route.groupby('trip_id')
    for key, form in gp:
        dataList_route[key] = {
            'route_id': form['route_id'].values[0],
            'route_id_short_name': form['route_long_name'].values[0]
            }
    
    
    dataList_trip = {}
    gp = combined_trip.groupby('trip_id')
    
    for key, form in gp:
        temp = form['arrival_time']
        temp = convert_time_sequence(temp)
        dataList_trip[key] = {
            'route_id': form['route_id'].values[0],
            'from_node_id': form['node_id'].values[0],
            'to_node_id': form['node_id'].values[-1],
            'node_sequence': form['node_id'].tolist(),
            'time_sequence': temp
            }
    
    
    link_list = []
    link_csv = pd.DataFrame()
    
    node_x = node_csv['x_coord'].tolist()
    node_y = node_csv['y_coord'].tolist()
    node_id_list = node_csv['node_id'].tolist()
    
    for key in dataList_trip.keys(): 
        # print(key)    
        active_node_sequence_size = len(dataList_trip[key]['node_sequence'])
            
        for i in range(active_node_sequence_size-1):
            
            route_index = dataList_trip[key]['route_id']
            active_from_node_id = dataList_trip[key]['node_sequence'][i]
            active_to_node_id = dataList_trip[key]['node_sequence'][i+1]
            active_from_node_idx = node_id_list.index(active_from_node_id)
            active_to_node_idx = node_id_list.index(active_to_node_id)
            
            from_node_id_x = node_x[active_from_node_idx] ###
            from_node_id_y = node_y[active_from_node_idx]
            to_node_id_x = node_x[active_to_node_idx]
            to_node_id_y = node_y[active_to_node_idx]
            
            active_distance = LLs2Dist(from_node_id_x,from_node_id_y,to_node_id_x,to_node_id_y)
            active_geometry = 'LINESTRING (' + str(from_node_id_x)+' '+str(from_node_id_y)+', '+str(to_node_id_x)+' '+str(to_node_id_y)+')'
            
            link_list.append([route_index,active_from_node_id,active_to_node_id,active_distance,active_geometry])
    
    link_csv = pd.DataFrame(link_list, columns=['name','from_node_id','to_node_id','length','geometry']).drop_duplicates()    
    
    link_csv['link_type_name'] = 'transit'
    link_csv['link_type'] = 99
    link_csv['dir_flag'] = 1
    link_csv['lanes'] = 1
    link_csv['free_speed'] = 50
    link_csv['capacity'] = 100
      
        
    link_csv.index.name = 'link_id'
    link_csv.index += 10000001
    link_csv.to_csv(gmns_path + os.sep + '/link_transit.csv')   
    # print(' link.csv done') 
    return node_csv, link_csv

def Create_Boundary(node_csv):
    df = node_csv
    gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df['x_coord'], df['y_coord']))
    
    minx = gdf.bounds['minx'].min()
    miny = gdf.bounds['miny'].min()
    maxx = gdf.bounds['maxx'].max()
    maxy = gdf.bounds['maxy'].max()
    bbox = [minx,miny,maxx,maxy]
    return bbox