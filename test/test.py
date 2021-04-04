import os
import osm2gmns as og
import gtfs2gmns as gg

# city = 'Raleigh'
osm_path = 'osm/consolidated/'
gtfs_path = 'gtfs/'
gmns_path = '.'


node_transit,link_transit = gg.Convert_GTFS(gtfs_path,gmns_path)
bbox = gg.Create_Boundary(node_transit)

net = og.getNetFromOSMFile('osm/map.osm',network_type=('auto'), default_lanes=True, default_speed=True)
og.outputNetToCSV(net, output_folder='osm/')
net = og.getNetFromCSV(osm_path)
og.consolidateComplexIntersections(net)
og.outputNetToCSV(net, output_folder=osm_path)

node,link_osm_connector = gg.CreatConnector_osm_gtfs(osm_path,gmns_path)
link = gg.Create_TransitRoute(gmns_path)