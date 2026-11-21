"""Agente de planejamento com interpretação por LLM e verificação determinística.

O modelo de linguagem é trocável. O padrão é o Ollama (local, sem chave de API).
A Anthropic continua disponível como opção, mas exige ANTHROPIC_API_KEY.

Configuração por variáveis de ambiente:
    LLM_PROVIDER   "ollama" (padrão) ou "anthropic"
    OLLAMA_HOST    endereço do servidor Ollama (padrão http://localhost:11434)
    OLLAMA_MODEL   modelo instalado no Ollama (padrão "llama3.2")
    ANTHROPIC_API_KEY  só é necessária se LLM_PROVIDER=anthropic
"""

from __future__ import annotations

import inspect
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Callable

_PLANEJADOR_DIR = Path(__file__).resolve().parents[1] / "q11-agentes-classico-vs-llm"
if str(_PLANEJADOR_DIR) not in sys.path:
    sys.path.insert(0, str(_PLANEJADOR_DIR))

import planejador  # noqa: E402  (depende da Q11)

LLM = Callable[[str, list[dict[str, str]]], str]

PROVEDOR_PADRAO = "ollama"
OLLAMA_HOST_PADRAO = "http://localhost:11434"
OLLAMA_MODELO_PADRAO = "llama3.2"
ANTHROPIC_MODELO = "claude-opus-5-5"


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
    if isinstance(plano, dict) and isinstance(plano.get("plano"), list):
        plano = plano["plano"]  # aceita {"plano": [...]}, formato comum em modelos menores
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


# ---------------------------------------------------------------------------
# Provedores de LLM
# ---------------------------------------------------------------------------


def verificar_ollama(timeout: int = 5) -> None:
    """Confere, antes de começar, se o servidor responde e se o modelo está instalado."""
    host = os.environ.get("OLLAMA_HOST", OLLAMA_HOST_PADRAO).rstrip("/")
    modelo = os.environ.get("OLLAMA_MODEL", OLLAMA_MODELO_PADRAO)
    try:
        with urllib.request.urlopen(f"{host}/api/tags", timeout=timeout) as resposta:
            dados = json.loads(resposta.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, OSError) as erro:
        raise RuntimeError(
            f"Ollama não responde em {host}. Abra o aplicativo Ollama "
            "(ou rode 'ollama serve') e tente de novo."
        ) from erro
    instalados = {m.get("name", "") for m in dados.get("models", [])}
    if not any(nome == modelo or nome.split(":")[0] == modelo.split(":")[0] for nome in instalados):
        raise RuntimeError(
            f"O modelo '{modelo}' não está instalado. Rode 'ollama pull {modelo}'. "
            f"Modelos instalados: {', '.join(sorted(instalados)) or 'nenhum'}."
        )


def chamar_ollama(sistema: str, mensagens: list[dict[str, str]]) -> str:
    """Chama um modelo local pelo Ollama (API /api/chat). Não usa chave de API."""
    host = os.environ.get("OLLAMA_HOST", OLLAMA_HOST_PADRAO).rstrip("/")
    modelo = os.environ.get("OLLAMA_MODEL", OLLAMA_MODELO_PADRAO)
    timeout = int(os.environ.get("OLLAMA_TIMEOUT", "300"))
    corpo = {
        "model": modelo,
        "messages": [{"role": "system", "content": sistema}, *mensagens],
        "stream": False,
        "format": "json",  # força a saída em JSON, como o agente espera
    }
    pedido = urllib.request.Request(
        f"{host}/api/chat",
        data=json.dumps(corpo).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(pedido, timeout=timeout) as resposta:
            dados = json.loads(resposta.read().decode("utf-8"))
    except urllib.error.URLError as erro:
        raise RuntimeError(
            f"Não foi possível conectar ao Ollama em {host}. "
            "Verifique se o serviço está rodando e se o modelo "
            f"'{modelo}' foi baixado (ollama pull {modelo})."
        ) from erro

    texto = dados.get("message", {}).get("content", "")
    if not texto:
        raise RuntimeError("O Ollama não retornou conteúdo de texto.")
    return texto


def chamar_anthropic(sistema: str, mensagens: list[dict[str, str]]) -> str:
    """Chama a API da Anthropic. Exige ANTHROPIC_API_KEY."""
    chave = os.environ.get("ANTHROPIC_API_KEY")
    if not chave:
        raise RuntimeError("Defina ANTHROPIC_API_KEY para usar o provedor anthropic.")
    try:
        import anthropic
    except ImportError as erro:
        raise RuntimeError("Instale a dependência anthropic para usar o provedor anthropic.") from erro

    cliente = anthropic.Anthropic(api_key=chave)
    resposta = cliente.messages.create(
        model=ANTHROPIC_MODELO,
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


PROVEDORES: dict[str, LLM] = {
    "ollama": chamar_ollama,
    "anthropic": chamar_anthropic,
}


def escolher_llm() -> LLM:
    """Escolhe o provedor pela variável LLM_PROVIDER (padrão: ollama)."""
    nome = (os.environ.get("LLM_PROVIDER") or PROVEDOR_PADRAO).strip().lower()
    if nome not in PROVEDORES:
        raise RuntimeError(f"Provedor desconhecido: {nome}. Use: {', '.join(PROVEDORES)}.")
    return PROVEDORES[nome]


def extrair_json(texto: str) -> dict:
    try:
        decisao = json.loads(texto)
    except json.JSONDecodeError as erro:
        raise ValueError("resposta sem JSON válido") from erro
    if not isinstance(decisao, dict):
        raise ValueError("a resposta JSON precisa ser um objeto")
    return decisao


def _resposta_util(texto: str) -> bool:
    """Recusa resposta vazia ou copiada do próprio prompt do sistema."""
    limpo = texto.strip()
    return len(limpo) >= 20 and limpo not in SISTEMA


def _plano_do_planejador(registro: list[dict]) -> tuple[list, dict] | None:
    """Último plano produzido por 'planejar' que passa na verificação, ou None."""
    for etapa in reversed(registro):
        if etapa.get("acao") == "planejar" and isinstance(etapa.get("resultado"), dict):
            plano = etapa["resultado"].get("plano")
            pendencias = etapa["resultado"].get("pendencias", {})
            try:
                valido = bool(plano) and f_verificar_plano(plano, False)["valido"]
            except (TypeError, ValueError):
                valido = False
            return (plano, pendencias) if valido else None
    return None


def _texto_do_plano(plano: list, pendencias: dict) -> str:
    """Texto com os horários verificados e as pendências, sem depender do modelo."""
    linhas = [f"{b.get('inicio')}–{b.get('fim')}  {b.get('atividade')}" for b in plano]
    texto = "Plano verificado pelo planejador:\n" + "\n".join(linhas)
    if pendencias:
        texto += "\nPendências: " + "; ".join(f"{k}: {v}" for k, v in pendencias.items())
    return texto


def executar_agente(
    pedido: str,
    llm: LLM | None = None,
    max_passos: int = 20,
    progresso=None,
    aceita_divisao: bool = False,
) -> dict:
    """aceita_divisao=True só quando o professor autoriza dividir a correção B."""
    if not pedido.strip():
        raise ValueError("o pedido não pode estar vazio")
    if max_passos < 1:
        raise ValueError("max_passos deve ser pelo menos 1")

    chamar = llm or escolher_llm()
    mensagens = [{"role": "user", "content": pedido}]
    registro = []

    for passo in range(1, max_passos + 1):
        if progresso:
            progresso(f"Passo {passo}: aguardando o modelo responder...")
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
                if divisao and not aceita_divisao:
                    raise ValueError("divisão da atividade B não foi autorizada pelo professor")
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
            texto = decisao["resposta_final"]
            if not isinstance(texto, str):
                raise ValueError("resposta_final precisa ser texto")
            if conferencia["valido"] and _resposta_util(texto):
                return {"resposta": texto, "plano": decisao["plano"], "registro": registro}
            if conferencia["valido"]:
                observacao = {
                    "erro": "resposta_final deve explicar ao professor os horários e as "
                            "pendências, com suas próprias palavras."
                }
            else:
                encontrado = _plano_do_planejador(registro)
                if encontrado:
                    # O texto é do modelo; o plano é o último já verificado pelo planejador.
                    return {
                        "resposta": texto,
                        "plano": encontrado[0],
                        "origem_do_plano": "planejador",
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
                    raise ValueError(
                        f"ferramenta desconhecida: {nome}. Use somente: "
                        + "; ".join(f"{n}{inspect.signature(f)}" for n, f in FERRAMENTAS.items())
                    )
                if not isinstance(argumentos, dict):
                    raise ValueError("argumentos da ferramenta devem ser um objeto")
                if argumentos.get("permitir_divisao") and not aceita_divisao:
                    raise ValueError(
                        "divisão da atividade B não foi autorizada pelo professor; "
                        "use permitir_divisao=false"
                    )
                observacao = FERRAMENTAS[nome](**argumentos)
                if nome == "verificar_plano" and observacao.get("valido"):
                    # Sem este aviso, modelos pequenos costumam repetir ferramentas em vez de responder.
                    observacao = {
                        **observacao,
                        "proximo_passo": "Plano válido. Responda agora com resposta_final, "
                                         "usando este mesmo plano.",
                    }
                acao = nome
            except TypeError as erro:
                assinatura = inspect.signature(FERRAMENTAS[nome]) if nome in FERRAMENTAS else ""
                observacao = {
                    "erro": f"argumentos inválidos ({erro}). Use: {nome}{assinatura}"
                }
                acao = f"falha na ferramenta {nome}"
            except (KeyError, ValueError) as erro:
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
            if acao == "planejar":
                # Parada antecipada: o planejador já devolveu um plano verificado.
                encontrado = _plano_do_planejador(registro)
                if encontrado:
                    return {
                        "resposta": _texto_do_plano(*encontrado),
                        "plano": encontrado[0],
                        "origem_do_plano": "planejador",
                        "registro": registro,
                    }
        mensagens.append(
            {"role": "user", "content": json.dumps(observacao, ensure_ascii=False)}
        )

    # Fallback: o último plano do planejador só é usado se passar na verificação determinística.
    for etapa in reversed(registro):
        if etapa.get("acao") == "planejar" and isinstance(etapa.get("resultado"), dict):
            plano = etapa["resultado"].get("plano")
            pendencias = etapa["resultado"].get("pendencias", {})
            try:
                valido = bool(plano) and f_verificar_plano(plano, False)["valido"]
            except (TypeError, ValueError):
                valido = False
            if valido:
                linhas = [f"{b['inicio']}–{b['fim']}  {b['atividade']}" for b in plano]
                texto = (
                    "O modelo não concluiu a resposta dentro do limite de passos. "
                    "Plano do planejador, verificado automaticamente:\n"
                    + "\n".join(linhas)
                )
                if pendencias:
                    texto += "\nPendências: " + "; ".join(
                        f"{chave}: {valor}" for chave, valor in pendencias.items()
                    )
                return {"resposta": texto, "plano": plano, "registro": registro}
            break

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


def planejar_direto() -> dict:
    """Caminho rápido e determinístico: planejador + verificação, sem chamar o modelo."""
    resultado = f_planejar(False)
    registro = [{"passo": 1, "acao": "planejar", "resultado": resultado}]
    encontrado = _plano_do_planejador(registro)
    if not encontrado:
        return {"resposta": "O planejador não encontrou um plano válido.",
                "plano": None, "registro": registro}
    return {
        "resposta": _texto_do_plano(*encontrado),
        "plano": encontrado[0],
        "origem_do_plano": "planejador",
        "registro": registro,
    }


def main() -> None:
    if "--llm" not in sys.argv:
        print(planejar_direto()["resposta"])
        print("\n(Para usar o modelo de linguagem, rode com --llm.)")
        return

    def progresso(mensagem: str) -> None:
        print(mensagem, flush=True)

    provedor = (os.environ.get("LLM_PROVIDER") or PROVEDOR_PADRAO).strip().lower()
    try:
        if provedor == "ollama":
            progresso("Verificando o Ollama...")
            verificar_ollama()
        resultado = executar_agente(PEDIDO_EXEMPLO, progresso=progresso)
    except RuntimeError as erro:
        print(f"\nErro: {erro}", file=sys.stderr)
        sys.exit(1)
    print("\n" + resultado["resposta"])
    if resultado.get("plano") and resultado.get("origem_do_plano") != "planejador":
        print("\nPlano verificado:")
        for bloco in resultado["plano"]:
            print(f"  {bloco.get('inicio')}–{bloco.get('fim')}  {bloco.get('atividade')}")
    for etapa in resultado["registro"]:
        print(f"\nPasso {etapa['passo']}: {etapa['acao']}")
        if "resultado" in etapa:
            print(json.dumps(etapa["resultado"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
