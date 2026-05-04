import osmnx as ox
import networkx as nx
import requests
import math

# =========================
# 1. CARREGAR GRAFO
# =========================
G = ox.graph_from_xml("proj/map.osm")
print(G)

# =========================
# 2. WEATHER API
# =========================
api_key = "86ddf3e584f443a298a171037261904"

def get_current_weather(location):
    url = "http://api.weatherapi.com/v1/current.json"

    params = {
        "key": api_key,
        "q": location,
        "aqi": "no",
        "lang": "pt"
    }

    data = requests.get(url, params=params).json()

    return {
        "temp_c": data["current"]["temp_c"],
        "feelslike_c": data["current"]["feelslike_c"],
        "wind_kph": data["current"]["wind_kph"],
        "rain": 1 if "rain" in data["current"]["condition"]["text"].lower() else 0,
        "condition": data["current"]["condition"]["text"]
    }

weather = get_current_weather("Guimarães")

# =========================
# 3. ATRIBUIR CLIMA AO GRAFO
# =========================
def assign_weather_to_graph(G, weather):
    for node in G.nodes:
        G.nodes[node]["temp"] = weather["temp_c"]
        G.nodes[node]["wind"] = weather["wind_kph"]
        G.nodes[node]["rain"] = weather["rain"]

assign_weather_to_graph(G, weather)

# =========================
# 4. FUNÇÃO DE CUSTO (IA)
# =========================
def node_cost(node, G):
    temp = G.nodes[node].get("temp", 20)
    wind = G.nodes[node].get("wind", 0)
    rain = G.nodes[node].get("rain", 0)

    cost = 1

    cost += rain * 0.6
    cost += wind / 50

    if temp > 30:
        cost += 0.3

    return cost

# =========================
# 5. PESO DAS ARESTAS
# =========================
def edge_weight(u, v, data, G):
    base = data.get("length", 1)
    return base * (node_cost(u, G) + node_cost(v, G)) / 2

# =========================
# 6. HEURÍSTICA (A*)
# =========================
def heuristic(u, v, G):
    x1, y1 = G.nodes[u]["x"], G.nodes[u]["y"]
    x2, y2 = G.nodes[v]["x"], G.nodes[v]["y"]

    return math.sqrt((x1 - x2)**2 + (y1 - y2)**2)

# =========================
# 7. ESCOLHER ORIGEM / DESTINO
# =========================
orig = list(G.nodes)[0]
dest = list(G.nodes)[-1]

# =========================
# 8. A* (PROCURA INFORMADA)
# =========================
path = nx.astar_path(
    G,
    orig,
    dest,
    heuristic=lambda u, v: heuristic(u, dest, G),
    weight=lambda u, v, d: edge_weight(u, v, d, G)
)

print("Caminho encontrado:", path)

# =========================
# 9. VISUALIZAR
# =========================
ox.plot_graph_route(G, path)

""" Adicionar mais critérios
Definir dificuldade
definir se é a pé , bicicleta, correr
adicionar idade
tipo de estrada
"""