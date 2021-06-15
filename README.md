## GTFS2GMNS

The General Transit Feed Specification [(GTFS)](https://gtfs.org/) defines a common format for public transportation schedules and associated geographic information. It is used by thousands of public transport providers. As a data conversion tool, gtfs2gmns, can directly convert the GTFS data to node, link, and agent files in the [GMNS](https://github.com/zephyr-data-specs/GMNS) format. In addition, this tool can merge the transit network into the road network which is obtained from Open Street Map via [OSM2GMNS](https://github.com/jiawei92/OSM2GMNS).

The python code is developed based on the C++ version in NeXTA data hub, which is supported by the FHWA research project titled: "the Effective Integration of Analysis, Modeling, and Simulation Tools, AMS Data Hub Concept of operations". With external link to https://www.fhwa.dot.gov/publications/research/operations/13036/004.cfm and https://github.com/asu-trans-ai-lab/nexta.

## Installation

GTFS2GMNS has been published on [PyPI](https://pypi.org/project/gtfs2gmns/), and can be installed using:

```python
pip install gtfs2gmns
```

## Getting Started

### *Download GTFS Data*

On TransitFeed [homepage](https://transitfeeds.com/), users can browse and download official GTFS  feeds from around the world. Make sure that the following files are present, so that we can proceed.

* stop.txt
* route.txt
* trip.txt
* stop_times.txt
* agency.txt

### *Set the Directory*

GTFS2GMNS can handle the transit data from several agencies. Users need to configure different sub-files in the same directory.  There are two agencies in the Raleigh, GoRaleigh and NCSU Wolfline. So under the `Raleigh` folder, two subfolders `gtfs1` and `gtfs2` are set up, and each subfolder includes its own GTFS data.

### *Convert GTFS Data into GMNS Format*

```python
import gtfs2gmns as gg

path = 'Raleigh'
gmns_path = '.'
gg.converting(path,gmns_path)
```

The input parameter  `path` is the path of GTFS data, and the parameter  `gmns_path` is the path of output GMNS files.

The output files include node.csv, link.csv, trip.csv and route.csv.

## Main Steps

### *Read GTFS data*

**Step 1.1: Read routes.txt**

- route_id, route_long_name, route_short_name, route_url, route_type

**Step 1.2: Read stop.txt**

- stop_id, stop_lat, stop_lon, direction, location_type, position, stop_code, stop_name, zone_id

**Step 1.3: Read trips.txt**

- trip_id, route_id, service_id, block_id, direction_id, shape_id, trip_type
- and create the directed_route_id by combining route_id and direction_id

**Step 1.4: Read stop_times.txt**

- trip_id, stop_id, arrival_time, deaprture_time, stop_sequence

- create directed_route_stop_id by combining directed_route_id and stop_id through the trip_id

  > Note: the function needs to skip this record if trip_id is not defined, and link the virtual stop id with corresponding physical stop id.

- fetch the geometry of the direction_route_stop_id

- return the arrival_time for every stop

### *Building service network*

**Step 2.1 Create physical nodes**

- physical node is the original stop in standard GTFS

**Step 2.2 Create directed route stop vertexes**

- add route stop vertexes. the node_id of route stop nodes starts from 100001

  > Note: the route stop vertex the programing create nearby the corresponding physical node, to make some offset.

- add entrance link from physical node to route stop node
- add exit link from route stop node to physical node. As they both connect to the physical nodes, the in-station transfer process can be also implemented

**Step 2.3 Create physical arcs**

- add physical links between each physical node pair of each trip

**Step 2.4 Create service arcs**

- add service links between each route stop pair of each trip

## Visualization

You can visualize generated networks using [NeXTA](https://github.com/xzhou99/NeXTA-GMNS) or [QGIS](https://qgis.org/).

## Upcoming Features

- [ ] Output service and trace files.
- [ ] Set the time period and add vdf_fftt and vdf_freq fields in link files.
