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

def custo_acessibilidade(row):
    custo = 0

    highway = str(row.get("highway", ""))
    surface = str(row.get("surface", ""))
    sidewalk = str(row.get("sidewalk", ""))
    wheelchair = str(row.get("wheelchair", ""))
    lit = str(row.get("lit", ""))

    if "steps" in highway:
        custo += 100

    if wheelchair == "no":
        custo += 100

    if surface in ["cobblestone", "gravel", "unpaved", "ground"]:
        custo += 30

    if sidewalk in ["no", "none"]:
        custo += 30

    if lit == "no":
        custo += 15

    return custo