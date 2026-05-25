from __future__ import annotations

import math
from abc import ABC, abstractmethod
from typing import Dict, Optional, Tuple

from estado import Estado, PerfilUtilizador
# from problema import ProblemaRotaUrbana  # importação tardia para evitar circular


# Interface base
class Heuristica(ABC):

    @abstractmethod
    def __call__(self, estado: Estado, problema) -> float:
        ...

    @property
    @abstractmethod
    def nome(self) -> str:
        ...

    @property
    def admissivel(self) -> bool:
        return False



# Heurística nula (BFS/UCS com f = g)
class HeuristicaNula(Heuristica):
    @property
    def nome(self) -> str:
        return "nula"

    @property
    def admissivel(self) -> bool:
        return True

    def __call__(self, estado: Estado, problema) -> float:
        return 0.0


# Heurísticas admissíveis
class HeuristicaEuclidiana(Heuristica):

    @property
    def nome(self) -> str:
        return "euclidiana"

    @property
    def admissivel(self) -> bool:
        return True

    def __call__(self, estado: Estado, problema) -> float:
        if estado.no_atual == problema.no_destino:
            return 0.0
        try:
            dist = problema.distancia_euclidiana(estado.no_atual, problema.no_destino)
        except (KeyError, TypeError):
            return 0.0
        # Escalar pelo peso de distância do perfil (garantia de admissibilidade)
        return dist * estado.perfil.peso_distancia


class HeuristicaHaversine(Heuristica):

    @property
    def nome(self) -> str:
        return "haversine"

    @property
    def admissivel(self) -> bool:
        return True

    def __call__(self, estado: Estado, problema) -> float:
        if estado.no_atual == problema.no_destino:
            return 0.0
        try:
            dist = problema.distancia_haversine(estado.no_atual, problema.no_destino)
        except (KeyError, TypeError):
            return 0.0
        return dist * estado.perfil.peso_distancia


class HeuristicaOtimista(Heuristica):

    def __init__(self, custo_minimo_por_metro: float = 0.9):
        self._fator = custo_minimo_por_metro

    @property
    def nome(self) -> str:
        return "otimista"

    @property
    def admissivel(self) -> bool:
        return True

    def __call__(self, estado: Estado, problema) -> float:
        if estado.no_atual == problema.no_destino:
            return 0.0
        try:
            dist = problema.distancia_euclidiana(estado.no_atual, problema.no_destino)
        except (KeyError, TypeError):
            return 0.0
        return dist * self._fator * estado.perfil.peso_distancia


# Heurísticas não-admissíveis (mais informadas, sem garantia de optimalidade)
class HeuristicaAmbiental(Heuristica):

    def __init__(
        self,
        poluicao_media: float = 0.3,
        ruido_medio: float = 0.4,
        fator_inflacao: float = 1.2,
    ):
        self._poluicao = poluicao_media
        self._ruido = ruido_medio
        self._inflacao = fator_inflacao

    @property
    def nome(self) -> str:
        return "ambiental"

    def __call__(self, estado: Estado, problema) -> float:
        if estado.no_atual == problema.no_destino:
            return 0.0
        try:
            dist = problema.distancia_euclidiana(estado.no_atual, problema.no_destino)
        except (KeyError, TypeError):
            return 0.0

        p = estado.perfil
        custo_est = (
            p.peso_distancia * dist
            + p.peso_poluicao * self._poluicao * dist
            + p.peso_ruido   * self._ruido    * dist
        )
        return custo_est * self._inflacao


class HeuristicaPerfilAdaptativa(Heuristica):
    # Inclinação média típica em Guimarães (terreno ondulado)
    _INCLINACAO_MEDIA_PCT = 3.5

    @property
    def nome(self) -> str:
        return "perfil_adaptativa"

    def __call__(self, estado: Estado, problema) -> float:
        if estado.no_atual == problema.no_destino:
            return 0.0
        try:
            dist = problema.distancia_euclidiana(estado.no_atual, problema.no_destino)
        except (KeyError, TypeError):
            return 0.0

        p = estado.perfil

        # Custo base de distância
        h = p.peso_distancia * dist

        # Penalização por inclinação estimada (eleva ≈ 3.5% da distância)
        subida_estimada = (self._INCLINACAO_MEDIA_PCT / 100.0) * dist
        h += p.peso_inclinacao * subida_estimada

        # Penalização ambiental adaptada ao perfil
        if p.nome in ("idoso", "crianca"):
            h *= 1.3  # perfis sensíveis — estimativa mais conservadora
        elif p.nome == "cadeira_rodas":
            h *= 1.5  # acessibilidade muito restritiva
        elif p.nome == "atleta":
            h *= 0.9  # atleta aceita rotas mais desafiadoras

        return h


class HeuristicaMultiObjetivo(Heuristica):
    def __init__(
        self,
        estatisticas_grafo: Optional[Dict[str, float]] = None,
        fator_inflacao: float = 1.0,
    ):

        defaults = {
            "poluicao_media": 0.25,
            "ruido_medio": 0.35,
            "inclinacao_media": 2.8,  # % — terreno típico de Guimarães
            "sombra_media": 0.2,
        }
        self._stats = {**defaults, **(estatisticas_grafo or {})}
        self._inflacao = fator_inflacao

    @property
    def nome(self) -> str:
        return f"multiobjetivo(w={self._inflacao:.1f})"

    def __call__(self, estado: Estado, problema) -> float:
        if estado.no_atual == problema.no_destino:
            return 0.0
        try:
            dist = problema.distancia_euclidiana(estado.no_atual, problema.no_destino)
        except (KeyError, TypeError):
            return 0.0

        p = estado.perfil
        s = self._stats

        subida_est = (s["inclinacao_media"] / 100.0) * dist

        h = (
            p.peso_distancia   * dist
            + p.peso_poluicao  * s["poluicao_media"] * dist
            + p.peso_ruido     * s["ruido_medio"]    * dist
            + p.peso_inclinacao * subida_est
            - p.peso_sombra    * s["sombra_media"]   * dist * 0.1
        )
        return max(0.0, h * self._inflacao)


class HeuristicaDijkstraPrecomputada(Heuristica):
    def __init__(self):
        self._custos: Dict[int, float] = {}
        self._problema_id: Optional[int] = None

    @property
    def nome(self) -> str:
        return "dijkstra_precomputada"

    @property
    def admissivel(self) -> bool:
        return True

    def precomputar(self, problema) -> None:
        import heapq

        destino = problema.no_destino
        grafo_reverso: Dict[int, Dict[int, dict]] = {}

        # Construir grafo reverso
        for u, vizinhos in problema.grafo.items():
            for v, atrib in vizinhos.items():
                if v not in grafo_reverso:
                    grafo_reverso[v] = {}
                grafo_reverso[v][u] = atrib

        # Dijkstra a partir do destino no grafo reverso
        dist = {destino: 0.0}
        heap = [(0.0, destino)]

        while heap:
            d, no = heapq.heappop(heap)
            if d > dist.get(no, math.inf):
                continue
            for vizinho, atrib in grafo_reverso.get(no, {}).items():
                custo = problema.perfil.custo_aresta(atrib)
                nova_dist = d + custo
                if nova_dist < dist.get(vizinho, math.inf):
                    dist[vizinho] = nova_dist
                    heapq.heappush(heap, (nova_dist, vizinho))

        self._custos = dist
        self._problema_id = id(problema)

    def __call__(self, estado: Estado, problema) -> float:
        # Auto-precomputa se necessário (ou se o problema mudou)
        if self._problema_id != id(problema) or not self._custos:
            self.precomputar(problema)
        return self._custos.get(estado.no_atual, math.inf)


# EXTRA
# Heurística A* Weighted (epsilon-admissível)

class HeuristicaWeighted(Heuristica):
    def __init__(self, heuristica_base: Heuristica, w: float = 1.5):
        if w < 1.0:
            raise ValueError("O fator w deve ser ≥ 1.0")
        self._h = heuristica_base
        self._w = w

    @property
    def nome(self) -> str:
        return f"weighted({self._h.nome}, w={self._w})"

    def __call__(self, estado: Estado, problema) -> float:
        return self._w * self._h(estado, problema)


# Fábrica de heurísticas
def criar_heuristica(
    tipo: str,
    perfil: Optional[PerfilUtilizador] = None,
    **kwargs,
) -> Heuristica:
    catalogo = {
        "nula":                  HeuristicaNula,
        "euclidiana":            HeuristicaEuclidiana,
        "haversine":             HeuristicaHaversine,
        "otimista":              HeuristicaOtimista,
        "ambiental":             HeuristicaAmbiental,
        "perfil_adaptativa":     HeuristicaPerfilAdaptativa,
        "multiobjetivo":         HeuristicaMultiObjetivo,
        "dijkstra_precomputada": HeuristicaDijkstraPrecomputada,
    }

    if tipo == "weighted_euclidiana":
        return HeuristicaWeighted(HeuristicaEuclidiana(), w=kwargs.get("w", 1.5))
    if tipo == "weighted_multiobjetivo":
        return HeuristicaWeighted(HeuristicaMultiObjetivo(), w=kwargs.get("w", 1.5))
    if tipo == "auto" and perfil is not None:
        # Seleção automática baseada no perfil
        if perfil.nome == "cadeira_rodas":
            return HeuristicaPerfilAdaptativa()
        if perfil.nome in ("idoso", "crianca"):
            return HeuristicaMultiObjetivo()
        if perfil.nome == "atleta":
            return HeuristicaWeighted(HeuristicaEuclidiana(), w=1.2)
        return HeuristicaEuclidiana()

    cls = catalogo.get(tipo)
    if cls is None:
        raise ValueError(
            f"Heurística '{tipo}' desconhecida. "
            f"Opções: {sorted(catalogo.keys()) + ['weighted_euclidiana', 'weighted_multiobjetivo', 'auto']}"
        )
    return cls(**{k: v for k, v in kwargs.items() if k != "w"})


# Comparação de heurísticas
def comparar_heuristicas(
    heuristicas: list[Heuristica],
    estado: Estado,
    problema,
) -> dict:
    return {h.nome: round(h(estado, problema), 4) for h in heuristicas}
