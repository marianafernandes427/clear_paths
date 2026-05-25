from __future__ import annotations

import heapq
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple

from estado import Estado
from heuristicas import Heuristica, HeuristicaNula, HeuristicaEuclidiana


# Resultado da procura
@dataclass
class ResultadoProcura:
    algoritmo: str
    sucesso: bool
    caminho: List[int] = field(default_factory=list)
    custo: float = float("inf")
    distancia_total: float = 0.0
    nos_explorados: int = 0
    nos_gerados: int = 0
    tempo_execucao: float = 0.0
    estado_final: Optional[Estado] = None
    heuristica: str = "N/A"
    mensagem: str = ""

    def resumo(self) -> dict:
        return {
            "algoritmo":       self.algoritmo,
            "sucesso":         self.sucesso,
            "custo":           round(self.custo, 4),
            "distancia_m":     round(self.distancia_total, 1),
            "nos_caminho":     len(self.caminho),
            "nos_explorados":  self.nos_explorados,
            "nos_gerados":     self.nos_gerados,
            "tempo_s":         round(self.tempo_execucao, 4),
            "heuristica":      self.heuristica,
        }

    def __repr__(self) -> str:
        status = "✓" if self.sucesso else "✗"
        return (
            f"[{status}] {self.algoritmo} | custo={self.custo:.2f} "
            f"| dist={self.distancia_total:.0f}m "
            f"| explorados={self.nos_explorados} "
            f"| t={self.tempo_execucao:.3f}s"
        )



# BFS — Breadth-First Search
def bfs(problema, limite_nos: int = 500_000) -> ResultadoProcura:
    t0 = time.perf_counter()
    estado_inicial = problema.estado_inicial()

    if problema.eh_objetivo(estado_inicial):
        return ResultadoProcura(
            algoritmo="BFS", sucesso=True,
            caminho=list(estado_inicial.caminho),
            custo=0.0, distancia_total=0.0,
            tempo_execucao=time.perf_counter() - t0,
            estado_final=estado_inicial,
        )

    fronteira: deque[Estado] = deque([estado_inicial])
    visitados: set[int] = {estado_inicial.no_atual}
    nos_gerados = 1
    nos_explorados = 0

    while fronteira:
        if nos_explorados >= limite_nos:
            return ResultadoProcura(
                algoritmo="BFS", sucesso=False,
                nos_explorados=nos_explorados, nos_gerados=nos_gerados,
                tempo_execucao=time.perf_counter() - t0,
                mensagem=f"Limite de {limite_nos} nós atingido.",
            )

        estado = fronteira.popleft()
        nos_explorados += 1

        for vizinho, atributos in problema.acoes(estado):
            novo_estado = problema.sucessor(estado, vizinho, atributos)
            if problema.eh_objetivo(novo_estado):
                return ResultadoProcura(
                    algoritmo="BFS", sucesso=True,
                    caminho=list(novo_estado.caminho),
                    custo=novo_estado.custo_g,
                    distancia_total=novo_estado.distancia_total,
                    nos_explorados=nos_explorados,
                    nos_gerados=nos_gerados,
                    tempo_execucao=time.perf_counter() - t0,
                    estado_final=novo_estado,
                )
            if vizinho not in visitados:
                visitados.add(vizinho)
                fronteira.append(novo_estado)
                nos_gerados += 1

    return ResultadoProcura(
        algoritmo="BFS", sucesso=False,
        nos_explorados=nos_explorados, nos_gerados=nos_gerados,
        tempo_execucao=time.perf_counter() - t0,
        mensagem="Fronteira vazia — destino inacessível.",
    )


# DFS — Depth-First Search
def dfs(
    problema,
    limite_profundidade: int = 1000,
    limite_nos: int = 500_000,
) -> ResultadoProcura:
    t0 = time.perf_counter()
    estado_inicial = problema.estado_inicial()

    if problema.eh_objetivo(estado_inicial):
        return ResultadoProcura(
            algoritmo="DFS", sucesso=True,
            caminho=list(estado_inicial.caminho),
            custo=0.0, distancia_total=0.0,
            tempo_execucao=time.perf_counter() - t0,
            estado_final=estado_inicial,
        )

    # Pilha: (estado, profundidade)
    pilha: list[Tuple[Estado, int]] = [(estado_inicial, 0)]
    visitados: set[int] = set()
    nos_gerados = 1
    nos_explorados = 0

    while pilha:
        if nos_explorados >= limite_nos:
            return ResultadoProcura(
                algoritmo="DFS", sucesso=False,
                nos_explorados=nos_explorados, nos_gerados=nos_gerados,
                tempo_execucao=time.perf_counter() - t0,
                mensagem=f"Limite de {limite_nos} nós atingido.",
            )

        estado, profundidade = pilha.pop()

        if estado.no_atual in visitados:
            continue
        visitados.add(estado.no_atual)
        nos_explorados += 1

        if problema.eh_objetivo(estado):
            return ResultadoProcura(
                algoritmo="DFS", sucesso=True,
                caminho=list(estado.caminho),
                custo=estado.custo_g,
                distancia_total=estado.distancia_total,
                nos_explorados=nos_explorados,
                nos_gerados=nos_gerados,
                tempo_execucao=time.perf_counter() - t0,
                estado_final=estado,
            )

        if profundidade < limite_profundidade:
            for vizinho, atributos in problema.acoes(estado):
                if vizinho not in visitados:
                    novo_estado = problema.sucessor(estado, vizinho, atributos)
                    pilha.append((novo_estado, profundidade + 1))
                    nos_gerados += 1

    return ResultadoProcura(
        algoritmo="DFS", sucesso=False,
        nos_explorados=nos_explorados, nos_gerados=nos_gerados,
        tempo_execucao=time.perf_counter() - t0,
        mensagem="Fronteira vazia — destino inacessível ou limite atingido.",
    )


# UCS — Uniform Cost Search (Dijkstra)
def ucs(problema, limite_nos: int = 500_000) -> ResultadoProcura:
    t0 = time.perf_counter()
    estado_inicial = problema.estado_inicial()

    # Heap: (custo_g, contador_desempate, estado)
    contador = 0
    fronteira: list[Tuple[float, int, Estado]] = [(0.0, contador, estado_inicial)]
    visitados: Dict[int, float] = {}  # no -> melhor custo registado
    nos_gerados = 1
    nos_explorados = 0

    while fronteira:
        if nos_explorados >= limite_nos:
            return ResultadoProcura(
                algoritmo="UCS", sucesso=False,
                nos_explorados=nos_explorados, nos_gerados=nos_gerados,
                tempo_execucao=time.perf_counter() - t0,
                mensagem=f"Limite de {limite_nos} nós atingido.",
            )

        custo, _, estado = heapq.heappop(fronteira)
        nos_explorados += 1

        if problema.eh_objetivo(estado):
            return ResultadoProcura(
                algoritmo="UCS", sucesso=True,
                caminho=list(estado.caminho),
                custo=estado.custo_g,
                distancia_total=estado.distancia_total,
                nos_explorados=nos_explorados,
                nos_gerados=nos_gerados,
                tempo_execucao=time.perf_counter() - t0,
                estado_final=estado,
            )

        # Se já explorámos este nó com custo menor, ignorar
        if estado.no_atual in visitados and visitados[estado.no_atual] < custo:
            nos_explorados -= 1  # não conta como expansão real
            continue
        visitados[estado.no_atual] = custo

        for vizinho, atributos in problema.acoes(estado):
            novo_estado = problema.sucessor(estado, vizinho, atributos)
            novo_custo = novo_estado.custo_g

            if vizinho not in visitados or novo_custo < visitados.get(vizinho, float("inf")):
                contador += 1
                heapq.heappush(fronteira, (novo_custo, contador, novo_estado))
                nos_gerados += 1

    return ResultadoProcura(
        algoritmo="UCS", sucesso=False,
        nos_explorados=nos_explorados, nos_gerados=nos_gerados,
        tempo_execucao=time.perf_counter() - t0,
        mensagem="Fronteira vazia — destino inacessível.",
    )


# Greedy — Best-First Greedy Search
def greedy(
    problema,
    heuristica: Heuristica = None,
    limite_nos: int = 500_000,
) -> ResultadoProcura:
    t0 = time.perf_counter()
    heuristica = heuristica or HeuristicaEuclidiana()
    estado_inicial = problema.estado_inicial()

    if problema.eh_objetivo(estado_inicial):
        return ResultadoProcura(
            algoritmo="Greedy", sucesso=True,
            caminho=list(estado_inicial.caminho),
            custo=0.0, distancia_total=0.0,
            tempo_execucao=time.perf_counter() - t0,
            estado_final=estado_inicial,
            heuristica=heuristica.nome,
        )

    contador = 0
    h0 = heuristica(estado_inicial, problema)
    fronteira: list[Tuple[float, int, Estado]] = [(h0, contador, estado_inicial)]
    visitados: set[int] = set()
    nos_gerados = 1
    nos_explorados = 0

    while fronteira:
        if nos_explorados >= limite_nos:
            return ResultadoProcura(
                algoritmo="Greedy", sucesso=False,
                nos_explorados=nos_explorados, nos_gerados=nos_gerados,
                tempo_execucao=time.perf_counter() - t0,
                heuristica=heuristica.nome,
                mensagem=f"Limite de {limite_nos} nós atingido.",
            )

        _, _, estado = heapq.heappop(fronteira)

        if estado.no_atual in visitados:
            continue
        visitados.add(estado.no_atual)
        nos_explorados += 1

        if problema.eh_objetivo(estado):
            return ResultadoProcura(
                algoritmo="Greedy", sucesso=True,
                caminho=list(estado.caminho),
                custo=estado.custo_g,
                distancia_total=estado.distancia_total,
                nos_explorados=nos_explorados,
                nos_gerados=nos_gerados,
                tempo_execucao=time.perf_counter() - t0,
                estado_final=estado,
                heuristica=heuristica.nome,
            )

        for vizinho, atributos in problema.acoes(estado):
            if vizinho not in visitados:
                novo_estado = problema.sucessor(estado, vizinho, atributos)
                h = heuristica(novo_estado, problema)
                contador += 1
                heapq.heappush(fronteira, (h, contador, novo_estado))
                nos_gerados += 1

    return ResultadoProcura(
        algoritmo="Greedy", sucesso=False,
        nos_explorados=nos_explorados, nos_gerados=nos_gerados,
        tempo_execucao=time.perf_counter() - t0,
        heuristica=heuristica.nome,
        mensagem="Fronteira vazia — destino inacessível.",
    )


# A* — A-Star Search
def astar(
    problema,
    heuristica: Heuristica = None,
    limite_nos: int = 500_000,
) -> ResultadoProcura:
    t0 = time.perf_counter()
    heuristica = heuristica or HeuristicaEuclidiana()
    estado_inicial = problema.estado_inicial()

    if problema.eh_objetivo(estado_inicial):
        return ResultadoProcura(
            algoritmo="A*", sucesso=True,
            caminho=list(estado_inicial.caminho),
            custo=0.0, distancia_total=0.0,
            tempo_execucao=time.perf_counter() - t0,
            estado_final=estado_inicial,
            heuristica=heuristica.nome,
        )

    contador = 0
    h0 = heuristica(estado_inicial, problema)
    # Heap: (f = g + h, contador_desempate, estado)
    fronteira: list[Tuple[float, int, Estado]] = [(h0, contador, estado_inicial)]
    # Registo: no -> melhor g registado
    melhor_g: Dict[int, float] = {estado_inicial.no_atual: 0.0}
    nos_gerados = 1
    nos_explorados = 0

    while fronteira:
        if nos_explorados >= limite_nos:
            return ResultadoProcura(
                algoritmo="A*", sucesso=False,
                nos_explorados=nos_explorados, nos_gerados=nos_gerados,
                tempo_execucao=time.perf_counter() - t0,
                heuristica=heuristica.nome,
                mensagem=f"Limite de {limite_nos} nós atingido.",
            )

        f, _, estado = heapq.heappop(fronteira)
        nos_explorados += 1

        # Poda: se já encontrámos um caminho melhor para este nó, ignorar
        if estado.custo_g > melhor_g.get(estado.no_atual, float("inf")):
            nos_explorados -= 1
            continue

        if problema.eh_objetivo(estado):
            return ResultadoProcura(
                algoritmo="A*", sucesso=True,
                caminho=list(estado.caminho),
                custo=estado.custo_g,
                distancia_total=estado.distancia_total,
                nos_explorados=nos_explorados,
                nos_gerados=nos_gerados,
                tempo_execucao=time.perf_counter() - t0,
                estado_final=estado,
                heuristica=heuristica.nome,
            )

        for vizinho, atributos in problema.acoes(estado):
            novo_estado = problema.sucessor(estado, vizinho, atributos)
            novo_g = novo_estado.custo_g

            if novo_g < melhor_g.get(vizinho, float("inf")):
                melhor_g[vizinho] = novo_g
                h = heuristica(novo_estado, problema)
                f_novo = novo_g + h
                contador += 1
                heapq.heappush(fronteira, (f_novo, contador, novo_estado))
                nos_gerados += 1

    return ResultadoProcura(
        algoritmo="A*", sucesso=False,
        nos_explorados=nos_explorados, nos_gerados=nos_gerados,
        tempo_execucao=time.perf_counter() - t0,
        heuristica=heuristica.nome,
        mensagem="Fronteira vazia — destino inacessível.",
    )

# EXTRA
# A* Weighted — epsilon-admissível
def astar_weighted(
    problema,
    heuristica: Heuristica = None,
    w: float = 1.5,
    limite_nos: int = 500_000,
) -> ResultadoProcura:
    from heuristicas import HeuristicaWeighted
    heuristica = heuristica or HeuristicaEuclidiana()
    h_weighted = HeuristicaWeighted(heuristica, w=w)

    resultado = astar(problema, heuristica=h_weighted, limite_nos=limite_nos)
    resultado.algoritmo = f"A* Weighted (w={w})"
    return resultado


# EXTRA útil
# Comparação de algoritmos
def comparar_algoritmos(
    problema,
    heuristica: Heuristica = None,
    incluir: Optional[List[str]] = None,
) -> Dict[str, ResultadoProcura]:
    heuristica = heuristica or HeuristicaEuclidiana()
    todos = {
        "bfs":     lambda: bfs(problema),
        "dfs":     lambda: dfs(problema),
        "ucs":     lambda: ucs(problema),
        "greedy":  lambda: greedy(problema, heuristica),
        "astar":   lambda: astar(problema, heuristica),
        "astar_w": lambda: astar_weighted(problema, heuristica, w=1.5),
    }

    if incluir:
        selecionados = {k: v for k, v in todos.items() if k in incluir}
    else:
        selecionados = todos

    resultados = {}
    for nome, fn in selecionados.items():
        print(f"  → A executar {nome.upper()}...", end=" ", flush=True)
        r = fn()
        resultados[nome] = r
        print(r)

    return resultados


def tabela_comparativa(resultados: Dict[str, ResultadoProcura]) -> str:
    linhas = [
        f"{'Algoritmo':<22} {'Sucesso':<8} {'Custo':>10} {'Dist(m)':>10} "
        f"{'Explorados':>12} {'Gerados':>10} {'Tempo(s)':>10} {'Heurística':<25}",
        "-" * 110,
    ]
    for nome, r in resultados.items():
        status = "✓" if r.sucesso else "✗"
        linhas.append(
            f"{r.algoritmo:<22} {status:<8} {r.custo:>10.2f} {r.distancia_total:>10.1f} "
            f"{r.nos_explorados:>12} {r.nos_gerados:>10} {r.tempo_execucao:>10.4f} {r.heuristica:<25}"
        )
    return "\n".join(linhas)
