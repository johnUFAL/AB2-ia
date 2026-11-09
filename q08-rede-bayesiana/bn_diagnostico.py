"""
Q8 - Sistema de diagnóstico médico com Rede Bayesiana (Lista 2, AB2, IA PPGI 2026.2).

Modela relações de causa e efeito entre a doença e os sintomas, faz inferência diagnóstica
com evidências incompletas e atualiza as probabilidades conforme novas evidências chegam.

Doenças e sintomas são os mesmos da Q7 (sistema CBR), para comparar os resultados.
Os dados são PROBABILIDADES ILUSTRATIVAS, definidas pelo autor com justificativa no README.
Este é um protótipo acadêmico e NÃO substitui avaliação médica.

Ferramenta: pgmpy (inferência por eliminação de variáveis).

Uso:
    python3 bn_diagnostico.py      # mostra a rede, os experimentos e salva o modelo em .bif
"""

from __future__ import annotations

from pathlib import Path

from pgmpy.factors.discrete import TabularCPD
from pgmpy.inference import VariableElimination
from pgmpy.models import DiscreteBayesianNetwork
from pgmpy.readwrite import BIFReader, BIFWriter

PASTA = Path(__file__).resolve().parent
CAMINHO_BIF = PASTA / "data" / "diagnostico.bif"

# ---------------------------------------------------------------------------
# Estados das variáveis
# ---------------------------------------------------------------------------

FAIXAS = ["Jovem", "Adulto", "Idoso"]
DOENCAS = ["Gripe", "Dengue", "Pneumonia", "Enxaqueca", "Gastrite"]
DURACOES = ["ate_3_dias", "4_a_7_dias", "mais_7_dias"]
SIM_NAO = ["Nao", "Sim"]

# Sintomas da Q7 (mesmos nomes, sem acento e em CamelCase para as variáveis da rede).
SINTOMAS = [
    "Febre", "Tosse", "DorDeCabeca", "DorMuscular", "DorDeGarganta", "Coriza",
    "Nausea", "DorAbdominal", "Azia", "DorAtrasDosOlhos", "ManchasNaPele",
    "FaltaDeAr", "DorNoPeito", "SensibilidadeLuz",
]

# ---------------------------------------------------------------------------
# Probabilidades
# ---------------------------------------------------------------------------

# P(Faixa etária): distribuição da população atendida (premissa do modelo).
P_FAIXA = {"Jovem": 0.30, "Adulto": 0.45, "Idoso": 0.25}

# P(Doença | Faixa etária). Cada linha (faixa) soma 1.
P_DOENCA_DADA_FAIXA = {
    #          Gripe  Dengue Pneumonia Enxaqueca Gastrite
    "Jovem":  [0.30,  0.20,  0.05,     0.25,     0.20],
    "Adulto": [0.25,  0.20,  0.10,     0.25,     0.20],
    "Idoso":  [0.20,  0.10,  0.30,     0.10,     0.30],
}

# P(Duração | Doença). Cada coluna (doença) soma 1.
P_DURACAO_DADA_DOENCA = {
    #              Gripe  Dengue Pneumonia Enxaqueca Gastrite
    "ate_3_dias":  [0.70,  0.60,  0.10,     0.60,     0.05],
    "4_a_7_dias":  [0.25,  0.35,  0.35,     0.20,     0.25],
    "mais_7_dias": [0.05,  0.05,  0.55,     0.20,     0.70],
}

# P(Sintoma = Sim | Doença), na ordem de DOENCAS.
P_SINTOMA_DADA_DOENCA = {
    #                   Gripe  Dengue Pneumonia Enxaqueca Gastrite
    "Febre":            [0.85,  0.90,  0.85,     0.10,     0.10],
    "Tosse":            [0.80,  0.15,  0.90,     0.10,     0.10],
    "DorDeCabeca":      [0.60,  0.60,  0.30,     0.95,     0.25],
    "DorMuscular":      [0.70,  0.75,  0.40,     0.20,     0.05],
    "DorDeGarganta":    [0.60,  0.15,  0.20,     0.05,     0.05],
    "Coriza":           [0.75,  0.05,  0.10,     0.05,     0.02],
    "Nausea":           [0.15,  0.45,  0.15,     0.60,     0.55],
    "DorAbdominal":     [0.05,  0.25,  0.05,     0.05,     0.90],
    "Azia":             [0.02,  0.02,  0.02,     0.05,     0.85],
    "DorAtrasDosOlhos": [0.10,  0.70,  0.05,     0.35,     0.02],
    "ManchasNaPele":    [0.02,  0.40,  0.02,     0.02,     0.02],
    "FaltaDeAr":        [0.05,  0.05,  0.80,     0.03,     0.02],
    "DorNoPeito":       [0.05,  0.05,  0.60,     0.05,     0.15],
    "SensibilidadeLuz": [0.05,  0.05,  0.05,     0.80,     0.05],
}

# Arestas: Faixa -> Doença -> Duração, e Doença -> cada sintoma.
ARESTAS = (
    [("Faixa", "Doenca"), ("Doenca", "Duracao")]
    + [("Doenca", s) for s in SINTOMAS]
)


# ---------------------------------------------------------------------------
# Construção do modelo
# ---------------------------------------------------------------------------


def construir_modelo() -> DiscreteBayesianNetwork:
    modelo = DiscreteBayesianNetwork(ARESTAS)

    nomes = {"Faixa": FAIXAS, "Doenca": DOENCAS, "Duracao": DURACOES}
    nomes.update({s: SIM_NAO for s in SINTOMAS})

    # Faixa etária (raiz). Valores: uma coluna só.
    cpd_faixa = TabularCPD(
        "Faixa", len(FAIXAS),
        [[P_FAIXA[f]] for f in FAIXAS],
        state_names={"Faixa": FAIXAS},
    )

    # Doença | Faixa: linhas = doenças, colunas = faixas.
    cpd_doenca = TabularCPD(
        "Doenca", len(DOENCAS),
        [[P_DOENCA_DADA_FAIXA[f][d] for f in FAIXAS] for d in range(len(DOENCAS))],
        evidence=["Faixa"], evidence_card=[len(FAIXAS)],
        state_names={"Doenca": DOENCAS, "Faixa": FAIXAS},
    )

    # Duração | Doença: linhas = durações, colunas = doenças.
    cpd_duracao = TabularCPD(
        "Duracao", len(DURACOES),
        [P_DURACAO_DADA_DOENCA[dur] for dur in DURACOES],
        evidence=["Doenca"], evidence_card=[len(DOENCAS)],
        state_names={"Duracao": DURACOES, "Doenca": DOENCAS},
    )

    cpds = [cpd_faixa, cpd_doenca, cpd_duracao]

    # Sintoma | Doença: linha 0 = Não, linha 1 = Sim.
    for s in SINTOMAS:
        p_sim = P_SINTOMA_DADA_DOENCA[s]
        cpds.append(TabularCPD(
            s, 2,
            [[1 - p for p in p_sim], p_sim],
            evidence=["Doenca"], evidence_card=[len(DOENCAS)],
            state_names={s: SIM_NAO, "Doenca": DOENCAS},
        ))

    modelo.add_cpds(*cpds)
    if not modelo.check_model():
        raise ValueError("Modelo inconsistente: verifique as tabelas de probabilidade.")
    return modelo


def salvar_bif(modelo: DiscreteBayesianNetwork, caminho: Path = CAMINHO_BIF) -> None:
    BIFWriter(modelo).write(str(caminho))


def carregar_bif(caminho: Path = CAMINHO_BIF) -> DiscreteBayesianNetwork:
    return BIFReader(str(caminho)).get_model()


# ---------------------------------------------------------------------------
# Inferência
# ---------------------------------------------------------------------------


def diagnostico(modelo: DiscreteBayesianNetwork, evidencias: dict[str, str]) -> dict[str, float]:
    """P(Doença | evidências). As evidências podem ser parciais (incompletas)."""
    resultado = VariableElimination(modelo).query(["Doenca"], evidence=evidencias or None)
    return {DOENCAS[i]: float(p) for i, p in enumerate(resultado.values)}


def diagnostico_direto(evidencias: dict[str, str]) -> dict[str, float]:
    """Mesma conta feita à mão, sem pgmpy: usada nos testes para conferir a inferência.

    P(D | e) ∝ [Σ_F P(F) P(D|F)] · [Σ_Dur P(Dur|D)] · Π P(s | D) para cada sintoma observado.
    Faixa e duração entram só se estiverem na evidência.
    """
    pesos = {}
    for i, d in enumerate(DOENCAS):
        if "Faixa" in evidencias:
            fator = P_DOENCA_DADA_FAIXA[evidencias["Faixa"]][i]
        else:
            fator = sum(P_FAIXA[f] * P_DOENCA_DADA_FAIXA[f][i] for f in FAIXAS)
        if "Duracao" in evidencias:
            fator *= P_DURACAO_DADA_DOENCA[evidencias["Duracao"]][i]
        for s in SINTOMAS:
            if s in evidencias:
                p = P_SINTOMA_DADA_DOENCA[s][i]
                fator *= p if evidencias[s] == "Sim" else 1 - p
        pesos[d] = fator
    total = sum(pesos.values())
    return {d: v / total for d, v in pesos.items()}


# ---------------------------------------------------------------------------
# Apresentação e experimentos
# ---------------------------------------------------------------------------


def imprimir_distribuicao(titulo: str, dist: dict[str, float]) -> None:
    print(f"  {titulo}")
    for d in sorted(dist, key=lambda k: -dist[k]):
        barra = "#" * round(dist[d] * 40)
        print(f"    {d:<11}{dist[d]:>7.1%}  {barra}")


def imprimir_evidencias(evidencias: dict[str, str]) -> str:
    return ", ".join(f"{k}={v}" for k, v in evidencias.items()) if evidencias else "(nenhuma)"


def experimentos(modelo: DiscreteBayesianNetwork) -> None:
    print("=" * 72)
    print("EXPERIMENTO 1: diagnóstico a partir de sintomas observados (enunciado)")
    print("=" * 72)
    ev = {"Febre": "Sim", "Tosse": "Sim", "DorMuscular": "Sim"}
    print(f"  Evidências: {imprimir_evidencias(ev)}")
    imprimir_distribuicao("Priori (sem evidências):", diagnostico(modelo, {}))
    imprimir_distribuicao("Posteriori (com as evidências):", diagnostico(modelo, ev))

    print("\n" + "=" * 72)
    print("EXPERIMENTO 2: atualização do diagnóstico conforme sintomas são incluídos")
    print("=" * 72)
    sequencia = ["Febre", "Tosse", "DorMuscular", "FaltaDeAr", "DorNoPeito"]
    acumulado: dict[str, str] = {}
    cabecalho = f"  {'Evidência adicionada':<22}" + "".join(f"{d[:9]:>11}" for d in DOENCAS)
    print(cabecalho)
    dist = diagnostico(modelo, {})
    print(f"  {'(priori)':<22}" + "".join(f"{dist[d]:>10.1%} " for d in DOENCAS))
    for s in sequencia:
        acumulado[s] = "Sim"
        dist = diagnostico(modelo, acumulado)
        print(f"  {s + ' = Sim':<22}" + "".join(f"{dist[d]:>10.1%} " for d in DOENCAS))

    print("\n" + "=" * 72)
    print("EXPERIMENTO 3: comparação entre conjuntos de evidências diferentes")
    print("=" * 72)
    conjuntos = {
        "Dengue": {"Febre": "Sim", "DorAtrasDosOlhos": "Sim", "ManchasNaPele": "Sim", "DorMuscular": "Sim"},
        "Enxaqueca": {"DorDeCabeca": "Sim", "SensibilidadeLuz": "Sim", "Nausea": "Sim"},
        "Gastrite": {"DorAbdominal": "Sim", "Azia": "Sim", "Nausea": "Sim"},
    }
    for nome, ev in conjuntos.items():
        imprimir_distribuicao(f"Evidências ({nome}): {imprimir_evidencias(ev)}", diagnostico(modelo, ev))
        print()

    print("=" * 72)
    print("EXPERIMENTO 4: efeito da faixa etária com os mesmos sintomas")
    print("=" * 72)
    base = {"Febre": "Sim", "Tosse": "Sim", "DorMuscular": "Sim"}
    for faixa in FAIXAS:
        dist = diagnostico(modelo, {**base, "Faixa": faixa})
        imprimir_distribuicao(f"Faixa = {faixa} + {imprimir_evidencias(base)}", dist)
        print()


def desenhar_rede(caminho: Path) -> None:
    """Desenho do grafo da rede: Faixa -> Doença -> (Duração, sintomas)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import networkx as nx

    grafo = nx.DiGraph(ARESTAS)
    pos = {"Faixa": (0, 3), "Doenca": (0, 2), "Duracao": (-7, 2)}
    for i, s in enumerate(SINTOMAS):
        pos[s] = (-6.5 + i * 1.0, 0)

    cores = {"Faixa": "#cfe8ff", "Doenca": "#ffd6a5", "Duracao": "#d8f5d0"}
    cor_no = [cores.get(n, "#f2f2f2") for n in grafo.nodes()]

    fig, ax = plt.subplots(figsize=(15, 5.5))
    nx.draw_networkx_edges(grafo, pos, ax=ax, arrows=True, arrowsize=12, edge_color="#777")
    nx.draw_networkx_nodes(grafo, pos, ax=ax, node_color=cor_no, node_size=1400)
    nx.draw_networkx_labels(grafo, pos, ax=ax, font_size=7)
    ax.set_title("Rede Bayesiana do diagnóstico (variáveis-doença em laranja, causas em azul)")
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(caminho, dpi=150)
    plt.close(fig)


def main() -> None:
    modelo = construir_modelo()
    salvar_bif(modelo)
    desenhar_rede(PASTA / "figuras" / "rede_bayesiana.png")
    print(f"Rede: {len(modelo.nodes())} variáveis, {len(modelo.edges())} arestas.")
    print(f"Modelo salvo em {CAMINHO_BIF}")
    print(f"Grafo salvo em {PASTA / 'figuras' / 'rede_bayesiana.png'}\n")
    experimentos(modelo)


if __name__ == "__main__":
    main()
