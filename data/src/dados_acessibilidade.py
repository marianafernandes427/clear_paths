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