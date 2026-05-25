from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Tuple, FrozenSet


# Perfis de utilizador
PERFIS_DISPONIVEIS = ("padrao", "idoso", "cadeira_rodas", "atleta", "crianca", "ciclista")


@dataclass(frozen=True)
class PerfilUtilizador:
    nome: str
    peso_distancia: float = 1.0
    peso_poluicao: float = 1.0
    peso_ruido: float = 1.0
    peso_inclinacao: float = 1.0
    peso_sombra: float = 1.0
    peso_acessibilidade: float = 1.0
    velocidade_media: float = 1.4          # ~5 km/h — caminhada normal
    max_inclinacao: Optional[float] = None # sem restrição por defeito

    def custo_aresta(self, atributos: dict) -> float:
        inclinacao = atributos.get("inclinacao", 0.0)

        # Verificar restrição de inclinação
        if self.max_inclinacao is not None and abs(inclinacao) > self.max_inclinacao:
            return float("inf")

        distancia    = atributos.get("distancia", 0.0)
        poluicao     = atributos.get("poluicao", 0.0)
        ruido        = atributos.get("ruido", 0.0)
        sombra       = atributos.get("sombra", 0.0)        # 0–1 (1 = totalmente ensombrado)
        acessib      = atributos.get("acessibilidade", 1.0) # 0–1 (1 = totalmente acessível)

        # Penalização de acessibilidade (quanto menor, maior a penalização)
        penalizacao_acessib = (1.0 - acessib) * self.peso_acessibilidade * 50.0

        custo = (
            self.peso_distancia   * distancia
            + self.peso_poluicao  * poluicao  * distancia
            + self.peso_ruido     * ruido     * distancia
            + self.peso_inclinacao * max(0.0, inclinacao) * distancia  # só sobe
            - self.peso_sombra    * sombra    * distancia * 0.1        # bónus de sombra
            + penalizacao_acessib
        )
        return max(0.0, custo)


# Perfis pré-definidos
PERFIS: dict[str, PerfilUtilizador] = {
    "padrao": PerfilUtilizador(
        nome="padrao",
        peso_distancia=1.0, peso_poluicao=0.5, peso_ruido=0.5,
        peso_inclinacao=0.3, peso_sombra=0.2, peso_acessibilidade=0.5,
        velocidade_media=1.4,
    ),
    "idoso": PerfilUtilizador(
        nome="idoso",
        peso_distancia=0.8, peso_poluicao=2.0, peso_ruido=1.5,
        peso_inclinacao=2.5, peso_sombra=1.0, peso_acessibilidade=2.0,
        velocidade_media=0.9, max_inclinacao=8.0,
    ),
    "cadeira_rodas": PerfilUtilizador(
        nome="cadeira_rodas",
        peso_distancia=1.0, peso_poluicao=1.0, peso_ruido=0.5,
        peso_inclinacao=5.0, peso_sombra=0.5, peso_acessibilidade=10.0,
        velocidade_media=0.8, max_inclinacao=5.0,
    ),
    "atleta": PerfilUtilizador(
        nome="atleta",
        peso_distancia=1.5, peso_poluicao=1.5, peso_ruido=0.2,
        peso_inclinacao=0.1, peso_sombra=0.5, peso_acessibilidade=0.2,
        velocidade_media=3.5,
    ),
    "crianca": PerfilUtilizador(
        nome="crianca",
        peso_distancia=0.7, peso_poluicao=2.5, peso_ruido=2.0,
        peso_inclinacao=1.5, peso_sombra=1.5, peso_acessibilidade=1.5,
        velocidade_media=1.1, max_inclinacao=12.0,
    ),
    "ciclista": PerfilUtilizador(
        nome="ciclista",
        peso_distancia=1.2, peso_poluicao=1.0, peso_ruido=0.3,
        peso_inclinacao=1.8, peso_sombra=0.3, peso_acessibilidade=0.5,
        velocidade_media=4.2, max_inclinacao=15.0,
    ),
}



# Estado
@dataclass
class Estado:
    no_atual: int
    custo_g: float = 0.0
    poluicao_acumulada: float = 0.0
    ruido_acumulado: float = 0.0
    inclinacao_acumulada: float = 0.0
    sombra_acumulada: float = 0.0
    distancia_total: float = 0.0
    caminho: Tuple[int, ...] = field(default_factory=tuple)
    perfil: PerfilUtilizador = field(default_factory=lambda: PERFIS["padrao"])

    # Identidade e hashing
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Estado):
            return NotImplemented
        return self.no_atual == other.no_atual

    def __hash__(self) -> int:
        return hash(self.no_atual)

    def __lt__(self, other: "Estado") -> bool:
        return self.custo_g < other.custo_g

    # Navegação
    @property
    def visitados(self) -> FrozenSet[int]:
        return frozenset(self.caminho)

    def ja_visitou(self, no: int) -> bool:
        return no in self.visitados

    def expandir(self, no_vizinho: int, atributos_aresta: dict) -> "Estado":
        custo_aresta = self.perfil.custo_aresta(atributos_aresta)

        return Estado(
            no_atual=no_vizinho,
            custo_g=self.custo_g + custo_aresta,
            poluicao_acumulada=(
                self.poluicao_acumulada
                + atributos_aresta.get("poluicao", 0.0)
                * atributos_aresta.get("distancia", 0.0)
            ),
            ruido_acumulado=(
                self.ruido_acumulado
                + atributos_aresta.get("ruido", 0.0)
                * atributos_aresta.get("distancia", 0.0)
            ),
            inclinacao_acumulada=(
                self.inclinacao_acumulada
                + max(0.0, atributos_aresta.get("inclinacao", 0.0))
            ),
            sombra_acumulada=(
                self.sombra_acumulada
                + atributos_aresta.get("sombra", 0.0)
                * atributos_aresta.get("distancia", 0.0)
            ),
            distancia_total=(
                self.distancia_total + atributos_aresta.get("distancia", 0.0)
            ),
            caminho=self.caminho + (no_vizinho,),
            perfil=self.perfil,
        )

    # Representação
    def resumo(self) -> dict:
        return {
            "no_atual": self.no_atual,
            "custo_g": round(self.custo_g, 4),
            "distancia_m": round(self.distancia_total, 1),
            "poluicao_acum": round(self.poluicao_acumulada, 2),
            "ruido_acum": round(self.ruido_acumulado, 2),
            "inclinacao_total_m": round(self.inclinacao_acumulada, 1),
            "sombra_acum": round(self.sombra_acumulada, 2),
            "nos_no_caminho": len(self.caminho),
            "perfil": self.perfil.nome,
        }

    def __repr__(self) -> str:
        return (
            f"Estado(no={self.no_atual}, g={self.custo_g:.2f}, "
            f"dist={self.distancia_total:.0f}m, "
            f"nos={len(self.caminho)}, perfil={self.perfil.nome})"
        )
