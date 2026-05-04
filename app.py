import streamlit as st
import osmnx as ox
import networkx as nx
import folium
import time
from streamlit.components.v1 import html


st.set_page_config(
    page_title="Clear Paths Guimarães",
    layout="wide"
)

st.title("Clear Paths Guimarães")
st.write("Sistema de recomendação de percursos pedonais acessíveis em Guimarães.")


@st.cache_resource
def carregar_grafo():
    G = ox.graph_from_place("Guimarães, Portugal", network_type="walk")
    G = ox.project_graph(G)
    return G


G = carregar_grafo()


locais = {
    "Campus de Azurém": (41.4446, -8.2944),
    "Largo do Toural": (41.4411, -8.2936),
    "Estação CP de Guimarães": (41.4358, -8.2956),
    "Castelo de Guimarães": (41.4479, -8.2908),
    "Centro Cultural Vila Flor": (41.4377, -8.2966)
}


st.sidebar.header("Configuração da rota")

origem_nome = st.sidebar.selectbox("Origem", list(locais.keys()))
destino_nome = st.sidebar.selectbox("Destino", list(locais.keys()), index=1)

perfil = st.sidebar.selectbox(
    "Perfil do utilizador",
    [
        "Normal",
        "Idoso",
        "Mobilidade reduzida",
        "Sensível ao calor/poluição"
    ]
)

algoritmo = st.sidebar.selectbox(
    "Algoritmo de procura",
    [
        "Dijkstra",
        "A*",
        "BFS"
    ]
)

condicao = st.sidebar.selectbox(
    "Condição ambiental",
    [
        "Normal",
        "Calor",
        "Chuva",
        "Má qualidade do ar"
    ]
)


def aplicar_custos(G, perfil, condicao):
    for u, v, k, data in G.edges(keys=True, data=True):
        distancia = data.get("length", 1)

        custo = distancia

        highway = data.get("highway", "")
        surface = data.get("surface", "")
        sidewalk = data.get("sidewalk", "")
        lit = data.get("lit", "")

        if isinstance(highway, list):
            highway = highway[0]

        if isinstance(surface, list):
            surface = surface[0]

        if isinstance(sidewalk, list):
            sidewalk = sidewalk[0]

        if isinstance(lit, list):
            lit = lit[0]

        # Penalização por escadas
        if highway == "steps":
            custo += 200

        # Penalização por piso irregular
        if surface in ["cobblestone", "gravel", "unpaved", "ground"]:
            custo += 40

        # Penalização por falta de passeio
        if sidewalk in ["no", "none"]:
            custo += 50

        # Penalização por pouca iluminação
        if lit == "no":
            custo += 30

        # Perfis
        if perfil == "Idoso":
            if highway == "steps":
                custo += 200
            if surface in ["cobblestone", "gravel", "unpaved", "ground"]:
                custo += 50

        elif perfil == "Mobilidade reduzida":
            if highway == "steps":
                custo += 10000
            if surface in ["cobblestone", "gravel", "unpaved", "ground"]:
                custo += 100
            if sidewalk in ["no", "none"]:
                custo += 100

        elif perfil == "Sensível ao calor/poluição":
            custo += 20

        # Condições ambientais
        if condicao == "Chuva":
            if surface in ["cobblestone", "gravel", "unpaved", "ground"]:
                custo += 70
            if highway == "steps":
                custo += 100

        elif condicao == "Calor":
            custo += 30

        elif condicao == "Má qualidade do ar":
            # aproximação: ruas principais recebem penalização maior
            if highway in ["primary", "secondary", "tertiary"]:
                custo += 80
            else:
                custo += 20

        data["custo"] = custo

    return G


def heuristica(n1, n2):
    x1 = G.nodes[n1]["x"]
    y1 = G.nodes[n1]["y"]
    x2 = G.nodes[n2]["x"]
    y2 = G.nodes[n2]["y"]

    return ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5


def calcular_rota(G, origem, destino, algoritmo):
    inicio = time.time()

    origem_node = ox.distance.nearest_nodes(G, origem[1], origem[0])
    destino_node = ox.distance.nearest_nodes(G, destino[1], destino[0])

    if algoritmo == "Dijkstra":
        rota = nx.shortest_path(
            G,
            origem_node,
            destino_node,
            weight="custo"
        )

    elif algoritmo == "A*":
        rota = nx.astar_path(
            G,
            origem_node,
            destino_node,
            heuristic=heuristica,
            weight="custo"
        )

    elif algoritmo == "BFS":
        rota = nx.shortest_path(
            G,
            origem_node,
            destino_node
        )

    fim = time.time()

    tempo = fim - inicio

    return rota, tempo


def calcular_distancia_rota(G, rota):
    distancia = 0
    custo = 0

    for i in range(len(rota) - 1):
        u = rota[i]
        v = rota[i + 1]

        dados_arestas = G.get_edge_data(u, v)
        primeira_aresta = list(dados_arestas.values())[0]

        distancia += primeira_aresta.get("length", 0)
        custo += primeira_aresta.get("custo", primeira_aresta.get("length", 0))

    return distancia, custo


def criar_mapa(G, rota):
    rota_latlon = []

    for node in rota:
        ponto = G.nodes[node]
        rota_latlon.append((ponto["y"], ponto["x"]))

    mapa = folium.Map(
        location=rota_latlon[0],
        zoom_start=15
    )

    folium.Marker(
        rota_latlon[0],
        popup="Origem",
        icon=folium.Icon(color="green")
    ).add_to(mapa)

    folium.Marker(
        rota_latlon[-1],
        popup="Destino",
        icon=folium.Icon(color="red")
    ).add_to(mapa)

    folium.PolyLine(
        rota_latlon,
        weight=6,
        tooltip="Rota recomendada"
    ).add_to(mapa)

    return mapa


if st.sidebar.button("Calcular rota"):
    if origem_nome == destino_nome:
        st.warning("A origem e o destino não podem ser iguais.")
    else:
        G = aplicar_custos(G, perfil, condicao)

        origem = locais[origem_nome]
        destino = locais[destino_nome]

        rota, tempo = calcular_rota(G, origem, destino, algoritmo)

        distancia, custo = calcular_distancia_rota(G, rota)

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Distância", f"{distancia/1000:.2f} km")
        col2.metric("Custo total", f"{custo:.2f}")
        col3.metric("Tempo", f"{tempo:.4f} s")
        col4.metric("Nós na rota", len(rota))

        mapa = criar_mapa(G, rota)

        html(mapa._repr_html_(), height=600)