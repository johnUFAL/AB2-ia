"""
Q2 - K-vizinhos mais próximos (KNN) sobre a base de crédito da Lista 1 (30 instâncias).

Implementa, só com a biblioteca padrão:
  * distância de Hamming (número de atributos diferentes), adequada a atributos categóricos
  * classificação por voto majoritário entre os k vizinhos mais próximos
  * validação leave-one-out para vários valores de k

Uso:
    python3 knn.py
"""

from __future__ import annotations

import csv
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

CAMINHO_PADRAO = Path(__file__).resolve().parent / "data" / "credito_ampliado.csv"
ATRIBUTOS = ["Historia", "Divida", "Garantia", "Renda", "Emprego", "Idade"]
CLASSE = "Decision"

Valores = tuple[str, ...]


@dataclass(frozen=True)
class Instancia:
    nome: str        # E1 ... E30, como na tabela da Lista 1
    valores: Valores
    classe: str


@dataclass(frozen=True)
class Vizinho:
    distancia: int
    instancia: Instancia


@dataclass(frozen=True)
class Classificacao:
    classe: str
    vizinhos: list[Vizinho]    # os k mais próximos, do mais próximo ao mais distante
    votos: Counter


# ---------------------------------------------------------------------------
# Dados
# ---------------------------------------------------------------------------


def carregar_base(caminho: Path = CAMINHO_PADRAO) -> list[Instancia]:
    """Lê o CSV da Lista 1. A linha n do arquivo (sem contar o cabeçalho) é o exemplo E{n}."""
    with open(caminho, newline="", encoding="utf-8") as f:
        return [
            Instancia(
                nome=f"E{i}",
                valores=tuple(linha[a] for a in ATRIBUTOS),
                classe=linha[CLASSE],
            )
            for i, linha in enumerate(csv.DictReader(f), start=1)
        ]


# ---------------------------------------------------------------------------
# KNN
# ---------------------------------------------------------------------------


def distancia_hamming(a: Valores, b: Valores) -> int:
    """Número de atributos em que os dois exemplos têm valores diferentes (0 a 6).

    Para atributos categóricos não faz sentido somar diferenças numéricas, então
    a distância euclidiana não se aplica diretamente. A de Hamming conta mismatches.
    """
    return sum(x != y for x, y in zip(a, b))


def vizinhos_mais_proximos(consulta: Valores, base: list[Instancia]) -> list[Vizinho]:
    """Todos os exemplos da base, ordenados pela distância à consulta.

    A ordenação é estável: em caso de empate de distância, vale a ordem da base (E1 antes de E2...).
    """
    vizinhos = [Vizinho(distancia_hamming(consulta, inst.valores), inst) for inst in base]
    return sorted(vizinhos, key=lambda v: v.distancia)


def classificar(consulta: Valores, base: list[Instancia], k: int) -> Classificacao:
    """Classifica por voto majoritário entre os k vizinhos mais próximos.

    Empate de votos: fica a classe empatada que aparece primeiro na lista de vizinhos,
    ou seja, a do vizinho mais próximo entre as classes empatadas.
    """
    if not 1 <= k <= len(base):
        raise ValueError(f"k deve estar entre 1 e {len(base)}, recebeu {k}")

    proximos = vizinhos_mais_proximos(consulta, base)[:k]
    votos = Counter(v.instancia.classe for v in proximos)
    maior = max(votos.values())
    empatadas = {c for c, n in votos.items() if n == maior}
    classe = next(v.instancia.classe for v in proximos if v.instancia.classe in empatadas)
    return Classificacao(classe, proximos, votos)


def leave_one_out(base: list[Instancia], k: int) -> tuple[int, list[tuple[str, str, str]]]:
    """Para cada exemplo, treina com os outros 29 e prevê a classe dele.

    Retorna (acertos, [(nome, classe real, classe prevista), ...]).
    """
    acertos = 0
    detalhes = []
    for i, inst in enumerate(base):
        resto = base[:i] + base[i + 1:]
        prevista = classificar(inst.valores, resto, k).classe
        detalhes.append((inst.nome, inst.classe, prevista))
        acertos += prevista == inst.classe
    return acertos, detalhes


# ---------------------------------------------------------------------------
# Apresentação
# ---------------------------------------------------------------------------

CONSULTA_EXEMPLO = {
    "Historia": "Boa",
    "Divida": "Baixa",
    "Garantia": "Nenhuma",
    "Renda": "15-35k",
    "Emprego": "Estavel",
    "Idade": "Adulto",
}


def imprimir_resumo(base: list[Instancia]) -> None:
    contagem = Counter(i.classe for i in base)
    print(f"Base: {len(base)} instâncias, {len(ATRIBUTOS)} atributos categóricos")
    print("Distribuição: " + ", ".join(f"{c} = {n}" for c, n in sorted(contagem.items())))


def imprimir_consulta(consulta: Valores, base: list[Instancia], k: int) -> None:
    print("\nConsulta: " + ", ".join(f"{a}={v}" for a, v in zip(ATRIBUTOS, consulta)))
    print(f"\nDistância de Hamming até cada exemplo (k = {k}):")
    print(f"  {'Exemplo':<8}{'Dist.':>6}  {'Classe':<10}  Valores")
    resultado = classificar(consulta, base, k)
    proximos = {v.instancia.nome for v in resultado.vizinhos}
    for v in vizinhos_mais_proximos(consulta, base):
        marca = "  <- entre os k" if v.instancia.nome in proximos else ""
        print(f"  {v.instancia.nome:<8}{v.distancia:>6}  {v.instancia.classe:<10}  "
              f"{' | '.join(v.instancia.valores)}{marca}")

    print(f"\nVotos entre os {k} vizinhos: " +
          ", ".join(f"{c} = {n}" for c, n in resultado.votos.most_common()))
    print(f"Classe prevista: {resultado.classe}")


def imprimir_loo(base: list[Instancia]) -> None:
    print("\nValidação leave-one-out (LOO) para diferentes k:")
    print(f"  {'k':>3}  {'Acertos':>8}  {'Acurácia':>9}")
    for k in (1, 3, 5, 7, 9):
        acertos, _ = leave_one_out(base, k)
        print(f"  {k:>3}  {acertos:>4}/{len(base):<3}  {100 * acertos / len(base):>8.1f}%")


def main() -> None:
    base = carregar_base()
    imprimir_resumo(base)

    print("\n--- Distância de Hamming entre dois exemplos ---")
    a, b = base[0], base[6]  # E1 e E7
    diferentes = [ATRIBUTOS[i] for i, (x, y) in enumerate(zip(a.valores, b.valores)) if x != y]
    print(f"{a.nome} vs {b.nome}: diferem em {diferentes} -> distância = "
          f"{distancia_hamming(a.valores, b.valores)}")

    print("\n--- Classificação de um novo cliente (k = 5) ---")
    consulta = tuple(CONSULTA_EXEMPLO[a] for a in ATRIBUTOS)
    imprimir_consulta(consulta, base, k=5)

    print("\n--- Validação ---")
    imprimir_loo(base)


if __name__ == "__main__":
    main()
