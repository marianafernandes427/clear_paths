import pandas as pd
from pathlib import Path

EXCEL_PATH = Path(__file__).resolve().parents[1] / "raw" / "qualidade_ar_2024.xlsx"

ar = pd.read_excel(EXCEL_PATH)
print(ar.head())
print(ar.columns)


# função custo
def condicao_qualidade_ar(valor_pm10):
    if valor_pm10 >= 50:
        return "ma"
    elif valor_pm10 >= 25:
        return "media"
    else:
        return "boa"

pm10_medio = ar["Partículas < 10 µm (µg/m3)"].mean()
print(pm10_medio)
qualidade = condicao_qualidade_ar(pm10_medio)
#print("Qualidade do ar:", qualidade)    

# pôr no grafo
def custo_poluicao(row, qualidade_ar):
    highway = str(row.get("highway", ""))

    if qualidade_ar == "boa":
        return 0

    if qualidade_ar == "media":
        if highway in ["primary", "secondary", "tertiary"]:
            return 20
        return 5

    if qualidade_ar == "ma":
        if highway in ["primary", "secondary", "tertiary"]:
            return 60
        return 20

def aplicar_custo_ar_grafo(G):
    for u, v, k, data in G.edges(keys=True, data=True):

        custo_extra = custo_poluicao(data, qualidade)

        data["custo_ar"] = custo_extra

    return G