# AB2 - Inteligência Artificial

Resolução da Lista 2 de Inteligência Artificial (2026.2), prof. Evandro Costa.

O enunciado completo está em [`docs/Lista 2_IA_Grad_2026_2-1.pdf`](docs/Lista%202_IA_Grad_2026_2-1.pdf).

Cada questão fica em uma pasta própria (`qNN-nome`), com o código, os dados, os testes e um README com a explicação detalhada da solução. Este arquivo dá a visão geral do repositório e explica como preparar o ambiente e rodar cada questão.

## Sumário

- [Estrutura do repositório](#estrutura-do-repositório)
- [Preparação do ambiente](#preparação-do-ambiente)
- [Questões](#questões)
- [Como rodar cada questão](#como-rodar-cada-questão)
- [Testes](#testes)
- [Vídeos de teste](#vídeos-de-teste)
- [Relação entre as questões](#relação-entre-as-questões)
- [Observações e limitações](#observações-e-limitações)

## Estrutura do repositório

```
AB2-ia/
├── docs/                               # enunciado da lista (PDF)
├── q01-ontologia-vs-kg/                # ontologia (Turtle) e grafo (Cypher)
├── q02-knn/                            # KNN sobre a base de crédito da Lista 1
├── q03-eliza/                          # ELIZA em português
├── q04-agentes-peas/                   # taxonomia de agentes e descrições PEAS
├── q05-resumo-llm-inference/           # resumo sobre inferência em LLMs
├── q06-fuzzy/                          # sistema fuzzy de Mamdani (scikit-fuzzy)
├── q07-cbr-medico/                     # diagnóstico médico baseado em casos (CBR)
├── q08-rede-bayesiana/                 # diagnóstico médico com rede bayesiana (pgmpy)
├── q09-ontologia-recomendacao/         # recomendação de filmes com OWL 2 (Owlready2 + HermiT)
├── q10-busca-rotas/                    # BFS, DFS, UCS e A* em um grafo de entregas
├── q11-agentes-classico-vs-llm/        # agente clássico vs. agente baseado em LLM
├── q12-agente-llm/                     # agente de planejamento com LLM e ferramentas
├── q13-transformers/                   # ensaio/notebook sobre a arquitetura Transformer
├── q14-knowledge-graph/                # pesquisa e implementação de grafo de conhecimento
├── q15-owl-protege/                    # ontologia OWL 2 de um departamento universitário
├── requirements.txt
└── README.md
```

## Preparação do ambiente

Requisitos gerais:

- **Python 3.10 ou mais recente** (os códigos foram testados com Python 3.13).
- **Java** (JDK/JRE 11 ou mais recente) para as questões 9 e 15, porque o reasoner HermiT usado pelo Owlready2 roda em Java.
- **Neo4j** apenas se quiser executar os scripts Cypher das questões 1 e 14. Não é obrigatório para o resto.
- **Chave da API da Anthropic** apenas para executar o agente da questão 12 de verdade. Os testes dessa questão não precisam da chave.

Criar e ativar um ambiente virtual e instalar as dependências (PowerShell, na raiz do repositório):

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

No Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

O `requirements.txt` não inclui `pytest` nem `jupyter`. Eles só são necessários para os testes da questão 6 e para abrir os notebooks das questões 13 e 15:

```powershell
python -m pip install pytest jupyter
```

Bibliotecas principais usadas no projeto:

| Biblioteca | Usada em |
|---|---|
| `scikit-fuzzy`, `numpy`, `matplotlib` | Q6 |
| `pgmpy`, `networkx`, `matplotlib` | Q8 |
| `owlready2` | Q9, Q15 |
| `anthropic` | Q12 |
| `numpy`, `pandas`, `matplotlib` | Q13, Q15 |
| `neo4j` (opcional) | Q14 |
| Somente biblioteca padrão | Q2, Q3, Q7, Q10, Q11, Q14 |

## Questões

| Nº | Pasta | Tema | Tipo de entrega |
|---|---|---|---|
| 1 | [`q01-ontologia-vs-kg`](q01-ontologia-vs-kg) | Ontologias vs. grafos de conhecimento | Texto + `filmes.ttl` + `grafo.cypher` |
| 2 | [`q02-knn`](q02-knn) | KNN sobre as 30 instâncias da Lista 1 | Código + testes |
| 3 | [`q03-eliza`](q03-eliza) | Chatbot ELIZA | Código + testes |
| 4 | [`q04-agentes-peas`](q04-agentes-peas) | Taxonomia de agentes e PEAS | Texto |
| 5 | [`q05-resumo-llm-inference`](q05-resumo-llm-inference) | Resumo do vídeo sobre inferência em LLMs | Texto |
| 6 | [`q06-fuzzy`](q06-fuzzy) | Sistema fuzzy (Mamdani) | Código + testes |
| 7 | [`q07-cbr-medico`](q07-cbr-medico) | Diagnóstico médico baseado em casos | Código + testes + relatório |
| 8 | [`q08-rede-bayesiana`](q08-rede-bayesiana) | Diagnóstico médico com rede bayesiana | Código + testes + relatório |
| 9 | [`q09-ontologia-recomendacao`](q09-ontologia-recomendacao) | Recomendação de filmes com OWL 2 | Código + `.owl` + testes + relatório |
| 10 | [`q10-busca-rotas`](q10-busca-rotas) | Busca de rotas (BFS, DFS, UCS, A*) | Código + testes |
| 11 | [`q11-agentes-classico-vs-llm`](q11-agentes-classico-vs-llm) | Agente clássico vs. agente com LLM | Código + testes + texto |
| 12 | [`q12-agente-llm`](q12-agente-llm) | Agente baseado em LLM | Código + testes |
| 13 | [`q13-transformers`](q13-transformers) | Arquitetura Transformer | Notebook |
| 14 | [`q14-knowledge-graph`](q14-knowledge-graph) | Knowledge Graph | Pesquisa + código + testes |
| 15 | [`q15-owl-protege`](q15-owl-protege) | Aplicação com ontologia OWL 2 | Notebook + `.owl` |

### Q1 - Ontologias vs. grafos de conhecimento

Compara sistemas baseados em ontologias e sistemas baseados em grafos de conhecimento usando recomendação de filmes como exemplo. Mostra o mapeamento de uma ontologia OWL para um *property graph*: classes viram labels, indivíduos viram nós, propriedades de objeto viram relacionamentos e propriedades de dados viram atributos dos nós.

- `filmes.ttl`: ontologia em RDF/Turtle, para abrir no Protégé. Com o reasoner ligado, o filme `Matrix` é classificado como `FilmeDeAcao` sem que esse tipo esteja declarado nele.
- `grafo.cypher`: o mesmo exemplo em Cypher, com a carga dos dados, a inferência feita de forma explícita (no grafo a regra precisa ser escrita como consulta) e consultas de conferência.

### Q2 - KNN

Aplica o KNN à base de risco de crédito da Lista 1 (30 exemplos, 6 atributos categóricos, classes Alto/Moderado/Baixo). Como os atributos são categóricos, a distância usada é a de Hamming (número de atributos diferentes). O programa mostra uma classificação passo a passo, com os vizinhos e o voto, e faz validação *leave-one-out* para vários valores de k. O melhor resultado foi k = 9, com 20 de 30 acertos (66,7%). O README da questão discute por que esse número é otimista e compara o resultado com as árvores de decisão da Lista 1.

### Q3 - ELIZA

Implementação reduzida do ELIZA em português, seguindo a ideia do programa original de Weizenbaum (1966):

- palavras-chave com prioridade: a palavra de maior prioridade encontrada na frase define a regra usada;
- regras de decomposição e remontagem: a frase é quebrada em partes e um trecho dela é reaproveitado na resposta;
- troca de pronomes (por exemplo, "eu" vira "você", "meu" vira "seu");
- rodízio entre respostas da mesma regra, para não repetir sempre a mesma frase;
- memória: algumas falas do usuário são guardadas e usadas depois, quando nenhuma palavra-chave é encontrada.

A conversa termina com `tchau` ou `adeus`.

### Q4 - Agentes e PEAS

Duas aplicações para cada uma das cinco categorias de agentes do Russell & Norvig (cap. 2), cada uma com descrição PEAS e propriedades do ambiente (observável, determinístico, episódico, estático, discreto, agente único):

| Categoria | Aplicações |
|---|---|
| Reativo simples | Termostato; filtro de spam por palavras-chave |
| Baseado em modelo | Aspirador robô com mapa; monitor de paciente em UTI |
| Baseado em objetivo | Roteador de entregas; robô de armazém |
| Baseado em utilidade | Assistente de planejamento acadêmico; carro autônomo |
| Com aprendizagem | Filtro de spam com Naive Bayes; analista de risco de crédito |

### Q5 - Inferência em LLMs

Resumo estendido do vídeo indicado no enunciado, em [`resumo-inferencia-llm.md`](q05-resumo-llm-inference/resumo-inferencia-llm.md). Trata do motor de inferência, tokenização, uso de GPU, *continuous batching*, fases de *prefill* e *decode*, cache KV e das métricas TTFT (tempo até o primeiro token) e ITL (tempo entre tokens).

### Q6 - Sistema fuzzy

Sistema de Mamdani que calcula a prioridade de uma atividade (0 a 100) a partir de três entradas:

| Variável | Universo | Termos |
|---|---|---|
| Prazo (horas) | 0 a 72 | urgente, próximo, folgado |
| Importância | 0 a 10 | baixa, média, alta |
| Esforço (minutos) | 0 a 180 | pequeno, médio, grande |
| Prioridade (saída) | 0 a 100 | baixa, média, alta |

Usa funções trapezoidais nos extremos e triangulares no meio, AND pelo mínimo, agregação pelo máximo e defuzzificação pelo centroide. Além da versão com o `ControlSystem` do scikit-fuzzy, o módulo faz a inferência "à mão" (`inferencia_manual`), etapa por etapa, e os testes conferem que as duas dão o mesmo resultado. Há funções para gerar os gráficos das funções de pertinência, da agregação e da superfície de controle (salvos em `q06-fuzzy/figs/`).

### Q7 - Diagnóstico médico baseado em casos (CBR)

Base com 20 casos fictícios e cinco doenças (gripe, dengue, pneumonia, enxaqueca e gastrite), em `data/casos_medicos.csv`. Cada caso tem sintomas, diagnóstico e tratamento. O sistema implementa o ciclo completo:

- **Retrieve**: calcula a similaridade entre o paciente e cada caso da base e mostra os mais parecidos;
- **Reuse**: propõe o diagnóstico e o tratamento a partir dos casos recuperados;
- **Revise**: no modo interativo, o usuário confirma ou corrige o diagnóstico;
- **Retain**: o caso confirmado pode ser gravado na base.

O README da questão traz a descrição da base, a representação dos casos, a fórmula de similaridade, exemplos de consultas e uma avaliação *leave-one-out*.

### Q8 - Rede bayesiana

Rede com 17 variáveis feita com `pgmpy`: faixa etária (causa), doença (nó principal, com as mesmas cinco doenças da Q7), duração dos sintomas e 14 sintomas observáveis. O README explica cada variável, as dependências, as independências condicionais, as hipóteses e as tabelas de probabilidade (CPTs). São quatro experimentos:

1. diagnóstico a partir de febre, tosse e dor muscular (o exemplo do enunciado);
2. atualização do diagnóstico conforme os sintomas vão sendo incluídos;
3. comparação entre conjuntos de evidências diferentes;
4. efeito da faixa etária com os mesmos sintomas.

O modelo é salvo em `data/diagnostico.bif`, que também abre em Netica ou GeNIe, e o desenho da rede fica em `figuras/rede_bayesiana.png`. As probabilidades são ilustrativas, definidas para fins didáticos.

### Q9 - Recomendação com ontologia OWL 2

Ontologia de filmes feita com Owlready2, com 26 classes, 18 propriedades (13 de objeto e 5 de dados), hierarquia de classes, restrições, axiomas e 80 indivíduos. O reasoner HermiT classifica os indivíduos, descobre relações implícitas e verifica a consistência (os testes incluem um caso propositalmente inconsistente). O recomendador usa o resultado do reasoner para sugerir filmes a quatro perfis de usuário (Ana, Bruno, Carla e Diego) e mostra a justificativa de cada recomendação. A ontologia gerada fica em `data/filmes.owl` e pode ser aberta no Protégé.

### Q10 - Busca de rotas

Formulação do problema e execução de BFS, DFS, UCS e A* no grafo do enunciado, de A até I:

| Algoritmo | Rota | Custo (min) | Nós expandidos |
|---|---|---|---|
| BFS | A-B-C-F-I | 15 | 8 |
| DFS | A-B-C-F-E-D-G-H-I | 29 | 8 |
| UCS | A-B-E-F-I | 13 | 8 |
| A* | A-B-E-F-I | 13 | 6 |

O enunciado escreve "Busca em Profundidade (BFS)". Como há essa ambiguidade, foram feitas as duas buscas (largura e profundidade). O programa mostra a ordem de expansão, a tabela de g(n), h(n) e f(n) do A* e verifica se a heurística é admissível e consistente.

Na versão modificada, o estado passa a ser `(nó atual, conjunto de obrigatórios já visitados)`. A melhor rota que passa por D e F antes de I é A → D → E → F → I, com custo 14. Um teste por força bruta confirma que não existe rota válida mais barata.

### Q11 - Agente clássico vs. agente com LLM

Usa o cenário do professor com quatro atividades entre 14h e 18h. O lado clássico é um agente baseado em utilidade que testa todos os planos possíveis, descarta os que violam as restrições e escolhe o de maior utilidade:

- caso base: A (14h-15h30), C (16h-17h), D (17h-18h). B não é feita porque precisa de 120 minutos seguidos e o maior bloco livre tem 30 minutos; o próprio planejador gera essa justificativa;
- variante com B divisível: A, B (15h30-16h), C, B (17h-18h). D fica para depois.

O texto compara as duas abordagens e responde à pergunta do enunciado: o LLM ajuda a interpretar pedidos em linguagem natural e a explicar o plano, mas o cálculo do plano e a verificação das restrições continuam precisando de um mecanismo explícito. O arquivo `demo_hibrido.py` mostra essa divisão sem chamar nenhum modelo.

### Q12 - Agente baseado em LLM

Assistente que recebe pedidos em linguagem natural e usa o modelo Claude para decidir quais ferramentas chamar. As ferramentas reaproveitam o planejador da Q11:

| Ferramenta | O que faz |
|---|---|
| `consultar_agenda` | Retorna as atividades e a janela de tempo |
| `planejar` | Chama a busca exata da Q11 (divisão só para a correção de trabalhos, se pedida) |
| `verificar_plano` | Rejeita sobreposições, horários fora da janela e outras violações |
| `calcular_utilidade` | Calcula a utilidade de um plano válido |

- **Interface**: o usuário escreve o pedido em português e recebe a resposta também em texto.
- **Inferência**: o LLM interpreta o pedido e escolhe as ferramentas; o plano em si vem do planejador determinístico.
- **Explicabilidade**: a resposta vem acompanhada do registro das ferramentas chamadas e dos resultados, e o agente só aceita uma resposta final se o plano passou pelo verificador.

A função que chama o LLM pode ser substituída por uma função falsa, e é assim que os testes rodam sem chave e sem internet.

### Q13 - Transformers

Notebook que explica o Transformer de ponta a ponta com um exemplo pequeno: tokenização, embeddings, codificação posicional, atenção, encoder, decoder com máscara causal e geração de tokens. Os cálculos são feitos com NumPy e pesos aleatórios, só para mostrar as contas e os formatos das matrizes. Nenhum modelo é treinado ou baixado.

### Q14 - Knowledge Graph

Três partes:

1. Pesquisa em [`pesquisa_knowledge_graph.md`](q14-knowledge-graph/pesquisa_knowledge_graph.md) sobre representação, inferência e aprendizagem em grafos de conhecimento, com uma aplicação comentada (o Knowledge Graph da busca do Google).
2. Implementação em Python puro de um grafo de filmes (mesmo domínio da Q9), com regras de inferência, explicação de cada fato inferido e recomendação por caminhos no grafo. As recomendações saem iguais às da Q9, e isso é verificado em teste.
3. Exportação do grafo para Cypher (`python kg.py --cypher`), para carregar no Neo4j.

### Q15 - Ontologia OWL 2 (Protégé)

Ontologia de um departamento universitário (professores, alunos, disciplinas, projetos e laboratórios). O notebook define classes, propriedades, axiomas e indivíduos, roda o reasoner HermiT, faz consultas, mostra a detecção de inconsistências e discute a hipótese do mundo aberto. A ontologia serializada está em `universidade.owl` e pode ser aberta no Protégé para rodar o reasoner por lá também.

## Como rodar cada questão

Alguns programas devem ser executados dentro da pasta da questão, porque leem arquivos de `data/` com caminho relativo. Os comandos abaixo já levam isso em conta. Em Linux/macOS, troque `python` por `python3` e `\` por `/`.

```powershell
# Q2 - KNN
cd q02-knn
python knn.py
cd ..

# Q3 - ELIZA (na raiz)
python q03-eliza\eliza.py

# Q6 - Fuzzy (na raiz)
python q06-fuzzy\fuzzy_prioridade.py

# Q7 - CBR
cd q07-cbr-medico
python cbr.py                # demonstração com duas consultas e a avaliação (não grava nada)
python cbr.py --interativo   # consulta interativa; pode gravar o caso na base
cd ..

# Q8 - Rede bayesiana
cd q08-rede-bayesiana
python bn_diagnostico.py
cd ..

# Q9 - Ontologia de filmes (precisa de Java)
cd q09-ontologia-recomendacao
python ontologia_filmes.py   # monta a ontologia, salva data/filmes.owl e mostra as inferências
python recomendador.py       # recomendações para os quatro usuários
cd ..

# Q10 - Busca de rotas
cd q10-busca-rotas
python busca_rotas.py
cd ..

# Q11 - Agente clássico vs. LLM
cd q11-agentes-classico-vs-llm
python planejador.py
python demo_hibrido.py
cd ..

# Q12 - Agente com LLM (na raiz, precisa da chave)
$env:ANTHROPIC_API_KEY = "sua-chave"
python q12-agente-llm\agente_llm.py

# Q14 - Knowledge Graph
cd q14-knowledge-graph
python kg.py
python kg.py --cypher        # gera data/grafo_filmes.cypher
cd ..
```

Questões que não são scripts:

- **Q1**: abrir `q01-ontologia-vs-kg/filmes.ttl` no Protégé e iniciar um reasoner; para o grafo, executar as seções de `grafo.cypher` no Neo4j Browser, na ordem descrita no README da questão.
- **Q4 e Q5**: só leitura (`q04-agentes-peas/README.md` e `q05-resumo-llm-inference/resumo-inferencia-llm.md`).
- **Q13 e Q15**: notebooks. Abrir com Jupyter ou com a extensão Jupyter do VS Code e executar as células em ordem:

```powershell
python -m jupyter notebook q13-transformers\questao_13.ipynb

cd q15-owl-protege
python -m jupyter notebook questao_15.ipynb
```

A chave da API da Q12 deve ficar só na variável de ambiente. Não grave a chave em nenhum arquivo do repositório (o `.gitignore` já ignora `.env`).

## Testes

Cada questão com código tem seus próprios testes. A maioria usa `unittest` e roda dentro da pasta da questão:

```powershell
cd q02-knn;                     python -m unittest -v; cd ..
cd q07-cbr-medico;              python -m unittest -v; cd ..
cd q08-rede-bayesiana;          python -m unittest -v; cd ..
cd q09-ontologia-recomendacao;  python -m unittest -v; cd ..
cd q10-busca-rotas;             python -m unittest -v; cd ..
cd q11-agentes-classico-vs-llm; python -m unittest -v; cd ..
cd q14-knowledge-graph;         python -m unittest -v test_kg.py; cd ..
```

Q3 e Q12 rodam a partir da raiz:

```powershell
python -m unittest discover -s q03-eliza -p "test_*.py" -v
python -m unittest discover -s q12-agente-llm -p "test_*.py" -v
```

A Q6 usa `pytest`:

```powershell
python -m pytest -q q06-fuzzy\test_fuzzy_prioridade.py
```

| Questão | Testes | O que cobrem |
|---|---|---|
| Q2 | 14 | Integridade da base, distância, ordenação, desempates e validação |
| Q3 | - | Escolha de resposta, troca de pronomes, memória e encerramento |
| Q6 | - | Inferência automática igual à manual, limites da saída, regras de esforço, entradas inválidas |
| Q7 | 19 | Similaridade, recuperação, diagnóstico, revisão e gravação de casos |
| Q8 | 16 | Estrutura da rede, CPTs válidas e resultados dos experimentos |
| Q9 | 15 | Classes inferidas, relações implícitas, recomendações e detecção de inconsistência |
| Q10 | 18 | Ordem de expansão, rotas, g/h/f, admissibilidade, consistência e força bruta da versão modificada |
| Q11 | - | Plano ótimo, variante, verificador e ferramenta |
| Q12 | - | Planejador reaproveitado, ciclo do agente e tratamento de erros (sem chamar a API) |
| Q14 | 18 | Regras de inferência, explicações e recomendações iguais às da Q9 |

Os testes da Q9 precisam de Java instalado, por causa do HermiT.

## Vídeos de teste

[Acessar os vídeos de teste das atividades](https://drive.google.com/drive/folders/10fJlAHI5tzeGQvnkUlUCYc-_-mj1K1vr?usp=sharing).

## Relação entre as questões

Algumas questões foram feitas sobre o mesmo domínio para que os resultados pudessem ser comparados:

- **Q7 e Q8** usam as mesmas cinco doenças e os mesmos sintomas. Dá para comparar o diagnóstico por similaridade de casos com o diagnóstico probabilístico.
- **Q1, Q9 e Q14** usam recomendação de filmes. A Q1 compara ontologia e grafo na teoria, a Q9 implementa a versão com OWL e reasoner, e a Q14 implementa a versão com grafo e regras, chegando às mesmas recomendações.
- **Q10 e Q11** usam busca em espaço de estados; a formulação da Q11 segue o mesmo raciocínio da Q10.
- **Q11 e Q12** usam o mesmo cenário de planejamento. A Q12 reaproveita o planejador e o verificador da Q11 como ferramentas do agente com LLM.
- **Q4 e Q11** usam a mesma taxonomia de agentes do Russell & Norvig.
