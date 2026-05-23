import requests
import json
from pathlib import Path

url = "https://api.ipma.pt/open-data/forecast/meteorology/cities/daily/1030800.json"

resposta = requests.get(url)
dados = resposta.json()

output_path = Path(__file__).resolve().parents[1] / "raw" / "ipma"
output_path.mkdir(parents=True, exist_ok=True)
file_path = output_path / "ipma_guimaraes.json"

with open(file_path, "w", encoding="utf-8") as f:
    json.dump(dados, f, ensure_ascii=False, indent=4)

print(f"Dados IPMA guardados em {file_path}")


##### 
tmax = float(dados["data"][0]["tMax"])
prob_chuva = float(dados["data"][0]["precipitaProb"])

condicao = "normal"
if tmax >= 30:
    condicao = "calor"

elif prob_chuva >= 60:
    condicao = "chuva"

print("Temperatura máxima:", tmax)
print("Probabilidade de chuva:", prob_chuva)
print("Condição:", condicao)