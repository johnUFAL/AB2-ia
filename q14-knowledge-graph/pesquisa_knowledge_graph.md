# Knowledge Graphs: representação, inferência e aprendizagem

## 1. O que é um Knowledge Graph

Hogan et al. (2021), em um dos surveys sobre o tema, definem um Knowledge Graph como "um grafo de dados destinado a acumular e transmitir conhecimento do mundo real", em que os nós representam entidades de interesse e as arestas representam relações potencialmente diferentes entre elas. A ideia central é tratar fatos como conexões entre coisas, e não como linhas de uma tabela ou palavras em um texto.

Um exemplo prático de escala: em 16 de maio de 2012, o Google anunciou o seu Knowledge Graph com a frase "things, not strings" (coisas, não strings). No lançamento, a empresa dizia conter mais de 500 milhões de objetos e mais de 3,5 bilhões de fatos e relações entre eles.

## 2. Representação de conhecimento

**Triplas.** A unidade básica é a tripla (sujeito, predicado, objeto). Por exemplo, `(interestelar, dirigidoPor, christopher_nolan)`. O modelo RDF, padronizado pelo W3C, usa triplas com identificadores globais (URIs). O modelo de *property graph*, usado pelo Neo4j, guarda propriedades diretamente nos nós e nas arestas, o que costuma ser mais cômodo para consultas, mas não tem a mesma semântica formal do RDF.

**Esquema e ontologia.** Além dos fatos, um KG pode descrever o vocabulário: hierarquia de classes (`Diretor é subclasse de Pessoa`), domínio e contradomínio de relações, propriedades especiais (inversa, simétrica, funcional) e classes definidas por condição (`FilmeDeTerror` é o conjunto de filmes com gênero Terror). A linguagem padrão para isso é o OWL, usado na Q9 deste trabalho.

**Mundo aberto e mundo fechado.** Na lógica de OWL, se um fato não está no grafo, ele não é necessariamente falso: pode apenas não ser conhecido (mundo aberto). Em bancos de dados e na maioria dos sistemas de regras, o que não está registrado é considerado falso (mundo fechado). Essa diferença muda o resultado das consultas e precisa ser escolhida conscientemente. Na Q14 usei mundo fechado, pois o catálogo é a lista completa de filmes do sistema.

## 3. Inferência

**Encadeamento para frente (forward chaining).** Aplica-se cada regra a todos os fatos conhecidos, adiciona os fatos novos e repete até não surgir nada novo (ponto fixo). Para regras sem criação de objetos, o processo termina, porque o número de triplas possíveis é finito. No `kg.py`, a regra "gosta de Terror ⇒ é fã de Terror" é aplicada assim.

**Encadeamento para trás (backward chaining).** Parte-se de uma pergunta e procura-se regra e fatos que a justifiquem, como em Prolog. É mais eficiente quando só se quer responder a algumas consultas, mas não materializa o grafo inferido.

**Lógicas de descrição.** O OWL 2 DL é baseado em lógicas de descrição. Raciocinadores como o HermiT (usado na Q9) verificam consistência, classificam indivíduos em classes definidas e inferem valores de propriedades. Essas lógicas são decidíveis, mas o custo cresce rápido com a expressividade. Regras simples (como as da Q14) são mais rápidas e mais fáceis de explicar, mas não cobrem tudo que o OWL cobre.

**Explicação.** Um ponto importante, e pouco mencionado, é a procedência (*provenance*): para cada fato inferido, guardar qual regra o gerou e quais premissas foram usadas. Isso permite responder "por que o sistema acha que Ana é fã de Terror?" Na Q14, a função `explicar` mostra essa cadeia:

```
ana tipo FanDeTerror   [inferida por: definida FanDeTerror (gostaDeGenero Terror)]
  ana gostaDeGenero Terror   [afirmada]
```

Para recomendadores, isso é valioso, porque a justificativa acompanha a sugestão. A limitação é que as regras são escritas à mão e precisam ser coerentes entre si. Além disso, remover um fato exige recalcular o que dele dependia, já que as inferências não se desfazem sozinhas.

## 4. Aprendizagem

Além de inferir a partir de regras, há um conjunto de técnicas que aprende a partir do próprio grafo.

**Embeddings de grafo.** Cada entidade e cada relação recebe um vetor, e uma função de pontuação diz quão plausível é uma tripla. O TransE (Bordes et al., NIPS 2013) assume que, para uma tripla verdadeira `(h, r, t)`, vale aproximadamente `h + r ≈ t`. É simples e eficiente, mas modela mal relações simétricas e relações do tipo um-para-muitos. O RotatE (Sun et al., arXiv 2019, publicado na ICLR 2019) representa a relação como uma rotação em um espaço complexo, e consegue modelar simetria, inversão e composição de relações.

**Previsão de ligações (link prediction).** Usa os embeddings para completar triplas que faltam. Por exemplo, prever `(ana, gostaDeDiretor, ?)` a partir de filmes parecidos que ela viu. É a forma mais comum de transformar um KG em recomendador.

**Redes neurais em grafos.** O R-GCN (Schlichtkrull et al., ESWC 2018) agrega informação dos vizinhos de cada nó, separando os tipos de aresta. Serve para classificar nós e prever ligações. Essa referência é citada de memória e não foi conferida nesta pesquisa.

**Aprendizagem e inferência juntas.** Regras podem ser aprendidas a partir do grafo, por exemplo por mineração de regras, e depois usadas como restrição sobre os embeddings. Também há uso recente de KGs para recuperar fatos antes de gerar texto com modelos de linguagem (RAG com grafos). Esse ponto ainda está em evolução e não aprofundei.

## 5. Aplicação comentada: busca do Google

O Google Knowledge Graph alimenta os painéis de informação que aparecem nos resultados de busca, com dados sobre pessoas, lugares e coisas. O anúncio de 2012 descreve a ideia de entender entidades do mundo real e suas relações, mas **não detalha o mecanismo interno de inferência**, que não é público. Portanto, não descreverei como ele é implementado por dentro.

Para mostrar como a inferência funciona em um sistema desse tipo, uso o grafo de filmes deste trabalho, que segue o mesmo princípio em escala pequena. Ao perguntar "Ana gosta de filmes de Terror?", o sistema não tem essa resposta escrita. Ele aplica duas etapas:

1. Ana tem a aresta afirmada `gostaDeGenero → Terror`.
2. A regra "quem gosta de Terror é fã de Terror" gera `ana tipo FanDeTerror`.

Com a mesma lógica, a recomendação de O Iluminado para Ana sai de um caminho no grafo: `ana → gostaDeGenero → Terror ← temGenero ← o_iluminado`. Cada motivo exibido ao usuário é um caminho que pode ser verificado.

Essa é a parte mais útil de um KG para uma aplicação: a resposta vem com o caminho que a justifica, e não só com um número.

## 6. Referências

- Hogan, A. et al. *Knowledge Graphs*. ACM Computing Surveys, 54(4), art. 71, 2021. (Verificado: definição citada no início da seção 1.)
- Google. *Introducing the Knowledge Graph: things, not strings*. Blog oficial, 16 de maio de 2012. (Verificado: números e data.)
- Bordes, A. et al. *Translating Embeddings for Modeling Multi-relational Data*. NIPS 2013. (Verificado: NIPS 26.)
- Sun, Z. et al. *RotatE: Knowledge Graph Embedding by Relational Rotation in Complex Space*. arXiv:1902.10197, 2019. (Verificado: arXiv. Venue ICLR 2019 citada de memória.)
- Schlichtkrull, M. et al. *Modeling Relational Data with Graph Convolutional Networks*. ESWC 2018. (Citada de memória, não conferida.)
