import osmnx as ox

G = ox.graph_from_place("Guimarães, Portugal", network_type="walk")
G = ox.project_graph(G)
ox.save_graphml(G, "data/01_raw/osm/guimaraes_walk.graphml")