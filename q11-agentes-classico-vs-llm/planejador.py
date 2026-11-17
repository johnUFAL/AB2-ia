from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from itertools import product

SLOT = 30                 # granularidade da grade, em minutos
INICIO = 14 * 60          # 14h
FIM = 18 * 60             # 18h

# Peso atribuído a conclusão de cada atividade.
PESO = {"Alta": 5, "Media": 3, "Baixa": 1}


@dataclass(frozen=True)
class Atividade:
    id: str
    nome: str
    duracao: int
    prioridade: str
    prazo: str
    inicio_fixo: int | None = None
    divisivel: bool = False

    @property
    def obrigatoria(self) -> bool:
        return self.prazo == "hoje"

    @property
    def slots(self) -> int:
        return self.duracao // SLOT


ATIVIDADES = [
    Atividade("A", "Preparar aula de IA", 90, "Alta", "hoje"),
    Atividade("B", "Corrigir trabalhos", 120, "Media", "amanha"),
    Atividade("C", "Reunião de pesquisa", 60, "Alta", "hoje", inicio_fixo=16 * 60),
    Atividade("D", "Revisar artigo", 60, "Baixa", "semana"),
]

Bloco = tuple[str, int, int]


def hhmm(minutos: int) -> str:
    return f"{minutos // 60:02d}:{minutos % 60:02d}"


def minutos(texto: str) -> int:
    h, m = texto.split(":")
    return int(h) * 60 + int(m)


@dataclass
class Resultado:
    blocos: list[Bloco]
    utilidade: Fraction
    nao_realizadas: dict[str, str]
    avaliados: int
    viaveis: int


def _agrupar(slots: list[int]) -> list[tuple[int, int]]:
    """Junta slots consecutivos em intervalos"""
    intervalos: list[list[int]] = []
    for t in sorted(slots):
        if intervalos and intervalos[-1][1] == t:
            intervalos[-1][1] = t + SLOT
        else:
            intervalos.append([t, t + SLOT])
    return [(i, f) for i, f in intervalos]


def planejar(atividades: list[Atividade] = ATIVIDADES, inicio: int = INICIO, fim: int = FIM,
             peso: dict[str, int] = PESO) -> Resultado:
    """Retorna o plano de maior utilidade que atende às restrições"""
    for a in atividades:
        if a.duracao % SLOT:
            raise ValueError(f"{a.id}: duração deve ser múltipla de {SLOT} min")

    fixos = {a.id: list(range(a.inicio_fixo, a.inicio_fixo + a.duracao, SLOT))
             for a in atividades if a.inicio_fixo is not None}
    ocupados = [t for slots in fixos.values() for t in slots]
    if len(ocupados) != len(set(ocupados)) or any(not inicio <= t < fim for t in ocupados):
        raise ValueError("compromissos fixos se sobrepõem ou saem da janela")

    livres = [t for t in range(inicio, fim, SLOT) if t not in set(ocupados)]
    moveis = [a for a in atividades if a.inicio_fixo is None]
    por_id = {a.id: a for a in atividades}

    melhor = None
    avaliados = viaveis = 0
    for atribuicao in product([None] + [a.id for a in moveis], repeat=len(livres)):
        avaliados += 1
        plano = {k: list(v) for k, v in fixos.items()}
        for t, x in zip(livres, atribuicao):
            if x is not None:
                plano.setdefault(x, []).append(t)
        if not _viavel(plano, atividades):
            continue
        viaveis += 1
        chave = _chave(plano, por_id, peso)
        if melhor is None or chave > melhor[0]:
            melhor = (chave, plano)

    if melhor is None:
        raise ValueError("nenhum plano respeita as restrições obrigatórias")

    (utilidade, _), plano = melhor
    blocos = sorted(
        ((i, ini, f) for i, slots in plano.items() for ini, f in _agrupar(slots)),
        key=lambda b: b[1],
    )
    return Resultado(blocos, utilidade, _justificar(plano, atividades, livres), avaliados, viaveis)


def _viavel(plano: dict[str, list[int]], atividades: list[Atividade]) -> bool:
    for a in atividades:
        n = len(plano.get(a.id, []))
        if a.obrigatoria and n != a.slots:
            return False
        if n and not a.divisivel and n != a.slots:
            return False
        if n and not a.divisivel and len(_agrupar(plano[a.id])) > 1:
            return False
    return True


def _chave(plano, por_id, peso) -> tuple[Fraction, int]:
    """Compara planos por utilidade; em caso de empate, prioriza términos mais cedo."""
    utilidade = Fraction(0)
    atraso = 0
    for i, slots in plano.items():
        a = por_id[i]
        utilidade += Fraction(peso[a.prioridade] * len(slots), a.slots)
        atraso += peso[a.prioridade] * (max(slots) + SLOT)
    return utilidade, -atraso


def _justificar(plano, atividades, livres) -> dict[str, str]:
    """Informa por que cada atividade não foi concluída"""
    usados = {t for slots in plano.values() for t in slots}
    sobra = sorted(t for t in livres if t not in usados)
    maior_bloco = max((f - i for i, f in _agrupar(sobra)), default=0)
    destino = {"hoje": "", "amanha": " Reagendar para amanhã (prazo: amanhã).",
               "semana": " Sem urgência (prazo: próxima semana)."}
    saida = {}
    for a in atividades:
        feito = len(plano.get(a.id, [])) * SLOT
        if feito >= a.duracao:
            continue
        if feito:
            motivo = f"Feita parcialmente ({feito} de {a.duracao} min)."
        elif a.divisivel is False and a.duracao > maior_bloco > 0:
            motivo = (f"Não coube: exige {a.duracao} min contínuos e o maior bloco livre "
                      f"é de {maior_bloco} min.")
        elif not sobra:
            motivo = "Sem tempo livre: ele foi usado por atividades de maior utilidade."
        else:
            motivo = "Outra combinação rendeu mais utilidade no tempo disponível."
        saida[a.id] = motivo + destino[a.prazo]
    return saida


def verificar(blocos: list[Bloco], atividades: list[Atividade] = ATIVIDADES,
              inicio: int = INICIO, fim: int = FIM) -> list[str]:
    """Retorna as violações encontradas; uma lista vazia indica um plano válido"""
    por_id = {a.id: a for a in atividades}
    erros = []

    for i, ini, f in blocos:
        if i not in por_id:
            erros.append(f"atividade desconhecida: {i}")
        if not ini < f:
            erros.append(f"{i}: bloco {hhmm(ini)}-{hhmm(f)} com duração inválida")
        if ini < inicio or f > fim:
            erros.append(f"{i}: bloco {hhmm(ini)}-{hhmm(f)} fora da janela {hhmm(inicio)}-{hhmm(fim)}")

    ordenados = sorted(blocos, key=lambda b: b[1])
    for (i1, _, f1), (i2, ini2, _) in zip(ordenados, ordenados[1:]):
        if f1 > ini2:
            erros.append(f"sobreposição entre {i1} e {i2} ({hhmm(ini2)}-{hhmm(f1)})")

    for a in atividades:
        meus = [b for b in blocos if b[0] == a.id]
        total = sum(f - i for _, i, f in meus)
        if total > a.duracao:
            erros.append(f"{a.id}: {total} min alocados, mas dura {a.duracao}")
        if a.obrigatoria and total != a.duracao:
            erros.append(f"{a.id}: prazo hoje, mas só {total} de {a.duracao} min foram alocados")
        if meus and not a.divisivel and (total != a.duracao or len(meus) > 1):
            erros.append(f"{a.id}: atividade indivisível, iniciada tem que ser concluída em bloco único")
        if a.inicio_fixo is not None and [(i, f) for _, i, f in meus] != [(a.inicio_fixo, a.inicio_fixo + a.duracao)]:
            erros.append(f"{a.id}: compromisso fixo às {hhmm(a.inicio_fixo)} não respeitado")
    return erros


def ferramenta_planejar(args: dict) -> dict:
    """Planeja a partir de atividades e horários recebidos em formato JSON"""
    atividades = [
        Atividade(
            id=x["id"], nome=x["nome"], duracao=x["duracao_min"], prioridade=x["prioridade"],
            prazo=x["prazo"],
            inicio_fixo=minutos(x["inicio_fixo"]) if x.get("inicio_fixo") else None,
            divisivel=x.get("divisivel", False),
        )
        for x in args["atividades"]
    ]
    janela = args.get("janela", {"inicio": hhmm(INICIO), "fim": hhmm(FIM)})
    ini, f = minutos(janela["inicio"]), minutos(janela["fim"])
    r = planejar(atividades, ini, f)
    return {
        "plano": [{"id": i, "inicio": hhmm(a), "fim": hhmm(b)} for i, a, b in r.blocos],
        "utilidade": float(r.utilidade),
        "nao_realizadas": r.nao_realizadas,
        "violacoes": verificar(r.blocos, atividades, ini, f),
    }


def mostrar(titulo: str, r: Resultado, atividades: list[Atividade] = ATIVIDADES) -> None:
    nomes = {a.id: a.nome for a in atividades}
    print(f"\n--- {titulo} ---")
    for i, ini, f in r.blocos:
        print(f"  {hhmm(ini)}-{hhmm(f)}  {i} - {nomes[i]}")
    print(f"  Utilidade: {float(r.utilidade):.2f} | combinações: {r.avaliados} ({r.viaveis} viáveis)")
    for i, motivo in r.nao_realizadas.items():
        print(f"  Ficou pendente: {i} - {nomes[i]}: {motivo}")


def main() -> None:
    print("Planejamento do dia")

    mostrar("Plano sem dividir atividades", planejar())

    dividida = [Atividade(a.id, a.nome, a.duracao, a.prioridade, a.prazo, a.inicio_fixo,
                          divisivel=(a.id == "B")) for a in ATIVIDADES]
    mostrar("Plano com correção em blocos de 30 min",
            planejar(dividida), dividida)

    print("\nEfeito dos pesos")
    print(f"  {'Pesos (Alta/Média/Baixa)':<26}{'Sem divisão':<20}Correção divisível")
    for p in ({"Alta": 5, "Media": 3, "Baixa": 1}, {"Alta": 10, "Media": 2, "Baixa": 1},
              {"Alta": 5, "Media": 1, "Baixa": 3}):
        base = planejar(peso=p)
        var = planejar(dividida, peso=p)
        resumo = lambda r: ", ".join(sorted({i for i, _, _ in r.blocos} - {"C"}))
        print(f"  {str(tuple(p.values())):<26}{resumo(base):<20}{resumo(var)}")


if __name__ == "__main__":
    main()
