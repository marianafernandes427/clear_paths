def custo_ruido(row):
    highway = str(row.get("highway", ""))

    if highway in ["primary", "secondary"]:
        return 50
    elif highway in ["tertiary"]:
        return 30
    elif highway in ["residential"]:
        return 15
    elif highway in ["pedestrian", "footway", "path"]:
        return 5
    else:
        return 10