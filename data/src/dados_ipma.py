import requests
import json

url = "https://api.ipma.pt/open-data/forecast/meteorology/cities/daily/1030800.json"

resposta = requests.get(url)
dados = resposta.json()

with open("data/raw/ipma/ipma_guimaraes.json", "w", encoding="utf-8") as f:
    json.dump(dados, f, ensure_ascii=False, indent=4)

print("Dados IPMA guardados.")


##### 
tmax = float(dados["data"][0]["tMax"])
prob_chuva = float(dados["data"][0]["precipitaProb"])

if tmax >= 30:
    condicao = "calor"

if prob_chuva >= 60:
    condicao = "chuva"