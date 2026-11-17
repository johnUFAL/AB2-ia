# Q12: Agente de planejamento baseado em LLM

Implementa um assistente que interpreta pedidos em linguagem natural, chama
ferramentas determinísticas para planejar e verificar a agenda e retorna uma
resposta com o registro das ações. O planejador e as regras de validação são
reutilizados de [Q11](../q11-agentes-classico-vs-llm/planejador.py), sem copiar
ou manter uma segunda implementação.

## Como executar

Instale as dependências do projeto e defina `ANTHROPIC_API_KEY`. A chamada à
API só ocorre ao executar o agente:

```powershell
$env:ANTHROPIC_API_KEY = "sua-chave"
python q12-agente-llm\agente_llm.py
```

O modelo utilizado é Claude Opus 5.5. A chave não deve ser gravada nos arquivos
do projeto. Sem uma chave válida, a chamada falha com uma mensagem explícita.

## Ferramentas e verificação

- `consultar_agenda` retorna os dados definidos no planejador de Q11.
- `planejar` chama a busca exata de Q11; a divisão só é permitida para a
  correção de trabalhos quando solicitada.
- `verificar_plano` rejeita sobreposições, horários fora da janela e demais
  violações antes que uma resposta final seja aceita.
- `calcular_utilidade` calcula o valor apenas para planos válidos.

O ciclo do agente aceita uma função LLM injetada, então pode ser testado sem
chave ou acesso à API.

## Testes

Na raiz do repositório:

```powershell
python -m unittest discover -s q12-agente-llm -p "test_*.py" -v
```

## Arquivos

| Arquivo | Conteúdo |
|---|---|
| `agente_llm.py` | Ferramentas, ciclo do agente e integração com a API Anthropic |
| `test_agente_llm.py` | Testes do planejador reutilizado, do ciclo e dos erros |

## Status

- [x] Código/conteúdo
- [x] Testes automatizados
- [x] Relatório (este README)
- [ ] Demo/vídeo (se aplicável)
