# Q12: Agente de planejamento baseado em LLM

Assistente que interpreta um pedido em linguagem natural, chama ferramentas determinísticas para planejar e verificar a agenda, e devolve uma resposta com o registro de cada ação. O planejador e as regras de validação são reutilizados da [Q11](../q11-agentes-classico-vs-llm/planejador.py), sem copiar ou manter uma segunda implementação.

## Modelo de linguagem

O modelo é trocável. O padrão é o **Ollama** (local), que não exige chave de API. A Anthropic continua disponível como opção.

| Variável | Padrão | Uso |
|---|---|---|
| `LLM_PROVIDER` | `ollama` | `ollama` ou `anthropic` |
| `OLLAMA_HOST` | `http://localhost:11434` | endereço do servidor Ollama |
| `OLLAMA_MODEL` | `llama3.2` | modelo instalado (`ollama pull <modelo>`) |
| `ANTHROPIC_API_KEY` | — | só é necessária com `LLM_PROVIDER=anthropic` |

O Ollama é chamado com `format: json`, o que força a saída em JSON. Modelos pequenos podem errar o formato. Nesse caso, o agente devolve a observação de formato e tenta de novo, até o limite de passos.

## Como executar

Com o Ollama instalado e o modelo baixado:

```powershell
ollama pull llama3.2
python q12-agente-llm\agente_llm.py
```

Para usar a Anthropic:

```powershell
$env:LLM_PROVIDER = "anthropic"
$env:ANTHROPIC_API_KEY = "sua-chave"
python q12-agente-llm\agente_llm.py
```

A chave não deve ser gravada nos arquivos do projeto.

## Ferramentas e verificação

- `consultar_agenda` retorna os dados definidos no planejador da Q11.
- `planejar` chama a busca exata da Q11. A divisão só é permitida para a correção de trabalhos (B), quando solicitada.
- `verificar_plano` rejeita sobreposições, horários fora da janela e demais violações antes que uma resposta final seja aceita.
- `calcular_utilidade` calcula o valor apenas para planos válidos.

O ciclo aceita uma função LLM injetada, então pode ser testado sem Ollama nem chave.

## Testes

Na raiz do repositório:

```powershell
python -m unittest discover -s q12-agente-llm -p "test_*.py" -v
```

Os testes do planejador (`TestFerramentasDoPlanejador`) precisam de `q11-agentes-classico-vs-llm/planejador.py`. Os demais não dependem da Q11.

## Arquivos

| Arquivo | Conteúdo |
|---|---|
| `agente_llm.py` | Ferramentas, ciclo do agente e provedores de LLM (Ollama e Anthropic) |
| `test_agente_llm.py` | Testes do provedor, do ciclo com LLM falso e do planejador |

## Status

- [x] Código/conteúdo
- [x] Provedor Ollama (sem chave), Anthropic como opção
- [x] Testes do provedor e do ciclo (8 testes)
- [ ] Testes do planejador: não executados aqui, porque a Q11 não estava disponível
- [ ] Execução com um modelo Ollama real: não executada aqui
- [ ] Demo/vídeo (se aplicável)
