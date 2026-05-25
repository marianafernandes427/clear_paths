from __future__ import annotations

import math
from typing import Any, Callable, Dict, Iterator, List, Optional, Set, Tuple

from estado import Estado, PerfilUtilizador, PERFIS


# Problema
class ProblemaRotaUrbana:

    def __init__(
        self,
        grafo: Dict[int, Dict[int, dict]],
        coords: Dict[int, Tuple[float, float]],
        no_origem: int,
        no_destino: int,
        perfil: PerfilUtilizador = None,
        bloqueios: Optional[Set[int]] = None,
        arestas_bloqueadas: Optional[Set[Tuple[int, int]]] = None,
        condicoes_dinamicas: Optional[Dict[str, Any]] = None,
    ):
        self.grafo = grafo
        self.coords = coords
        self.no_origem = no_origem
        self.no_destino = no_destino
        self.perfil = perfil or PERFIS["padrao"]
        self.bloqueios: Set[int] = bloqueios or set()
        self.arestas_bloqueadas: Set[Tuple[int, int]] = arestas_bloqueadas or set()
        self.condicoes_dinamicas: Dict[str, Any] = condicoes_dinamicas or {}

        # Valida que origem e destino existem no grafo
        if no_origem not in grafo:
            raise ValueError(f"Nó de origem {no_origem} não existe no grafo.")
        if no_destino not in grafo:
            raise ValueError(f"Nó de destino {no_destino} não existe no grafo.")

    # Estado inicial
    def estado_inicial(self) -> Estado:
        return Estado(
            no_atual=self.no_origem,
            caminho=(self.no_origem,),
            perfil=self.perfil,
        )

    # Teste objetivo
    def eh_objetivo(self, estado: Estado) -> bool:
        return estado.no_atual == self.no_destino

    # Ações e sucessores
    def acoes(self, estado: Estado) -> Iterator[Tuple[int, dict]]:
        no = estado.no_atual
        vizinhos = self.grafo.get(no, {})

        for vizinho, atributos_base in vizinhos.items():
            # Verificar bloqueios de nós
            if vizinho in self.bloqueios:
                continue

            # Verificar bloqueios de arestas
            if (no, vizinho) in self.arestas_bloqueadas:
                continue

            # Evitar revisitar nós (ciclos)
            if estado.ja_visitou(vizinho):
                continue

            # Aplicar modificadores dinâmicos (clima, eventos, etc.)
            atributos = self._aplicar_condicoes_dinamicas(atributos_base, no, vizinho)

            # Verificar se a aresta é transitável para este perfil
            custo_teste = self.perfil.custo_aresta(atributos)
            if math.isinf(custo_teste):
                continue  # aresta intransitável (ex.: inclinação excessiva)

            yield vizinho, atributos

    def sucessor(self, estado: Estado, no_vizinho: int, atributos: dict) -> Estado:
        return estado.expandir(no_vizinho, atributos)

    # Custo
    def custo_caminho(self, caminho: List[int]) -> float:
        custo = 0.0
        for i in range(len(caminho) - 1):
            u, v = caminho[i], caminho[i + 1]
            atributos = self.grafo.get(u, {}).get(v, {})
            atributos = self._aplicar_condicoes_dinamicas(atributos, u, v)
            custo += self.perfil.custo_aresta(atributos)
        return custo

    # Modificadores dinâmicos (integração com Pessoa 4)
    def _aplicar_condicoes_dinamicas(
        self, atributos_base: dict, no_u: int, no_v: int
    ) -> dict:
        if not self.condicoes_dinamicas:
            return atributos_base

        # Cópia rasa para não modificar o grafo original
        atrib = dict(atributos_base)

        # Fator meteorológico: chuva
        if "fator_chuva" in self.condicoes_dinamicas:
            f = self.condicoes_dinamicas["fator_chuva"]
            atrib["inclinacao"] = atrib.get("inclinacao", 0.0) * (1.0 + f * 0.5)
            atrib["acessibilidade"] = max(0.0, atrib.get("acessibilidade", 1.0) - f * 0.2)

        # Fator meteorológico: calor (penaliza sensíveis)
        if "fator_calor" in self.condicoes_dinamicas and self.perfil.nome in ("idoso", "crianca"):
            f = self.condicoes_dinamicas["fator_calor"]
            atrib["poluicao"] = atrib.get("poluicao", 0.0) * (1.0 + f * 0.3)

        # Fator de poluição global (ex.: alerta de qualidade do ar)
        if "fator_poluicao" in self.condicoes_dinamicas:
            f = self.condicoes_dinamicas["fator_poluicao"]
            atrib["poluicao"] = atrib.get("poluicao", 0.0) * f

        # Modificadores de arestas específicas (do eventos.py)
        chave_aresta = (no_u, no_v)
        if "arestas_modificadas" in self.condicoes_dinamicas:
            mod = self.condicoes_dinamicas["arestas_modificadas"].get(chave_aresta, {})
            atrib.update(mod)

        return atrib

    # Gestão dinâmica de bloqueios (API para Pessoa 4)
    def bloquear_no(self, no: int) -> None:
        self.bloqueios.add(no)

    def desbloquear_no(self, no: int) -> None:
        self.bloqueios.discard(no)

    def bloquear_aresta(self, u: int, v: int, bidirecional: bool = False) -> None:
        self.arestas_bloqueadas.add((u, v))
        if bidirecional:
            self.arestas_bloqueadas.add((v, u))

    def desbloquear_aresta(self, u: int, v: int, bidirecional: bool = False) -> None:
        self.arestas_bloqueadas.discard((u, v))
        if bidirecional:
            self.arestas_bloqueadas.discard((v, u))

    def atualizar_condicoes(self, novas_condicoes: dict) -> None:
        self.condicoes_dinamicas.update(novas_condicoes)

    # Utilitários
    def distancia_euclidiana(self, no_a: int, no_b: int) -> float:
        xa, ya = self.coords[no_a]
        xb, yb = self.coords[no_b]
        return math.sqrt((xa - xb) ** 2 + (ya - yb) ** 2)

    def distancia_haversine(self, no_a: int, no_b: int) -> float:
        lat1, lon1 = self.coords[no_a]
        lat2, lon2 = self.coords[no_b]
        return _haversine(lat1, lon1, lat2, lon2)

    def info(self) -> dict:
        return {
            "no_origem": self.no_origem,
            "no_destino": self.no_destino,
            "perfil": self.perfil.nome,
            "nos_grafo": len(self.grafo),
            "nos_bloqueados": len(self.bloqueios),
            "arestas_bloqueadas": len(self.arestas_bloqueadas),
            "condicoes_dinamicas": list(self.condicoes_dinamicas.keys()),
        }

    def __repr__(self) -> str:
        return (
            f"ProblemaRotaUrbana("
            f"origem={self.no_origem}, destino={self.no_destino}, "
            f"perfil='{self.perfil.nome}', nós={len(self.grafo)})"
        )


# Função auxiliar
def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6_371_000.0  # raio da Terra em metros
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))
