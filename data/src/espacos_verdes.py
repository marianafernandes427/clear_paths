# baixar os dados ainda!!!


import geopandas as gpd

edges = gpd.read_file("data/raw/osm/edges_guimaraes.geojson")
verdes = gpd.read_file("data/raw/websig/espacos_verdes.geojson")

edges = edges.to_crs(3763)
verdes = verdes.to_crs(3763)

# distância ao espaço verde mais próximo
edges["dist_espaco_verde"] = edges.geometry.apply(
    lambda geom: verdes.distance(geom).min()
)

edges.to_file("data/processed/edges_com_verdes.geojson", driver="GeoJSON")


# heuristica
def custo_sombra(dist_espaco_verde):
    if dist_espaco_verde <= 30:
        return 0
    elif dist_espaco_verde <= 100:
        return 10
    else:
        return 25