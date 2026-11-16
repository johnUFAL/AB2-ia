# Q11: Agente clássico (AIMA) vs. agente baseado em LLM

Questão 11 da Lista 2, IA PPGI 2026.2, prof. Evandro Costa.

> Comparar a concepção clássica de agentes inteligentes (Cap. 2 do Russell & Norvig) com agentes baseados em LLMs, usando um problema de planejamento de atividades com restrições de tempo, recursos e prioridades, e responder: em que situações o agente LLM tem vantagem e quais capacidades ainda dependem de raciocínio, planejamento e verificação explícitos?

## Como rodar

Só a biblioteca padrão do Python 3.10 ou mais recente.
Execute os comandos dentro desta pasta:

```bash
python planejador.py
python demo_hibrido.py
python -m unittest -v
```

## Arquivos

| Arquivo | Conteúdo |
|---|---|
| `planejador.py` | Planejador, verificador independente e a função ferramenta que um LLM chamaria |
| `demo_hibrido.py` | Demonstração do planejador e do verificador com dados definidos no código, não chama um modelo |
| `test_planejador.py` | Testes do plano ótimo, da variante, do verificador e da ferramenta |

---

## 1. O problema

Professor com a janela das 14h às 18h e quatro atividades:

| Atividade | Duração | Prioridade | Prazo |
|---|---|---|---|
| A: Preparar aula de IA | 90 min | Alta | Hoje |
| B: Corrigir trabalhos | 120 min | Média | Amanhã |
| C: Reunião de pesquisa | 60 min | Alta | Hoje, fixa das 16h às 17h |
| D: Revisar artigo | 60 min | Baixa | Próxima semana |

**Leitura que facilita tudo:** a reunião corta a tarde em dois blocos livres, 14h–16h (120 min) e 17h–18h (60 min). Sem dividir atividades, A (90) só cabe no primeiro bloco, B (120) só caberia ocupando o primeiro bloco inteiro, e o segundo bloco só comporta D (60). Como A tem prazo hoje, B não cabe junto.

## 2. Lado clássico: agente baseado em utilidade

### 2.1 PEAS e propriedades do ambiente (AIMA, Cap. 2)

| Elemento | Descrição |
|---|---|
| Performance | Maximizar a utilidade das atividades concluídas, sem violar compromissos fixos nem prazos de hoje |
| Environment | Agenda do professor, janela de 4 h, lista de atividades com duração, prioridade e prazo |
| Actuators | Propor blocos de horário e justificar o que ficou de fora |
| Sensors | A lista de atividades e a janela informadas (neste cenário, dados já estruturados) |

| Propriedade | Classificação | Por quê |
|---|---|---|
| Observável | Totalmente | O cenário fornece durações e prazos como fatos. Na vida real seria parcial: durações são estimativas |
| Determinístico | Sim | Assume que cada atividade dura exatamente o informado |
| Sequencial | Sim | A ordem escolhida ocupa o tempo das demais |
| Estático | Sim durante o planejamento | A agenda não muda enquanto o agente decide |
| Discreto | Sim | Grade de 30 min e conjunto finito de atividades |
| Agente único | Sim | O professor é o usuário, não um agente concorrente |
| Conhecido | Sim | As regras são conhecidas |

Esse é o ambiente "fácil" da taxonomia, e é justamente onde um agente clássico brilha. Isso é relevante para a comparação.

### 2.2 Formulação (mesmo raciocínio da Q10)

- **Estado:** quais atividades já ocupam quais slots de 30 min da janela.
- **Estado inicial:** só o compromisso fixo (C) alocado.
- **Ações:** atribuir cada slot livre a uma atividade móvel ou deixá-lo vazio.
- **Teste de viabilidade (restrições duras):** sem sobreposição, tudo na janela, C às 16h, atividades com prazo hoje concluídas, atividade indivisível iniciada é concluída em bloco contínuo.
- **Função de utilidade:** soma de `peso × fração concluída`, com Alta = 5, Média = 3, Baixa = 1.

### 2.3 Decisões de projeto (e por quê)

| Decisão | Por quê |
|---|---|
| **Busca exaustiva em grade de 30 min**, em vez de A*, CSP ou programação linear | São 6 slots livres e 3 atividades móveis: 4⁶ = 4096 combinações. Testar todas dá otimalidade sem precisar provar que uma heurística é admissível, e o código é curto o bastante para explicar no relatório. **Limite:** cresce exponencialmente com o número de slots. Para uma semana inteira, seria preciso CSP/ILP |
| **Grade única para atividades divisíveis e indivisíveis** | A mesma enumeração atende o caso base e a variante: só muda a regra de viabilidade. Evita dois algoritmos diferentes para comparar |
| **Prazo "hoje" é restrição dura**, não só peso alto | O enunciado diz "priorizar urgentes". Com peso, um plano poderia sacrificar a aula para ganhar utilidade em outra coisa. Como restrição, esse plano nem entra |
| **Divisão só quando explícita** (parâmetro `divisivel`) | O enunciado diz "iniciada deve ser concluída, salvo se o planejamento permitir explicitamente". Por padrão ninguém é divisível, na variante, só B |
| **Desempate por atraso ponderado** | Há 4 planos de utilidade igual. O desempate coloca o que é importante mais cedo, e a aula sai às 14h em vez de às 14h30 |
| **Verificador separado, em minutos e não em slots** | Precisa aceitar planos de qualquer origem. E, sendo outro código, também pegaria um bug do planejador. Os testes confirmam que a saída do planejador passa nele |
| **`Fraction` em vez de `float`** na utilidade | Compara utilidades parciais sem erro de arredondamento mudar o empate |

### 2.4 Resultados

**Caso base (nenhuma atividade divisível):**

| Horário | Atividade |
|---|---|
| 14:00-15:30 | A: Preparar aula de IA |
| 16:00-17:00 | C: Reunião de pesquisa |
| 17:00-18:00 | D: Revisar artigo |

Utilidade 11. Dos 4096 planos testados, só **4 são viáveis**. B não é feita: *"exige 120 min contínuos e o maior bloco livre é de 30 min. Reagendar para amanhã"*. A restrição "justificar o que não foi feito" sai do próprio algoritmo.

**Variante (B divisível em blocos de 30 min):** A 14h–15h30, B 15h30–16h, C, B 17h–18h. B avança 90 de 120 min, D é adiada, utilidade 12,25. Aqui a função de utilidade **decide**: trocar D (Baixa, 60 min) por 90 min de B (Média) rende mais.

**Sensibilidade aos pesos:**

| Pesos (Alta/Média/Baixa) | Caso base | Variante com B divisível |
|---|---|---|
| (5, 3, 1) | A, D | A, B |
| (10, 2, 1) | A, D | A, B |
| (5, 1, 3) | A, D | A, B, D |

No caso base o plano **não depende dos pesos**: as restrições já deixam um único conjunto de atividades viável. Os pesos só importam quando há escolha de verdade, como na variante. Isso evita superestimar a importância dos números que escolhi.

## 3. Lado LLM: o que muda

Um agente baseado em LLM mantém a estrutura percepção → decisão → ação do AIMA, mas o programa-agente é um modelo de linguagem dentro de um laço com ferramentas:

- **Percepções:** o pedido em texto e os resultados das ferramentas.
- **Ações:** texto ou chamadas de ferramenta (neste caso, `planejar`).
- **"Modelo" do mundo, objetivo e utilidade:** ficam implícitos no contexto e no prompt, em vez de explícitos no código.

`demo_hibrido.py` mostra os três papéis que atribuo ao LLM no desenho híbrido:

1. **Interpretar:** converter o pedido ("urgente", "da melhor maneira possível") em JSON estruturado para a ferramenta. O pedido do professor não traz as durações nem a reunião às 16h; o LLM precisa associá-las ao contexto.
2. **Propor/chamar:** acionar o planejador determinístico em vez de resolver de cabeça.
3. **Explicar:** redigir a resposta em português para o professor (papel não executado na demo, fica para a Q12).

E um papel que **não** deve ser do LLM: a **verificação**. A demo submete três planos "de cabeça", escritos à mão como erros plausíveis, ao verificador:

| Plano | Resultado do verificador |
|---|---|
| Prioriza B (2 h) e deixa A para 17h–18h30 | Rejeitado: A ultrapassa a janela das 18h |
| Encaixa tudo com A em 60 min | Rejeitado: B sobrepõe C, e A tem 60 de 90 min |
| Divide a aula para caber | Rejeitado: A e B são indivisíveis |

Os três parecem razoáveis em texto corrido e falham em aritmética de horários. **Isto é uma ilustração, não uma medição:** não rodei nenhum modelo, então não afirmo com que frequência um LLM real erraria este problema.

## 4. Comparação

| Critério | Agente clássico (AIMA) | Agente baseado em LLM |
|---|---|---|
| Entrada | Dados estruturados (precisa de formulário ou parser) | Linguagem natural, inclusive vaga ou incompleta |
| Representação do objetivo | Explícita: função de utilidade e restrições | Implícita no prompt e nos pesos do modelo |
| Decisão | Busca/otimização sobre um modelo formal | Geração de texto condicionada ao contexto |
| Garantias | Viabilidade e otimalidade (aqui, por enumeração) | Nenhuma por construção |
| Reprodutibilidade | Mesma entrada, mesma saída | Pode variar entre execuções |
| Explicabilidade | Rastreável: restrição violada ou utilidade comparada | Justificativa em texto fluente, **não necessariamente** fiel ao processo real |
| Conhecimento de senso comum | Só o que foi codificado | Amplo (ex.: correção de provas é fracionável, aula não) |
| Custo de adaptar a um novo domínio | Alto (reformular o modelo) | Baixo (mudar o prompt/ferramentas) |
| Aritmética, horários, contagem | Exata | Frágil sem ferramenta |
| Ambiente exigido | Bem especificado | Tolera ambiguidade |

## 5. Resposta à questão final

**Quando o LLM oferece vantagem sobre o agente clássico:**

- **Entrada em linguagem natural e objetivos mal especificados.** "Urgente" e "da melhor maneira possível" não são parâmetros. O agente clássico exige que alguém os traduza para pesos e prazos antes; o LLM faz essa tradução.
- **Conhecimento de senso comum que ninguém codificou.** Saber que correção de trabalhos pode ser feita em pedaços e que preparar aula ou reunião não pode, como fizemos manualmente na variante.
- **Ambiente aberto e mudança frequente.** Novos tipos de pedido ("remarque tudo porque a reunião foi cancelada") não exigem reprogramar o modelo.
- **Interação e explicação.** Pedir esclarecimento, negociar, redigir a justificativa na linguagem do usuário.
- **Integração de ferramentas heterogêneas.** Escolher qual ferramenta chamar e com quais argumentos.

**O que ainda depende de mecanismos explícitos:**

- **Satisfação de restrições duras.** Sobreposição, janela de horário e compromisso fixo são aritmética exata. A demo mostra três planos plausíveis que violam isso.
- **Otimalidade e comparação de alternativas.** Escolher entre D e 90 min de B é um problema de otimização. A busca testou os 4096 planos; um LLM "estima" qual parece melhor.
- **Verificação.** Quem checa o plano não deve ser quem o gerou. O verificador é um código separado e pequeno.
- **Auditabilidade e reprodutibilidade.** Em contextos em que a decisão precisa ser reproduzível e rastreável, o núcleo precisa ser determinístico.
- **Explicações fiéis.** O texto de um LLM pode soar convincente sem refletir o cálculo real. A justificativa "B não coube porque o maior bloco livre é 30 min" vem do algoritmo, não de uma narração.

**Síntese:** a divisão natural é o LLM nas pontas (interpretar o pedido e explicar o resultado) e o motor explícito no meio (planejar e verificar). Esta é também a arquitetura planejada para a **Q12**, em que o LLM chamará `ferramenta_planejar`. Em literatura recente há linha de trabalho com essa ideia, o LLM propondo e verificadores externos validando (por exemplo, o *LLM-Modulo* de Kambhampati), e benchmarks de planejamento com LLMs (como o PlanBench). **Citei de memória: confirme as referências antes de usá-las no relatório.**

## 6. Limites deste trabalho

- **Não há agente LLM rodando aqui.** O lado LLM é desenho e ilustração. A integração real, com API e *tool use*, fica para a Q12; só então dá para medir se o modelo erra os horários e com que frequência.
- **Os pesos 5/3/1 são escolha minha**, sem calibração. A tabela de sensibilidade mostra que no caso base não importam, e na variante importam.
- **A comparação usa um ambiente fácil** (determinístico, totalmente observável). Em ambientes parcialmente observáveis, com durações incertas, a vantagem relativa do clássico encolhe e seria preciso modelar a incerteza.
- **A busca exaustiva não escala.** Serve para este problema e serve bem para explicá-lo.

## Status

- [x] Código/conteúdo
- [ ] Relatório (montar a partir deste README)
- [ ] Demo/vídeo (opcional na Q11; a demo principal é a da Q12)
