# baixar os dados ainda!!!

from pathlib import Path
import geopandas as gpd

BASE_PATH = Path(__file__).resolve().parents[1]
edges_file = BASE_PATH / "raw" / "osm" / "edges_guimaraes.geojson"
verdes_file = BASE_PATH / "raw" / "websig" / "espacos_verdes.geojson"

if not verdes_file.exists():
    raise FileNotFoundError(
        f"Ficheiro não encontrado: {verdes_file}\n" \
        "Por favor coloque o arquivo espacos_verdes.geojson em data/raw/websig/ "
    )

edges = gpd.read_file(edges_file)
verdes = gpd.read_file(verdes_file)

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