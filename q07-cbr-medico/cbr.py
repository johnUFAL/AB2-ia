"""
Q7 - Sistema de Apoio ao Diagnóstico Médico Baseado em Casos (CBR).

Ciclo de raciocínio baseado em casos:
  Retrieve (recuperação) - busca os casos mais semelhantes ao paciente
  Reuse (reutilização)   - propõe diagnóstico e tratamento a partir deles
  Revise (revisão)       - o profissional confirma ou corrige o diagnóstico
  Retain (retenção)      - o caso confirmado é gravado na base

Os casos são FICTÍCIOS. Este é um protótipo acadêmico e NÃO substitui avaliação médica.

Uso:
    python3 cbr.py               # demonstração com consultas de exemplo (não grava nada)
    python3 cbr.py --interativo  # consulta com perguntas; pode gravar o caso confirmado
"""

from __future__ import annotations

import csv
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

CAMINHO_PADRAO = Path(__file__).resolve().parent / "data" / "casos_medicos.csv"

SINTOMAS = [
    "febre", "tosse", "dor_de_cabeca", "dor_muscular", "dor_de_garganta", "coriza",
    "nausea", "dor_abdominal", "azia", "dor_atras_dos_olhos", "manchas_na_pele",
    "falta_de_ar", "dor_no_peito", "sensibilidade_luz",
]
# A ordem importa: a similaridade ordinal usa a distância entre posições.
FAIXAS_ETARIAS = ["Jovem", "Adulto", "Idoso"]
DURACOES = ["ate_3_dias", "4_a_7_dias", "mais_7_dias"]

# Pesos dos atributos na similaridade global (somam 1).
PESOS = {"sintomas": 0.6, "faixa_etaria": 0.2, "duracao": 0.2}
K_PADRAO = 5


# ---------------------------------------------------------------------------
# Representação dos casos
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Descricao:
    """Atributos observados do paciente. A consulta e cada caso da base usam esta forma."""

    faixa_etaria: str
    duracao: str
    sintomas: frozenset[str]


@dataclass(frozen=True)
class Caso:
    id: str
    descricao: Descricao
    diagnostico: str
    tratamento: str


@dataclass(frozen=True)
class Recuperado:
    caso: Caso
    score: float                 # similaridade global, entre 0 e 1
    detalhes: dict[str, float]   # similaridade por atributo


@dataclass(frozen=True)
class Sugestao:
    diagnostico: str
    tratamento: str
    confianca: float             # fração do peso dos k casos que apontam para o diagnóstico
    recuperados: list[Recuperado]


# ---------------------------------------------------------------------------
# Base de casos (CSV)
# ---------------------------------------------------------------------------


def _linha(caso: Caso) -> list[str]:
    d = caso.descricao
    return [caso.id, d.faixa_etaria, d.duracao, ";".join(sorted(d.sintomas)),
            caso.diagnostico, caso.tratamento]


def carregar_casos(caminho: Path = CAMINHO_PADRAO) -> list[Caso]:
    with open(caminho, newline="", encoding="utf-8") as f:
        return [
            Caso(
                id=linha["id"],
                descricao=Descricao(
                    linha["faixa_etaria"],
                    linha["duracao"],
                    frozenset(s for s in linha["sintomas"].split(";") if s),
                ),
                diagnostico=linha["diagnostico"],
                tratamento=linha["tratamento"],
            )
            for linha in csv.DictReader(f)
        ]


# ---------------------------------------------------------------------------
# Similaridade
# ---------------------------------------------------------------------------


def similaridade_sintomas(a: frozenset[str], b: frozenset[str]) -> float:
    """Índice de Jaccard: sintomas em comum dividido pelo total de sintomas citados (0 a 1)."""
    if not a and not b:
        return 1.0
    return len(a & b) / len(a | b)


def similaridade_ordinal(escala: list[str], x: str, y: str) -> float:
    """1.0 se igual, 0.5 se vizinhos na escala ordenada, 0.0 caso contrário."""
    distancia = abs(escala.index(x) - escala.index(y))
    return {0: 1.0, 1: 0.5}.get(distancia, 0.0)


def similaridade(consulta: Descricao, caso: Descricao) -> tuple[float, dict[str, float]]:
    """Similaridade global ponderada e a parcela de cada atributo."""
    partes = {
        "sintomas": similaridade_sintomas(consulta.sintomas, caso.sintomas),
        "faixa_etaria": similaridade_ordinal(FAIXAS_ETARIAS, consulta.faixa_etaria, caso.faixa_etaria),
        "duracao": similaridade_ordinal(DURACOES, consulta.duracao, caso.duracao),
    }
    total = sum(PESOS[a] * s for a, s in partes.items()) / sum(PESOS.values())
    return total, partes


# ---------------------------------------------------------------------------
# Ciclo CBR
# ---------------------------------------------------------------------------


def recuperar(consulta: Descricao, base: list[Caso], k: int = K_PADRAO) -> list[Recuperado]:
    """RETRIEVE: os k casos mais semelhantes. Empates: vale a ordem da base."""
    itens = []
    for caso in base:
        score, detalhes = similaridade(consulta, caso.descricao)
        itens.append(Recuperado(caso, score, detalhes))
    itens.sort(key=lambda r: -r.score)  # sort é estável
    return itens[:k]


def reutilizar(recuperados: list[Recuperado]) -> Sugestao:
    """REUSE: vota no diagnóstico, ponderado pela similaridade de cada caso recuperado.

    O tratamento é o do caso mais semelhante que tem o diagnóstico vencedor.
    """
    pesos: dict[str, float] = defaultdict(float)
    for r in recuperados:
        pesos[r.caso.diagnostico] += r.score
    total = sum(pesos.values())
    # max() devolve o primeiro encontrado em caso de empate, na ordem dos recuperados.
    diagnostico = max(pesos, key=lambda d: pesos[d])
    tratamento = next(r.caso.tratamento for r in recuperados if r.caso.diagnostico == diagnostico)
    confianca = pesos[diagnostico] / total if total > 0 else 0.0
    return Sugestao(diagnostico, tratamento, confianca, recuperados)


def revisar(sugestao: Sugestao, confirmado: str | None = None) -> str:
    """REVISE: o profissional aceita a sugestão (confirmado vazio) ou informa outro diagnóstico."""
    if confirmado and confirmado.strip():
        return confirmado.strip()
    return sugestao.diagnostico


def tratamento_para(base: list[Caso], diagnostico: str) -> str | None:
    """Tratamento já registrado para um diagnóstico, ou None se a doença não existe na base."""
    return next((c.tratamento for c in base if c.diagnostico == diagnostico), None)


def reter(base: list[Caso], descricao: Descricao, diagnostico: str, tratamento: str,
          caminho: Path = CAMINHO_PADRAO) -> Caso:
    """RETAIN: grava o caso confirmado na base, em memória e no arquivo CSV."""
    numeros = [int(c.id[1:]) for c in base if c.id[1:].isdigit()]
    novo = Caso(f"C{max(numeros, default=0) + 1:02d}", descricao, diagnostico, tratamento)
    with open(caminho, "a", newline="", encoding="utf-8") as f:
        csv.writer(f, lineterminator="\n").writerow(_linha(novo))
    base.append(novo)
    return novo


# ---------------------------------------------------------------------------
# Avaliação
# ---------------------------------------------------------------------------


def avaliar_loo(base: list[Caso], k: int = K_PADRAO) -> tuple[int, list[tuple[str, str, str]]]:
    """Leave-one-out: para cada caso, recupera nos outros e compara o diagnóstico sugerido."""
    acertos = 0
    detalhes = []
    for i, caso in enumerate(base):
        resto = base[:i] + base[i + 1:]
        sugerido = reutilizar(recuperar(caso.descricao, resto, k)).diagnostico
        detalhes.append((caso.id, caso.diagnostico, sugerido))
        acertos += sugerido == caso.diagnostico
    return acertos, detalhes


# ---------------------------------------------------------------------------
# Apresentação
# ---------------------------------------------------------------------------


def formatar_descricao(d: Descricao) -> str:
    return f"{d.faixa_etaria}, {d.duracao}, sintomas: {', '.join(sorted(d.sintomas))}"


def imprimir_recuperados(recuperados: list[Recuperado]) -> None:
    print(f"  {'Caso':<6}{'Score':>7}{'Sint.':>8}{'Faixa':>7}{'Dur.':>7}  Diagnóstico")
    for r in recuperados:
        d = r.detalhes
        print(f"  {r.caso.id:<6}{r.score:>7.3f}{d['sintomas']:>8.2f}{d['faixa_etaria']:>7.1f}"
              f"{d['duracao']:>7.1f}  {r.caso.diagnostico}")


def imprimir_sugestao(s: Sugestao) -> None:
    print(f"  Diagnóstico sugerido: {s.diagnostico} (confiança {s.confianca:.0%})")
    print(f"  Tratamento sugerido:  {s.tratamento}")


def demonstracao(base: list[Caso]) -> None:
    consultas = [
        ("Paciente A", Descricao("Adulto", "4_a_7_dias",
                                 frozenset({"febre", "tosse", "falta_de_ar", "dor_no_peito"}))),
        ("Paciente B", Descricao("Adulto", "ate_3_dias",
                                 frozenset({"febre", "dor_atras_dos_olhos", "manchas_na_pele",
                                            "dor_muscular"}))),
    ]
    for nome, desc in consultas:
        print("=" * 72)
        print(f"{nome}: {formatar_descricao(desc)}")
        print("=" * 72)
        recuperados = recuperar(desc, base)
        print("RETRIEVE: casos mais semelhantes (k = 5)")
        imprimir_recuperados(recuperados)
        print("\nREUSE:")
        sugestao = reutilizar(recuperados)
        imprimir_sugestao(sugestao)
        print("\nREVISE: o profissional aceita o diagnóstico sugerido (demonstração).")
        print(f"  Diagnóstico confirmado: {revisar(sugestao)}")
        print("RETAIN: não gravado na demonstração (use --interativo para gravar).\n")

    print("=" * 72)
    print("Avaliação leave-one-out da base (acertos do diagnóstico sugerido)")
    print("=" * 72)
    print(f"  {'k':>3}  {'Acertos':>9}  {'Acurácia':>9}")
    for k in (1, 3, 5, 7):
        acertos, _ = avaliar_loo(base, k)
        print(f"  {k:>3}  {acertos:>4}/{len(base):<4}  {100 * acertos / len(base):>8.1f}%")


def perguntar_opcao(titulo: str, opcoes: list[str]) -> str:
    print(titulo)
    for i, opcao in enumerate(opcoes, 1):
        print(f"  {i}. {opcao}")
    while True:
        r = input("Escolha o número: ").strip()
        if r.isdigit() and 1 <= int(r) <= len(opcoes):
            return opcoes[int(r) - 1]
        print("Opção inválida.")


def perguntar_sintomas() -> frozenset[str]:
    print("Sintomas do paciente:")
    for i, s in enumerate(SINTOMAS, 1):
        print(f"  {i:>2}. {s}")
    while True:
        r = input("Números separados por vírgula (ex.: 1,2,13): ").replace(" ", "")
        try:
            escolhidos = {int(x) for x in r.split(",") if x}
        except ValueError:
            escolhidos = set()
        if escolhidos and all(1 <= n <= len(SINTOMAS) for n in escolhidos):
            return frozenset(SINTOMAS[n - 1] for n in escolhidos)
        print(f"Informe ao menos um número entre 1 e {len(SINTOMAS)}.")


def modo_interativo(caminho: Path = CAMINHO_PADRAO) -> None:
    base = carregar_casos(caminho)
    print("\nAVISO: protótipo acadêmico com casos fictícios. Não substitui avaliação médica.\n")
    desc = Descricao(
        perguntar_opcao("Faixa etária:", FAIXAS_ETARIAS),
        perguntar_opcao("Duração dos sintomas:", DURACOES),
        perguntar_sintomas(),
    )
    recuperados = recuperar(desc, base)
    print("\nRETRIEVE: casos mais semelhantes")
    imprimir_recuperados(recuperados)
    print("\nREUSE:")
    sugestao = reutilizar(recuperados)
    imprimir_sugestao(sugestao)

    resposta = input(f"\nREVISE: diagnóstico confirmado? [Enter = {sugestao.diagnostico}, "
                     f"ou digite outro]: ")
    diagnostico = revisar(sugestao, resposta)

    if input("RETAIN: gravar este caso na base? [s/N]: ").strip().lower() != "s":
        print("Caso não gravado.")
        return
    if diagnostico == sugestao.diagnostico:
        tratamento = sugestao.tratamento
    else:
        tratamento = tratamento_para(base, diagnostico) or input("Tratamento para o novo caso: ").strip()
    novo = reter(base, desc, diagnostico, tratamento, caminho)
    print(f"Caso {novo.id} gravado em {caminho.name}.")


def main() -> None:
    if "--interativo" in sys.argv:
        modo_interativo()
    else:
        demonstracao(carregar_casos())


if __name__ == "__main__":
    main()
