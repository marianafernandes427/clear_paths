import os
import time
import folium
import osmnx as ox
import networkx as nx

from estado import PERFIS, PerfilUtilizador, Estado
from problema import ProblemaRotaUrbana
from heuristicas import criar_heuristica


def preparar_grafo(project_place: str = "Guimarães, Portugal"):
    # Tentar carregar do ficheiro local primeiro
    local_file = "data/raw/osm/guimaraes_walk.graphml"
    if os.path.exists(local_file):
        print(f"[PREPARAR_GRAFO] Carregando grafo do ficheiro local: {local_file}")
        try:
            G = nx.read_graphml(local_file)
            print(f"[PREPARAR_GRAFO] Grafo carregado com sucesso!")
        except Exception as e:
            print(f"[PREPARAR_GRAFO] Erro ao carregar ficheiro local: {e}")
            print(f"[PREPARAR_GRAFO] Tentando descarregar do OSM...")
            G = ox.graph_from_place(project_place, network_type="walk")
            G = ox.project_graph(G)
    else:
        print(f"[PREPARAR_GRAFO] Ficheiro local não encontrado, descarregando do OSM...")
        G = ox.graph_from_place(project_place, network_type="walk")
        G = ox.project_graph(G)

    # preencher custos por perfil será feito depois; aqui apenas normalizamos atributos
    for u, v, k, data in G.edges(keys=True, data=True):
        # normalizar campos usados pelo modelo
        data.setdefault("length", data.get("length", 1.0))
        data.setdefault("distancia", data.get("length"))
        data.setdefault("poluicao", data.get("poluicao", 0.0))
        data.setdefault("ruido", data.get("ruido", 0.0))
        data.setdefault("sombra", data.get("sombra", 0.0))
        data.setdefault("acessibilidade", data.get("accessibility", 1.0))
        data.setdefault("inclinacao", data.get("incline", 0.0))

    coords = {n: (d["x"], d["y"]) for n, d in G.nodes(data=True)}

    # converter para formato dict[u][v] -> atributos (usado por ProblemaRotaUrbana)
    grafo_dict: dict = {}
    for u, v, k, data in G.edges(keys=True, data=True):
        grafo_dict.setdefault(u, {})
        # copia reduzida dos atributos (evita referências inesperadas)
        atrib = {
            "distancia": data.get("distancia", data.get("length", 0.0)),
            "poluicao": data.get("poluicao", 0.0),
            "ruido": data.get("ruido", 0.0),
            "sombra": data.get("sombra", 0.0),
            "acessibilidade": data.get("acessibilidade", 1.0),
            "inclinacao": data.get("inclinacao", 0.0),
            **{k: v for k, v in data.items()},
        }
        grafo_dict[u][v] = atrib

    return G, grafo_dict, coords


def aplicar_custo_por_perfil_nx(G: nx.MultiDiGraph, perfil: PerfilUtilizador):
    # Aceitar também nomes de perfil ou dicionários: garantir que temos um
    # `PerfilUtilizador` com valores numéricos coerentes.
    if not isinstance(perfil, PerfilUtilizador):
        try:
            if isinstance(perfil, str):
                perfil = PERFIS.get(perfil, PERFIS["padrao"])
            elif isinstance(perfil, dict):
                perfil = PerfilUtilizador(**perfil)
            else:
                perfil = PERFIS["padrao"]
        except Exception:
            perfil = PERFIS["padrao"]

    # Construir uma cópia sanitizada do perfil com pesos convertidos para float
    default = PERFIS["padrao"]
    try:
        perfil_sanitizado = PerfilUtilizador(
            nome=str(getattr(perfil, "nome", default.nome)),
            peso_distancia=float(getattr(perfil, "peso_distancia", default.peso_distancia)),
            peso_poluicao=float(getattr(perfil, "peso_poluicao", default.peso_poluicao)),
            peso_ruido=float(getattr(perfil, "peso_ruido", default.peso_ruido)),
            peso_inclinacao=float(getattr(perfil, "peso_inclinacao", default.peso_inclinacao)),
            peso_sombra=float(getattr(perfil, "peso_sombra", default.peso_sombra)),
            peso_acessibilidade=float(getattr(perfil, "peso_acessibilidade", default.peso_acessibilidade)),
            velocidade_media=float(getattr(perfil, "velocidade_media", default.velocidade_media)),
            max_inclinacao=(None if getattr(perfil, "max_inclinacao", default.max_inclinacao) is None else float(getattr(perfil, "max_inclinacao", default.max_inclinacao))),
        )
    except Exception:
        perfil_sanitizado = default

    perfil = perfil_sanitizado

    for u, v, k, data in G.edges(keys=True, data=True):
        # Converter valores para float (GraphML carrega como strings)
        try:
            distancia = float(data.get("length", data.get("distancia", 0.0)))
        except (ValueError, TypeError):
            distancia = 0.0
        
        try:
            poluicao = float(data.get("poluicao", 0.0))
        except (ValueError, TypeError):
            poluicao = 0.0
        
        try:
            ruido = float(data.get("ruido", 0.0))
        except (ValueError, TypeError):
            ruido = 0.0
        
        try:
            sombra = float(data.get("sombra", 0.0))
        except (ValueError, TypeError):
            sombra = 0.0
        
        try:
            acessibilidade = float(data.get("acessibilidade", data.get("accessibility", 1.0)))
        except (ValueError, TypeError):
            acessibilidade = 1.0
        
        try:
            inclinacao = float(data.get("inclinacao", data.get("incline", 0.0)))
        except (ValueError, TypeError):
            inclinacao = 0.0
        
        atrib = {
            "distancia": distancia,
            "poluicao": poluicao,
            "ruido": ruido,
            "sombra": sombra,
            "acessibilidade": acessibilidade,
            "inclinacao": inclinacao,
        }
        data["custo"] = perfil.custo_aresta(atrib)


def criar_heur_fn(heur, problema, perfil):
    def fn(u, v):
        est = Estado(no_atual=u, perfil=perfil)
        return float(heur(est, problema))

    return fn


def calcular_dist_e_custo(G: nx.MultiDiGraph, rota: list):
    distancia = 0.0
    custo = 0.0
    for i in range(len(rota) - 1):
        u = rota[i]
        v = rota[i + 1]
        dados = G.get_edge_data(u, v)
        if not dados:
            continue
        primeiro = list(dados.values())[0]
        distancia += primeiro.get("length", primeiro.get("distancia", 0.0))
        custo += primeiro.get("custo", primeiro.get("length", 0.0))
    return distancia, custo


def criar_mapa_folium(G: nx.MultiDiGraph, rota: list, out_html: str = "rota.html"):
    rota_latlon = []
    for node in rota:
        n = G.nodes[node]
        rota_latlon.append((n["y"], n["x"]))

    mapa = folium.Map(location=rota_latlon[0], zoom_start=15)
    folium.Marker(rota_latlon[0], popup="Origem", icon=folium.Icon(color="green")).add_to(mapa)
    folium.Marker(rota_latlon[-1], popup="Destino", icon=folium.Icon(color="red")).add_to(mapa)
    folium.PolyLine(rota_latlon, weight=6, tooltip="Rota recomendada").add_to(mapa)
    mapa.save(out_html)
    return out_html


def main():
    # parâmetros simples — pode alterar
    origem_coord = (41.4446, -8.2944)  # Campus de Azurém (lat, lon)
    destino_coord = (41.4479, -8.2908)  # Castelo de Guimarães (lat, lon)
    perfil_nome = "padrao"
    heur_tipo = "euclidiana"

    print("Carregando grafo (pode demorar alguns segundos)...")
    G, grafo_dict, coords = preparar_grafo()

    perfil = PERFIS.get(perfil_nome, PERFIS["padrao"])

    # preparar custos na estrutura networkx
    aplicar_custo_por_perfil_nx(G, perfil)

    # escolher nós mais próximos das coordenadas
    origem_node = ox.distance.nearest_nodes(G, origem_coord[1], origem_coord[0])
    destino_node = ox.distance.nearest_nodes(G, destino_coord[1], destino_coord[0])

    print(f"Origem nó: {origem_node}  Destino nó: {destino_node}")

    problema = ProblemaRotaUrbana(grafo=grafo_dict, coords=coords, no_origem=origem_node, no_destino=destino_node, perfil=perfil)

    heur = criar_heuristica(heur_tipo, perfil=perfil)
    heur_fn = criar_heur_fn(heur, problema, perfil)

    print("A executar A* (networkx) com heurística:", heur.nome)
    t0 = time.time()
    rota = nx.astar_path(G, origem_node, destino_node, heuristic=heur_fn, weight="custo")
    t1 = time.time()

    distancia, custo = calcular_dist_e_custo(G, rota)

    print("Rota encontrada (nós):", rota)
    print(f"Distância total: {distancia:.1f} m — Custo total: {custo:.2f}")
    print(f"Tempo A*: {t1 - t0:.4f}s — Nós na rota: {len(rota)}")

    out = criar_mapa_folium(G, rota, out_html="rota_integrada.html")
    print("Mapa guardado em:", out)


if __name__ == "__main__":
    main()
