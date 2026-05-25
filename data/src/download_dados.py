import osmnx as ox

# Zona de estudo: Guimarães
place = "Guimarães, Portugal"

# Rede pedonal real
G = ox.graph_from_place(place, network_type="walk")

# Projetar para metros
G = ox.project_graph(G)

# Guardar grafo
ox.save_graphml(G, "data/raw/osm/guimaraes_walk.graphml")

# Guardar também nós e arestas em GeoJSON
nodes, edges = ox.graph_to_gdfs(G)

nodes.to_file("data/raw/osm/nodes_guimaraes.geojson", driver="GeoJSON")
edges.to_file("data/raw/osm/edges_guimaraes.geojson", driver="GeoJSON")

print("Dados OSM guardados com sucesso.")

import geopandas as gpd

edges = gpd.read_file("data/raw/osm/edges_guimaraes.geojson")

print(edges.columns)
print(edges[["highway", "surface", "sidewalk", "wheelchair", "lit"]].head())