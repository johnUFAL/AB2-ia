# Q1: Ontologias vs. Grafos de Conhecimento

Questão 1 da Lista 2, IA PPGI 2026.2, prof. Evandro Costa.

> "Faça um comparativo entre essas duas abordagens (Sistemas baseados em Ontologias e Sistemas baseados em Grafos de Conhecimento), considerando um exemplo de aplicação de sua escolha. Mostre, com a ajuda de um exemplo, como se faz um mapeamento de uma ontologia em um grafo de conhecimento."

## O que é

Este trabalho compara sistemas baseados em ontologias e grafos de conhecimento usando **recomendação de filmes** como domínio. Também apresenta um exemplo de ontologia OWL em Turtle e o mapeamento de seus indivíduos e relações para um *property graph* no Neo4j.

Há dois arquivos com funções diferentes: [`filmes.ttl`](filmes.ttl) é a ontologia em RDF/Turtle, para abrir no Protégé; [`grafo.cypher`](grafo.cypher) é o exemplo do grafo em Cypher, a linguagem nativa de consulta do Neo4j. **Não é preciso instalar extensão RDF para executar o arquivo `.cypher` no Neo4j.
## Como rodar

### Ontologia

1. Abra `filmes.ttl` no [Protégé](https://protege.stanford.edu/).
2. Selecione um *reasoner* OWL e inicie.
3. Consulte os tipos inferidos de `Matrix`. O reasoner deve classificar também como `FilmeDeAcao`, embora esse tipo não esteja declarado diretamente no indivíduo.

### Grafo de conhecimento

1. Inicie um banco Neo4j e abra o Neo4j Browser conectado a ele.
2. No editor de consultas, copie e execute somente os comandos da seção **Carga** do arquivo `grafo.cypher`. O resultado deve mostrar o pequeno grafo criado.
3. Copie e execute o comando da seção **Inferência explicitada**.
4. Execute as consultas da seção **Consultas**, uma de cada vez, para conferir os dados e o label `FilmeDeAcao`.

Os comandos estão escritos em Cypher normal; basta colar no editor e pressionar **Run**. O exemplo pressupõe um banco de demonstração vazio. Os comandos `MERGE` permitem repetir a carga sem criar nós ou relações duplicados.

## Decisões tomadas (e por quê)

- **Domínio: filmes.** É familiar e ilustra classes, hierarquia, relações e inferência.
- **Destino do mapeamento: property graph do Neo4j.** Esse formato facilita visualizar entidades e relações e é reutilizável em trabalhos relacionados. Uma alternativa seria mapear a ontologia para RDF e consultar em uma *triple store*; RDF preserva diretamente a forma de triplas, enquanto o exemplo abaixo usa labels, propriedades e tipos de relacionamento do Neo4j.
- **Recorte pequeno.** O exemplo é suficiente para mostrar o mapeamento e o que não é preservado automaticamente, sem pretender modelar todo o domínio de filmes.
- **Semântica não é automática no property graph.** O banco armazena os fatos e executa as consultas; as regras OWL precisam ser traduzidas ou executadas por uma camada de raciocínio separada.

### Regras de mapeamento usadas

| Elemento OWL | Representação no property graph | Observação |
|---|---|---|
| Indivíduo | Nó | `:Matrix` vira um nó com identificador ou propriedade que o identifica. |
| Tipo declarado (`rdf:type`) | Label do nó | `:Matrix a :Filme` vira `:Filme`. |
| `ObjectProperty` | Tipo de relacionamento | `:dirigiu` vira `:DIRIGIU`. |
| `DatatypeProperty` | Propriedade do nó | `:anoLancamento 1999` vira `anoLancamento: 1999`. |
| `subClassOf` | Labels adicionais ou relacionamento de esquema | `Diretor` também recebe o label `Pessoa`; essa hierarquia precisa ser materializada ou consultada à parte. |
| `inverseOf` | Um relacionamento consultado em qualquer direção, ou duas direções materializadas | O Neo4j não aplica automaticamente a semântica OWL de inversa. |
| `domain` / `range` | Restrição ou documentação da aplicação | Não são inferidos automaticamente pelo modelo de property graph. |
| Restrições e axiomas, como `equivalentClass` com `hasValue` | Regra, consulta de inferência/materialização ou validação externa | Não têm equivalente semântico automático no mapeamento mostrado. |

O mapeamento é uma escolha de representação, não uma conversão sem perdas, o property graph mantém os fatos selecionados, mas não carrega por si só toda a semântica lógica da ontologia.

## Resultados

### Comparação

| Critério | Sistema baseado em ontologia (OWL) | Sistema baseado em grafo de conhecimento |
|---|---|---|
| Foco | Vocabulário, conceitos, relações e axiomas com semântica formal; costuma explicitar o esquema (TBox) e os fatos (ABox). | Representação e integração de fatos sobre entidades e suas relações; pode usar RDF ou property graph. |
| Fundamento | Lógica de descrição e semântica formal do OWL. | Depende do modelo: RDF tem semântica formal própria; property graphs como o Neo4j normalmente usam semântica operacional de nós, arestas e propriedades. |
| Informação ausente | Em OWL, em geral vale a hipótese de mundo aberto: não afirmar um fato não significa que ele seja falso. | Em aplicações de consulta, é comum tratar como não conhecido/não retornado o que não está armazenado; isso não é uma regra universal para todo grafo de conhecimento. |
| Raciocínio e consulta | Um reasoner pode classificar indivíduos, propagar consequências e detectar inconsistências a partir dos axiomas. | Consultas percorrem relações e recuperam fatos; regras, inferência e *embeddings* podem ser adicionados, mas dependem da tecnologia e da aplicação. |
| Esquema | Mais explícito e expressivo; alterações devem preservar a consistência lógica pretendida. | Pode ser flexível, especialmente em property graphs, embora aplicações ainda possam impor esquemas e validações. |
| Escala e custo | O custo do raciocínio depende dos axiomas, do reasoner e dos dados; inferência pode se tornar cara. | Bancos de grafos são apropriados para consultas relacionais e travessias em grandes volumes, mas desempenho depende do banco, dos índices e das consultas. |
| Ferramentas | Protégé, OWL API, HermiT e Pellet. | Neo4j/Cypher para property graphs; RDF stores e SPARQL para grafos RDF. |


### Aplicação: recomendação de filmes

Uma **ontologia** é útil para definir que `Diretor` é uma subclasse de `Pessoa`, que filmes têm gêneros e que um `FilmeDeAcao` é um filme que tem o gênero `Acao`. Um reasoner pode inferir tipos que não foram registrados diretamente e ajudar a encontrar inconsistências no modelo.

Um **grafo de conhecimento** é útil para conectar filmes, pessoas, gêneros e usuários, e responder consultas de caminhos, como encontrar filmes de um gênero ou títulos relacionados a filmes que uma pessoa avaliou. Para armazenar muitas avaliações e consultar conexões, um banco de grafos pode ser uma escolha prática. As duas partes podem ser combinadas: a ontologia define o significado do vocabulário e o grafo guarda os fatos e avaliações.

### Exemplo de mapeamento e inferência

Em `filmes.ttl`, o esquema declara `Diretor` como subclasse de `Pessoa` e define `FilmeDeAcao` como a classe de coisas que têm o gênero `Acao`. Os fatos dizem que Lana Wachowski dirigiu `Matrix`, e que `Matrix` tem gênero `Acao`.

No Neo4j, `Lana Wachowski` recebe os labels `Diretor` e `Pessoa`, e `Matrix` é representado por um nó `Filme` ligado ao nó `Genero` `Acao`. O script materializa a hierarquia de labels e depois executa uma consulta que atribui `FilmeDeAcao` aos filmes com esse gênero.

Essa última etapa evidencia a diferença: o reasoner OWL pode deduzir o tipo `FilmeDeAcao` a partir do axioma e dos fatos; no property graph, a mesma conclusão só aparece depois que a regra correspondente é executada. Sem essa materialização, o nó continua sem esse label, ainda que uma consulta possa encontrar o filme pelo gênero.

## Status

- [x] Código/conteúdo: ontologia Turtle e carga/consulta Cypher
- [x] Relatório: comparação, decisões e exemplo de mapeamento
- [ ] Demo/vídeo (se aplicável)
