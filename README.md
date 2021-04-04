## GTFS2GMNS

The General Transit Feed Specification [(GTFS)](https://gtfs.org/) defines a common format for public transportation schedules and associated geographic information. It is used by thousands of public transport providers. As a data conversion tool, gtfs2gmns, can directly convert the GTFS data to node, link, and agent files in the [GMNS](https://github.com/zephyr-data-specs/GMNS) format. In addition, this tool can merge the transit network into the road network which is obtain by Open Street Map via [OSM2GMNS](https://github.com/jiawei92/OSM2GMNS).

## Installation

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

### Download OSM Data

On OpenStreetMap [homepage](https://www.openstreetmap.org/), click the `Export` button to enter Export mode. Before downloading, you may need to span and zoom in/out the map to make sure that your target area should cover the transit network area.

### *Convert GTFS Data into GMNS Format*

```python
import gtfs2gmns as gg

node_transit,link_transit = gg.Convert_GTFS(gtfs_path,gmns_path)
```

Please modify the directory.

If you need the bounding box of the transit network,  **Create_Boundary** function might help.

```python
import gtfs2gmns as gg

node_transit,link_transit = gg.Convert_GTFS(gtfs_path,gmns_path)
bbox = gg.Create_Boundary(node_transit)
```

### *Get the OSM Network*

Before merging the transit network into the road network, you need to download the osm data and convert it into the GMNS format first. [OSM2GMNS](https://github.com/jiawei92/OSM2GMNS) python package will be a good choice.

```python
import os
import osm2gmns as og

net = og.getNetFromOSMFile('osm/map.osm',network_type=('auto'), default_lanes=True, default_speed=True)
og.outputNetToCSV(net, output_folder='osm/')

net = og.getNetFromCSV(osm_path)
og.consolidateComplexIntersections(net)
og.outputNetToCSV(net, output_folder=osm_path)
```

### *Create the Connector*

You can merge the networks by building the connector between the transit node and the nearby OSM node.

Make sure you already obtain node_transit.csv and the osm files (node.csv and link.csv).

```python
import gtfs2gmns as gg

node,link_osm_connector = gg.CreatConnector_osm_gtfs(osm_path,gmns_path)
```

### *Create the Transit Route*

This procedure can help you generate the actual trace for the transit route.

```python
import gtfs2gmns as gg

link = gg.Create_TransitRoute(gmns_path)
```

## Visualization

You can visualize generated networks using [NeXTA](https://github.com/xzhou99/NeXTA-GMNS) or [QGIS](https://qgis.org/).

## Module

**gtfs2gmns.py**

Convert GTFS Data into GMNS Format, including node and link files.

**create_connector.py**

Need to Download the OSM data first and convert it into GMNS format based on [osm2gmns](https://osm2gmns.readthedocs.io/en/latest/).

Build the connector between the transit node and the road node.

**trace2route.py** 

Create the actual transit route through the shortest path [algorithm](https://github.com/jdlph/PATH4GMNS).

**create_agent.py**

Create the agent file for transit schedule into GMNS format.

## Sample Networks

Phoenix Transit Network
![image](https://github.com/xtHuang0927/GTFS2GMNS/blob/main/dataset/pic/Phoenix.PNG)

Philadelphia Transit Network
![image](https://github.com/xtHuang0927/GTFS2GMNS/blob/main/dataset/pic/Philadelphia.PNG)

Pittsburgh Transit Network
![image](https://github.com/xtHuang0927/GTFS2GMNS/blob/main/dataset/pic/Pittsburgh%20.PNG)

Raleigh Transit Network
![image](https://github.com/xtHuang0927/GTFS2GMNS/blob/main/dataset/pic/Raleigh.PNG)
