"""Agente de planejamento com interpretação por LLM e verificação determinística."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Callable

_PLANEJADOR_DIR = Path(__file__).resolve().parents[1] / "q11-agentes-classico-vs-llm"
if str(_PLANEJADOR_DIR) not in sys.path:
    sys.path.insert(0, str(_PLANEJADOR_DIR))

import planejador

MODELO = "claude-opus-5-5"
LLM = Callable[[str, list[dict[str, str]]], str]


def _atividades(permitir_divisao: bool = False) -> list[planejador.Atividade]:
    if not isinstance(permitir_divisao, bool):
        raise ValueError("permitir_divisao deve ser booleano")
    return [
        planejador.Atividade(
            atividade.id,
            atividade.nome,
            atividade.duracao,
            atividade.prioridade,
            atividade.prazo,
            atividade.inicio_fixo,
            divisivel=permitir_divisao and atividade.id == "B",
        )
        for atividade in planejador.ATIVIDADES
    ]


def _hora(minuto: int) -> str:
    return f"{minuto // 60:02d}:{minuto % 60:02d}"


def _ler_plano(plano: object) -> list[planejador.Bloco]:
    if not isinstance(plano, list):
        raise ValueError("plano deve ser uma lista")

    blocos = []
    for bloco in plano:
        if not isinstance(bloco, dict):
            raise ValueError("cada bloco do plano deve ser um objeto")
        atividade = bloco.get("id", bloco.get("atividade"))
        inicio, fim = bloco.get("inicio"), bloco.get("fim")
        if not isinstance(atividade, str) or not isinstance(inicio, str) or not isinstance(fim, str):
            raise ValueError("cada bloco precisa de atividade, inicio e fim em texto")
        if atividade not in {item.id for item in planejador.ATIVIDADES}:
            por_nome = {item.nome: item.id for item in planejador.ATIVIDADES}
            atividade = por_nome.get(atividade, atividade)
        blocos.append((atividade, planejador.minutos(inicio), planejador.minutos(fim)))
    return blocos


def f_consultar_agenda() -> dict:
    return {
        "horario_disponivel": [
            _hora(planejador.INICIO),
            _hora(planejador.FIM),
        ],
        "atividades": [
            {
                "id": atividade.id,
                "nome": atividade.nome,
                "duracao_min": atividade.duracao,
                "prioridade": atividade.prioridade,
                "prazo": atividade.prazo,
                "horario_fixo": (
                    _hora(atividade.inicio_fixo)
                    if atividade.inicio_fixo is not None
                    else None
                ),
            }
            for atividade in planejador.ATIVIDADES
        ],
    }


def f_planejar(permitir_divisao: bool = False) -> dict:
    atividades = _atividades(permitir_divisao)
    resultado = planejador.planejar(atividades)
    nomes = {atividade.id: atividade.nome for atividade in atividades}
    return {
        "plano": [
            {
                "atividade": nomes[identificador],
                "id": identificador,
                "inicio": _hora(inicio),
                "fim": _hora(fim),
            }
            for identificador, inicio, fim in resultado.blocos
        ],
        "utilidade": float(resultado.utilidade),
        "pendencias": resultado.nao_realizadas,
    }


def f_verificar_plano(plano: object, permitir_divisao: bool = False) -> dict:
    atividades = _atividades(permitir_divisao)
    erros = planejador.verificar(_ler_plano(plano), atividades)
    return {"valido": not erros, "violacoes": erros}


def f_calcular_utilidade(plano: object, permitir_divisao: bool = False) -> dict:
    verificacao = f_verificar_plano(plano, permitir_divisao)
    if not verificacao["valido"]:
        raise ValueError("plano inválido: " + "; ".join(verificacao["violacoes"]))
    blocos = _ler_plano(plano)
    atividades = _atividades(permitir_divisao)
    por_id = {atividade.id: atividade for atividade in atividades}
    utilidade = sum(
        planejador.PESO[por_id[identificador].prioridade]
        * (fim - inicio)
        / por_id[identificador].duracao
        for identificador, inicio, fim in blocos
    )
    return {"utilidade": round(utilidade, 2)}


FERRAMENTAS = {
    "consultar_agenda": f_consultar_agenda,
    "planejar": f_planejar,
    "verificar_plano": f_verificar_plano,
    "calcular_utilidade": f_calcular_utilidade,
}

SISTEMA = """Você organiza a agenda de um professor universitário.

Responda em cada passo com exatamente um objeto JSON, sem texto fora dele.

Para usar uma ferramenta:
{"pensamento": "motivo breve", "acao": "nome_da_ferramenta", "argumentos": {}}

Para concluir:
{"pensamento": "motivo breve", "plano": [{"atividade": "A", "inicio": "14:00", "fim": "15:30"}], "permitir_divisao": false, "resposta_final": "texto para o professor"}

Ferramentas:
- consultar_agenda(): informa a janela e as atividades identificadas por A, B, C e D.
- planejar(permitir_divisao): calcula o plano ótimo. Só permita divisão se o professor aceitar explicitamente dividir a correção B.
- verificar_plano(plano, permitir_divisao): valida horários e restrições.
- calcular_utilidade(plano, permitir_divisao): calcula a utilidade de um plano válido.

Consulte a agenda antes de planejar. Não invente durações nem prazos. Se houver
uma condição adicional, ajuste o plano e verifique-o. Na resposta final, liste
os horários e explique atividades incompletas ou adiadas. O plano final será
validado automaticamente; corrija-o se receber violações."""


def chamar_llm(sistema: str, mensagens: list[dict[str, str]]) -> str:
    chave = os.environ.get("ANTHROPIC_API_KEY")
    if not chave:
        raise RuntimeError("Defina ANTHROPIC_API_KEY para chamar o agente LLM.")
    try:
        import anthropic
    except ImportError as erro:
        raise RuntimeError("Instale a dependência anthropic para usar o agente LLM.") from erro

    cliente = anthropic.Anthropic(api_key=chave)
    resposta = cliente.messages.create(
        model=MODELO,
        max_tokens=2048,
        system=sistema,
        messages=mensagens,
    )
    texto = "".join(
        bloco.text for bloco in resposta.content if getattr(bloco, "type", None) == "text"
    )
    if not texto:
        raise RuntimeError("A API do modelo não retornou conteúdo de texto.")
    return texto


def extrair_json(texto: str) -> dict:
    try:
        decisao = json.loads(texto)
    except json.JSONDecodeError as erro:
        raise ValueError("resposta sem JSON válido") from erro
    if not isinstance(decisao, dict):
        raise ValueError("a resposta JSON precisa ser um objeto")
    return decisao


def executar_agente(
    pedido: str, llm: LLM | None = None, max_passos: int = 8
) -> dict:
    if not pedido.strip():
        raise ValueError("o pedido não pode estar vazio")
    if max_passos < 1:
        raise ValueError("max_passos deve ser pelo menos 1")

    chamar = llm or chamar_llm
    mensagens = [{"role": "user", "content": pedido}]
    registro = []

    for passo in range(1, max_passos + 1):
        texto = chamar(SISTEMA, mensagens)
        mensagens.append({"role": "assistant", "content": texto})
        try:
            decisao = extrair_json(texto)
        except ValueError as erro:
            observacao = {"erro": f"{erro}. Responda somente com um objeto JSON."}
            registro.append(
                {
                    "passo": passo,
                    "acao": "resposta fora do formato",
                    "resultado": observacao,
                }
            )
            mensagens.append(
                {"role": "user", "content": json.dumps(observacao, ensure_ascii=False)}
            )
            continue

        pensamento = decisao.get("pensamento", "")
        if "resposta_final" in decisao:
            divisao = decisao.get("permitir_divisao", False)
            try:
                conferencia = f_verificar_plano(decisao.get("plano"), divisao)
            except (TypeError, ValueError) as erro:
                conferencia = {"valido": False, "violacoes": [str(erro)]}
            registro.append(
                {
                    "passo": passo,
                    "pensamento": pensamento,
                    "acao": "resposta final conferida",
                    "resultado": conferencia,
                }
            )
            if conferencia["valido"]:
                resposta_final = decisao["resposta_final"]
                if not isinstance(resposta_final, str):
                    raise ValueError("resposta_final precisa ser texto")
                return {
                    "resposta": resposta_final,
                    "plano": decisao["plano"],
                    "registro": registro,
                }
            observacao = {
                "erro": "O plano final tem violações. Corrija-o.",
                "violacoes": conferencia["violacoes"],
            }
        else:
            nome = decisao.get("acao")
            argumentos = decisao.get("argumentos", {})
            try:
                if not isinstance(nome, str) or nome not in FERRAMENTAS:
                    raise ValueError(f"ferramenta desconhecida: {nome}")
                if not isinstance(argumentos, dict):
                    raise ValueError("argumentos da ferramenta devem ser um objeto")
                observacao = FERRAMENTAS[nome](**argumentos)
                acao = nome
            except (KeyError, TypeError, ValueError) as erro:
                observacao = {"erro": str(erro)}
                acao = f"falha na ferramenta {nome}"
            registro.append(
                {
                    "passo": passo,
                    "pensamento": pensamento,
                    "acao": acao,
                    "resultado": observacao,
                }
            )
        mensagens.append(
            {"role": "user", "content": json.dumps(observacao, ensure_ascii=False)}
        )

    return {
        "resposta": "Não foi possível chegar a um plano válido dentro do limite de passos.",
        "plano": None,
        "registro": registro,
    }


PEDIDO_EXEMPLO = (
    "Preciso preparar uma aula de Inteligência Artificial, corrigir trabalhos "
    "e participar de uma reunião de pesquisa. Tenho quatro horas hoje. A aula "
    "é urgente, e os trabalhos precisam ser concluídos até amanhã. Organize "
    "minhas atividades da melhor maneira possível."
)


def main() -> None:
    resultado = executar_agente(PEDIDO_EXEMPLO)
    print(resultado["resposta"])
    for etapa in resultado["registro"]:
        print(f"\nPasso {etapa['passo']}: {etapa['acao']}")
        if "resultado" in etapa:
            print(json.dumps(etapa["resultado"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
