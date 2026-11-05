"""
Q10 - Planejamento de rotas para entregas urbanas (Lista 2, AB2, IA PPGI 2026.2).

Implementa, usando apenas a biblioteca padrão do Python:

  * Busca em largura (BFS)                  - busca não informada
  * Busca em profundidade (DFS)             - busca não informada
  * Busca de custo uniforme (UCS)           - busca não informada
  * A* com a heurística fornecida no enunciado - busca informada
  * Versão modificada: visitar D e F antes de chegar a I, em qualquer ordem

Uso:
    python3 busca_rotas.py
"""

from __future__ import annotations

import heapq
import itertools
from collections import deque
from dataclasses import dataclass, field
from math import inf
from typing import Callable, Hashable, Optional

# ---------------------------------------------------------------------------
# Dados do problema (enunciado da questão 10)
# ---------------------------------------------------------------------------

# Grafo não direcionado: (origem, destino, minutos de deslocamento)
TRECHOS: list[tuple[str, str, int]] = [
    ("A", "B", 4), ("B", "C", 5), ("C", "F", 2), ("D", "G", 6), ("E", "H", 5), ("G", "H", 3),
    ("A", "D", 3), ("B", "E", 2), ("D", "E", 4), ("E", "F", 3), ("F", "I", 4), ("H", "I", 2),
]

# Heurística do enunciado: h(n) = estimativa de tempo até I
HEURISTICA: dict[str, int] = {
    "A": 10, "B": 8, "C": 6, "D": 9, "E": 6, "F": 4, "G": 5, "H": 2, "I": 0,
}

INICIO = "A"                       # centro de distribuição
DESTINO = "I"                      # destino da entrega
OBRIGATORIOS = frozenset({"D", "F"})  # usados na versão modificada


def _construir_vizinhos(trechos: list[tuple[str, str, int]]) -> dict[str, dict[str, int]]:
    """Lista de adjacência: VIZINHOS[u][v] = custo do trecho u-v (nos dois sentidos)."""
    viz: dict[str, dict[str, int]] = {}
    for u, v, c in trechos:
        viz.setdefault(u, {})[v] = c
        viz.setdefault(v, {})[u] = c
    return viz


VIZINHOS = _construir_vizinhos(TRECHOS)


def custo_do_caminho(rota: list[str]) -> int:
    """Soma dos trechos de uma rota de nós. Levanta KeyError se algum trecho não existir."""
    return sum(VIZINHOS[a][b] for a, b in zip(rota, rota[1:]))


# ---------------------------------------------------------------------------
# Formulação do problema
# ---------------------------------------------------------------------------

Estado = Hashable
Acao = tuple[str, Estado, int]  # (rótulo da ação, estado seguinte, custo do trecho)


@dataclass(frozen=True)
class Problema:
    """Formulação genérica de um problema de busca."""

    nome: str
    estado_inicial: Estado
    acoes: Callable[[Estado], list[Acao]]
    teste_objetivo: Callable[[Estado], bool]
    no: Callable[[Estado], str]                 # nó do mapa que o estado representa
    rotulo: Callable[[Estado], str] = str       # texto mostrado nas tabelas de expansão


def problema_original(inicio: str = INICIO) -> Problema:
    """Problema do enunciado: ir de `inicio` até I, minimizando o tempo.

    Estados: nós do grafo. Ações: ir para um vizinho. Custo: minutos do trecho.
    """

    def acoes(no: str) -> list[Acao]:
        return [(f"ir para {v}", v, c) for v, c in sorted(VIZINHOS[no].items())]

    return Problema(
        nome=f"Rota de {inicio} até {DESTINO}",
        estado_inicial=inicio,
        acoes=acoes,
        teste_objetivo=lambda no: no == DESTINO,
        no=lambda no: no,
    )


def problema_com_obrigatorios(obrigatorios: frozenset[str] = OBRIGATORIOS) -> Problema:
    """Versão modificada: visitar os obrigatórios (D e F) antes de chegar a I.

    Estado: (nó atual, conjunto dos obrigatórios já visitados).
    Estado inicial: (A, {}). Objetivo: estar em I com todos os obrigatórios visitados.
    """

    def acoes(estado: tuple[str, frozenset[str]]) -> list[Acao]:
        no, visitados = estado
        return [
            (f"ir para {v}", (v, visitados | ({v} & obrigatorios)), c)
            for v, c in sorted(VIZINHOS[no].items())
        ]

    return Problema(
        nome=f"Rota de {INICIO} até {DESTINO} passando por {' e '.join(sorted(obrigatorios))}",
        estado_inicial=(INICIO, frozenset({INICIO}) & obrigatorios),
        acoes=acoes,
        teste_objetivo=lambda e: e[0] == DESTINO and obrigatorios <= e[1],
        no=lambda e: e[0],
        rotulo=lambda e: f"{e[0]}{{{','.join(sorted(e[1]))}}}",
    )


# ---------------------------------------------------------------------------
# Resultados
# ---------------------------------------------------------------------------


@dataclass
class Expansao:
    """Um nó expandido, com os valores relevantes para o algoritmo."""

    rotulo: str
    g: Optional[int] = None   # custo acumulado até o nó (UCS e A*)
    h: Optional[int] = None   # heurística do nó (A*)
    f: Optional[int] = None   # g + h (A*)


@dataclass
class Resultado:
    algoritmo: str
    encontrou: bool
    rota: list[str] = field(default_factory=list)
    custo: Optional[int] = None
    expansoes: list[Expansao] = field(default_factory=list)  # na ordem em que foram expandidos


def _resultado(algoritmo: str, problema: Problema, caminho: list[Estado],
               expansoes: list[Expansao]) -> Resultado:
    rota = [problema.no(e) for e in caminho]
    return Resultado(algoritmo, True, rota, custo_do_caminho(rota), expansoes)


# ---------------------------------------------------------------------------
# Algoritmos de busca
#
# Convenções comuns:
#   * O teste de objetivo é feito quando o nó sai da fronteira (é expandido).
#   * Vizinhos são considerados em ordem alfabética.
#   * Há um conjunto de nós já explorados, para não repetir estados.
#   * "Nós expandidos" não inclui o nó objetivo.
# ---------------------------------------------------------------------------


def busca_em_largura(p: Problema) -> Resultado:
    """BFS: expande por níveis (menor número de trechos). Não considera custos."""
    fronteira: deque[list[Estado]] = deque([[p.estado_inicial]])
    alcancados: set[Estado] = {p.estado_inicial}
    expansoes: list[Expansao] = []

    while fronteira:
        caminho = fronteira.popleft()
        estado = caminho[-1]
        if p.teste_objetivo(estado):
            return _resultado("BFS", p, caminho, expansoes)
        expansoes.append(Expansao(p.rotulo(estado)))
        for _, prox, _c in p.acoes(estado):
            if prox not in alcancados:
                alcancados.add(prox)
                fronteira.append(caminho + [prox])

    return Resultado("BFS", False, expansoes=expansoes)


def busca_em_profundidade(p: Problema) -> Resultado:
    """DFS: segue sempre um caminho até o fim antes de voltar. Não garante o menor custo."""
    pilha: list[list[Estado]] = [[p.estado_inicial]]
    explorados: set[Estado] = set()
    expansoes: list[Expansao] = []

    while pilha:
        caminho = pilha.pop()
        estado = caminho[-1]
        if estado in explorados:
            continue
        if p.teste_objetivo(estado):
            return _resultado("DFS", p, caminho, expansoes)
        explorados.add(estado)
        expansoes.append(Expansao(p.rotulo(estado)))
        # Empilha em ordem inversa para que o vizinho alfabeticamente menor saia primeiro.
        for _, prox, _c in reversed(p.acoes(estado)):
            if prox not in explorados:
                pilha.append(caminho + [prox])

    return Resultado("DFS", False, expansoes=expansoes)


def busca_custo_uniforme(p: Problema) -> Resultado:
    """UCS: sempre expande o nó com menor custo acumulado g(n). Ótima para custos positivos.

    Empates de custo são resolvidos pela ordem de inserção na fila.
    """
    contador = itertools.count()
    fila: list[tuple[int, int, Estado, list[Estado]]] = [
        (0, next(contador), p.estado_inicial, [p.estado_inicial])
    ]
    melhor_g: dict[Estado, int] = {p.estado_inicial: 0}
    explorados: set[Estado] = set()
    expansoes: list[Expansao] = []

    while fila:
        g, _, estado, caminho = heapq.heappop(fila)
        if estado in explorados:
            continue
        if p.teste_objetivo(estado):
            return _resultado("UCS", p, caminho, expansoes)
        explorados.add(estado)
        expansoes.append(Expansao(p.rotulo(estado), g=g))
        for _, prox, c in p.acoes(estado):
            ng = g + c
            if prox not in explorados and ng < melhor_g.get(prox, inf):
                melhor_g[prox] = ng
                heapq.heappush(fila, (ng, next(contador), prox, caminho + [prox]))

    return Resultado("UCS", False, expansoes=expansoes)


def busca_a_estrela(p: Problema, heuristica: Callable[[Estado], int]) -> Resultado:
    """A*: expande pelo menor f(n) = g(n) + h(n). Ótima se h for admissível e consistente."""
    contador = itertools.count()
    h0 = heuristica(p.estado_inicial)
    # Entrada da fila: (f, g, desempate, estado, caminho). Desempate por g: menor g primeiro.
    fila: list[tuple[int, int, int, Estado, list[Estado]]] = [
        (h0, 0, next(contador), p.estado_inicial, [p.estado_inicial])
    ]
    melhor_g: dict[Estado, int] = {p.estado_inicial: 0}
    explorados: set[Estado] = set()
    expansoes: list[Expansao] = []

    while fila:
        f, g, _, estado, caminho = heapq.heappop(fila)
        if estado in explorados:
            continue
        if p.teste_objetivo(estado):
            return _resultado("A*", p, caminho, expansoes)
        explorados.add(estado)
        h = heuristica(estado)
        expansoes.append(Expansao(p.rotulo(estado), g=g, h=h, f=f))
        for _, prox, c in p.acoes(estado):
            ng = g + c
            if prox not in explorados and ng < melhor_g.get(prox, inf):
                melhor_g[prox] = ng
                nf = ng + heuristica(prox)
                heapq.heappush(fila, (nf, ng, next(contador), prox, caminho + [prox]))

    return Resultado("A*", False, expansoes=expansoes)


def heuristica_do_no(p: Problema) -> Callable[[Estado], int]:
    """Usa a heurística do enunciado, indexada pelo nó que o estado representa."""
    return lambda estado: HEURISTICA[p.no(estado)]


# ---------------------------------------------------------------------------
# Verificação da heurística
# ---------------------------------------------------------------------------


def verificar_heuristica() -> tuple[dict[str, int], bool, bool]:
    """Retorna (custo real até I de cada nó, admissível?, consistente?).

    Admissível: h(n) <= custo real de n até I, para todo n.
    Consistente: h(u) <= c(u, v) + h(v), para todo trecho u-v.
    """
    custos_reais = {no: busca_custo_uniforme(problema_original(no)).custo for no in VIZINHOS}
    admissivel = all(HEURISTICA[no] <= custos_reais[no] for no in VIZINHOS)
    consistente = all(
        HEURISTICA[u] <= c + HEURISTICA[v]
        for u in VIZINHOS
        for v, c in VIZINHOS[u].items()
    )
    return custos_reais, admissivel, consistente


# ---------------------------------------------------------------------------
# Apresentação
# ---------------------------------------------------------------------------


def imprimir_formulacao() -> None:
    print("1. Formulação do problema")
    print("   Estados ......... nós do mapa: A, B, C, D, E, F, G, H, I")
    print("   Estado inicial .. A (centro de distribuição)")
    print("   Ações ........... ir para um vizinho ligado ao nó atual por um trecho")
    print("   Transição ....... resultado(n, ir para v) = v")
    print("   Teste objetivo .. estado atual é I")
    print("   Custo ........... minutos do trecho; custo da rota = soma dos trechos")


def imprimir_resultado(r: Resultado) -> None:
    print(f"\n--- {r.algoritmo} ---")
    if not r.encontrou:
        print("Nenhuma rota encontrada.")
        return
    ordem = " -> ".join(e.rotulo for e in r.expansoes)
    print(f"Ordem de expansão ({len(r.expansoes)} nós): {ordem}")
    print(f"Rota encontrada:   {' -> '.join(r.rota)}")
    print(f"Custo total:       {r.custo} min")
    if r.expansoes and r.expansoes[0].h is not None:
        print(f"\n  {'Nó':<12}{'g(n)':>6}{'h(n)':>6}{'f(n)':>6}")
        for e in r.expansoes:
            print(f"  {e.rotulo:<12}{e.g:>6}{e.h:>6}{e.f:>6}")
        print(f"  {'(objetivo)':<12}{r.custo:>6}{0:>6}{r.custo:>6}")
    elif r.expansoes and r.expansoes[0].g is not None:
        print("\n  Nó           g(n) (custo acumulado)")
        for e in r.expansoes:
            print(f"  {e.rotulo:<12}{e.g:>6}")


def imprimir_comparativo(resultados: dict[str, Resultado], otimo: int) -> None:
    print(f"\n{'Algoritmo':<11}{'Rota':<26}{'Custo':>6}{'Expandidos':>12}  Custo ótimo?")
    for nome, r in resultados.items():
        rota = "-".join(r.rota)
        otimo_txt = "sim" if r.custo == otimo else "não"
        print(f"{nome:<11}{rota:<26}{r.custo:>6}{len(r.expansoes):>12}  {otimo_txt}")


def main() -> None:
    print("=" * 72)
    print("Q10 - Planejamento de rotas para entregas urbanas")
    print("=" * 72)
    imprimir_formulacao()

    # ---- Problema original -------------------------------------------------
    p = problema_original()
    h = heuristica_do_no(p)

    print("\n2. Busca não informada e busca informada (problema original)")
    resultados = {
        "BFS": busca_em_largura(p),
        "DFS": busca_em_profundidade(p),
        "UCS": busca_custo_uniforme(p),
        "A*": busca_a_estrela(p, h),
    }
    for r in resultados.values():
        imprimir_resultado(r)

    otimo = resultados["UCS"].custo
    print(f"\n3. Comparação (custo ótimo nesta instância: {otimo} min)")
    imprimir_comparativo(resultados, otimo)

    print("\n4. Verificação da heurística")
    custos_reais, admissivel, consistente = verificar_heuristica()
    print(f"   {'Nó':<6}{'h(n)':>6}{'custo real até I':>18}{'h <= real?':>12}")
    for no in sorted(VIZINHOS):
        print(f"   {no:<6}{HEURISTICA[no]:>6}{custos_reais[no]:>18}"
              f"{'sim' if HEURISTICA[no] <= custos_reais[no] else 'não':>12}")
    print(f"   Admissível: {'sim' if admissivel else 'não'} | "
          f"Consistente: {'sim' if consistente else 'não'}")

    # ---- Versão modificada -------------------------------------------------
    pm = problema_com_obrigatorios()
    print(f"\n5. Versão modificada: {pm.nome}")
    print("   Estado = (nó atual, obrigatórios já visitados), ex.: E{D} = em E, já passou por D")
    r_ucs = busca_custo_uniforme(pm)
    r_astar = busca_a_estrela(pm, heuristica_do_no(pm))
    imprimir_resultado(r_ucs)
    imprimir_resultado(r_astar)
    print(f"\nRota modificada: {' -> '.join(r_ucs.rota)} | custo {r_ucs.custo} min")


if __name__ == "__main__":
    main()
