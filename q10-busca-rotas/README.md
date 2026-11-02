# Q10: Planejamento de rotas para entregas urbanas

Questão 10 da Lista 2 (AB2), IA PPGI 2026.2, prof. Evandro Costa.

Um agente precisa levar uma entrega do centro de distribuição **A** até o destino **I**, em um mapa de nove localidades, minimizando o tempo de deslocamento. A questão pede a formulação do problema, quatro algoritmos de busca (BFS, DFS, UCS e A*), uma comparação entre eles e uma versão modificada em que o entregador precisa passar por **D** e **F** antes de chegar a **I**.

## Como rodar

Só a biblioteca padrão do Python 3 (testado com Python 3.13). Não há dependências.

```bash
python3 busca_rotas.py          # imprime todas as execuções, a comparação e a versão modificada
python3 -m unittest -v          # roda os 18 testes automatizados
```

## Arquivos

| Arquivo | Conteúdo |
|---|---|
| `busca_rotas.py` | Formulação, algoritmos (BFS, DFS, UCS, A*), verificação da heurística e saída formatada |
| `test_busca_rotas.py` | Testes: valores esperados, ordem de expansão, valores de g/h/f, admissibilidade e consistência, e uma checagem por força bruta da versão modificada |
| `README.md` | Este arquivo, com as respostas da questão |

---

## 1. Formulação do problema

- **Estados:** os nós do grafo, `{A, B, C, D, E, F, G, H, I}`.
- **Estado inicial:** `A`.
- **Ações:** ir para um vizinho do nó atual, pelo trecho que os liga.
- **Função de transição:** `resultado(n, ir para v) = v`.
- **Teste de objetivo:** o estado atual é `I`.
- **Função de custo:** o tempo do trecho, em minutos. O custo de uma rota é a soma dos trechos.

O grafo é não direcionado e tem 9 nós e 12 trechos.

## 2. Busca não informada

Convenções usadas em todas as buscas:
- O teste de objetivo é feito quando o nó sai da fronteira (é expandido).
- Vizinhos são considerados em ordem alfabética. Isso decide os empates.
- Há um conjunto de nós explorados, para não repetir estados.
- "Nós expandidos" não conta o nó objetivo.

### BFS (busca em largura)

O enunciado chama de "Busca em Profundidade (BFS)", mas **BFS é busca em largura**. Resolvi as duas (esta e a DFS abaixo) e registro a diferença aqui.

- **Ordem de expansão:** A → B → D → C → E → G → F → H
- **Rota:** A → B → C → F → I
- **Custo:** 15 min (4 trechos)

O BFS minimiza o número de trechos, não o tempo. A rota A → B → E → F → I também tem 4 trechos e custa 13 min. A escolha de A → B → C → F → I vem da ordem alfabética.

### DFS (busca em profundidade)

- **Ordem de expansão:** A → B → C → F → E → D → G → H
- **Rota:** A → B → C → F → E → D → G → H → I
- **Custo:** 29 min (8 trechos)

A DFS segue um caminho até o fim antes de voltar. Ela encontra uma rota válida, mas muito mais longa que a ótima.

### UCS (busca de custo uniforme)

Sempre expande o nó com menor custo acumulado g(n).

- **Ordem de expansão (com g):** A(0) → D(3) → B(4) → E(6) → G(9) → C(9) → F(9) → H(11)
- **Rota:** A → B → E → F → I
- **Custo:** 13 min

Os empates de custo (C, F e G com g = 9) são resolvidos pela ordem de inserção na fila. Por isso G aparece antes de C e F. A rota e o custo não dependem dessa escolha.

Há outra rota de custo 13 (A → B → E → H → I). O UCS encontrou a que passa por F, que entrou na fila primeiro.

## 3. Busca informada: A*

Função de avaliação: `f(n) = g(n) + h(n)`, com a heurística do enunciado.

| Nó expandido | g(n) | h(n) | f(n) |
|---|---|---|---|
| A | 0 | 10 | 10 |
| D | 3 | 9 | 12 |
| B | 4 | 8 | 12 |
| E | 6 | 6 | 12 |
| F | 9 | 4 | 13 |
| H | 11 | 2 | 13 |
| I (objetivo) | 13 | 0 | 13 |

- **Ordem de expansão:** A → D → B → E → F → H
- **Rota:** A → B → E → F → I
- **Custo:** 13 min

Quando B é expandido, E é alcançado com g = 6 pelo caminho A → B → E, que é melhor que g = 7 pelo caminho A → D → E. Por isso E entra com g = 6.

## 4. Verificação da heurística

A otimalidade do A* depende da heurística. Ela precisa ser:

- **Admissível:** h(n) ≤ custo real de n até I, para todo n.
- **Consistente:** h(u) ≤ c(u, v) + h(v), para todo trecho u–v.

O código calcula o custo real até I de cada nó com UCS e confere as duas propriedades:

| Nó | h(n) | Custo real até I | h ≤ real? |
|---|---|---|---|
| A | 10 | 13 | sim |
| B | 8 | 9 | sim |
| C | 6 | 6 | sim |
| D | 9 | 11 | sim |
| E | 6 | 7 | sim |
| F | 4 | 4 | sim |
| G | 5 | 5 | sim |
| H | 2 | 2 | sim |
| I | 0 | 0 | sim |

A heurística é admissível e consistente. Por isso o A* é ótimo.

## 5. Comparação

| Algoritmo | Rota | Custo (min) | Nós expandidos | Custo ótimo nesta instância? |
|---|---|---|---|---|
| BFS | A-B-C-F-I | 15 | 8 | não |
| DFS | A-B-C-F-E-D-G-H-I | 29 | 8 | não |
| UCS | A-B-E-F-I | 13 | 8 | sim |
| A* | A-B-E-F-I | 13 | 6 | sim |

Propriedades teóricas:

| Critério | BFS | DFS | UCS | A* |
|---|---|---|---|---|
| Completude (grafo finito, com explorados) | sim | sim | sim | sim |
| Otimalidade em minutos | não | não | sim | sim (h admissível e consistente) |
| Otimalidade em número de trechos | sim | não | não | não necessariamente |
| Usa informação sobre o destino | não | não | não | sim |

**Conclusões:**
- **DFS** tem o pior resultado (29 min). Ela não considera custos nem profundidade, e no pior caso pode explorar o grafo inteiro antes de achar uma rota.
- **BFS** é ótimo em número de trechos, mas o tempo não é esse critério, e por isso chega a 15 min.
- **UCS** é ótimo para custos positivos, mas não usa informação sobre o destino. Ele expande todos os nós com g menor que o custo ótimo (8 nós).
- **A*** chega ao mesmo ótimo que a UCS e expande menos nós (6 contra 8). A heurística direciona a busca para I, e G e C, que a UCS expande, nem chegam a ser expandidos pelo A*.

## 6. Versão modificada: visitar D e F antes de I

O entregador precisa passar por **D** e **F** antes de chegar a **I**, em qualquer ordem.

**Nova representação de estados:** `(nó atual, conjunto dos obrigatórios já visitados)`. Por exemplo, `E{D}` significa "estou em E e já passei por D".

- **Estado inicial:** `(A, {})`.
- **Transição:** ao entrar em um nó, ele é acrescentado ao conjunto se for D ou F.
- **Teste de objetivo:** nó atual é I **e** `{D, F}` já foi visitado.
- **Custo:** o mesmo da versão original.
- **Tamanho do espaço de estados:** no máximo 9 nós × 4 subconjuntos = 36 estados.

A heurística do enunciado depende só do nó, e continua admissível e consistente nesse espaço de estados. Por isso o A* também funciona aqui.

**Resultado (UCS e A* dão o mesmo):**
- **Rota:** A → D → E → F → I
- **Custo:** 14 min (3 + 4 + 3 + 4)

**Por que é ótima:**
- A outra ordem (F antes de D) custa pelo menos 9 (A → B → E → F) + 7 (F → E → D) + 11 (D → E → F → I) = 27 min.
- Na ordem D antes de F, o mínimo é 3 (A → D) + 7 (D → E → F) + 4 (F → I) = 14 min.
- A ordem D → F é, portanto, a melhor. A restrição custa 1 minuto a mais que a rota sem restrição (13 min).

O teste `test_bate_com_forca_bruta` confirma isso de forma independente: enumera todos os passeios de A com custo até 14 e verifica que nenhum com custo menor que 14 satisfaz a restrição.

## 7. Decisões de implementação

- **Passar por I sem parar:** na versão modificada, chegar a I sem ter visitado D e F não é objetivo, e a busca continua a partir de I. Nesta instância, a rota ótima não passa por I antes do fim (o código mostra isso na expansão de I{F} e I{}, que não são solução).
- **Visitar = passar pelo nó:** um nó obrigatório conta como visitado se a rota passa por ele, mesmo sem parar.
- **Ordem dos vizinhos:** alfabética. Outra ordem pode mudar qual rota de mesmo custo é devolvida (BFS e UCS têm empates). O custo ótimo não muda.
- **Estados repetidos:** a busca usa conjunto de explorados. Sem isso, a DFS poderia entrar em ciclos (A-B-E-B-...).

## 8. Limitações

- O grafo é pequeno (9 nós). Para mapas grandes, a UCS e o A* precisariam de estruturas mais eficientes, e a versão modificada cresce com 2^k subconjuntos de k obrigatórios.
- A heurística foi dada pelo enunciado. O código não tenta gerar uma heurística melhor.
- Não há tempo de espera nem janelas de entrega. Isso ficou fora do enunciado.
