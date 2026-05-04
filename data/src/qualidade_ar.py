import pandas as pd

ar = pd.read_excel("data/raw/qualidade_ar/qualidade_ar_2024.xlsx")

print(ar.head())

# função custo
def condicao_qualidade_ar(valor_pm10):
    if valor_pm10 >= 50:
        return "ma"
    elif valor_pm10 >= 25:
        return "media"
    else:
        return "boa"
    

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