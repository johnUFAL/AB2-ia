# Q14 - Knowledge Graph: representação, inferência e aprendizagem

Esta questão tem três partes:

1. **Pesquisa** (texto): `pesquisa_knowledge_graph.md`. Cobre representação, inferência, aprendizagem e uma aplicação comentada (busca do Google), com referências.
2. **Implementação** em Python puro: um grafo de conhecimento sobre o mesmo domínio de filmes da Q9, com regras de inferência, explicação das inferências e recomendação por caminhos no grafo.
3. **Exportação para Neo4j** (Cypher), pedida na dica do enunciado. **Não foi executada** neste ambiente (ver seção "Limitações").

## Como rodar

Requisitos: Python 3 (testado com Python 3.13; a versão mínima não foi testada, mas o código usa apenas a biblioteca padrão e anotações compatíveis com 3.9+). Não há dependências externas.

```bash
cd q14-knowledge-graph

# Monta o grafo, aplica as regras, mostra explicações e recomendações
python3 kg.py

# Gera data/grafo_filmes.cypher (script para o Neo4j)
python3 kg.py --cypher

# Testes (18 testes)
python3 -m unittest -v test_kg.py
```

Saída esperada do `python3 kg.py` (trecho):

```
Triplas afirmadas: 305
Triplas inferidas pelas regras: 135
Total no grafo: 440

--- Classes definidas por regra (inferidas) ---
  FilmeDeTerror (2): o_iluminado, silencio_dos_inocentes
  FilmeParaFamilia (8): amelie, forrest_gump, interestelar, jurassic_park, la_la_land, titanic, toy_story, up
  FanDeTerror (1): ana
...
```

## Estrutura

| Arquivo | Conteúdo |
|---|---|
| `kg.py` | Grafo com procedência, regras, explicação, recomendação e exportação Cypher |
| `test_kg.py` | 18 testes (regras isoladas, inferências do catálogo, recomendações, Cypher) |
| `data/catalogo_filmes.json` | Catálogo exportado da Q9 (17 filmes, 4 usuários, 41 pessoas) |
| `data/grafo_filmes.cypher` | Script Cypher gerado por `kg.py --cypher` (não executado) |
| `pesquisa_knowledge_graph.md` | Texto de pesquisa, com a aplicação comentada e as referências |

## Modelo

Tudo é uma **tripla** `(sujeito, predicado, objeto)`. Há três tipos de predicado:

- **Relações entre entidades**: `dirigidoPor`, `temAtor`, `temGenero`, `similarA`, `viu`, `gostaDeGenero`, etc.
- **Literais**: `titulo`, `ano`, `nome`, `idade`, `idadeMinima`. O objeto é um texto ou número, não uma entidade.
- **Esquema**: `tipo` (é instância de) e `subClasseDe` (é subclasse de).

Ao todo, 305 triplas são afirmadas diretamente do catálogo.

## Regras de inferência

Cada regra é aplicada até o grafo parar de crescer (encadeamento para frente, ponto fixo):

| Regra | Forma |
|---|---|
| subclasse | `(x tipo A)`, `(A subClasseDe B)` ⇒ `(x tipo B)`, e transitividade de `subClasseDe` |
| inversa | `dirigidoPor` ⇒ `dirigiu`; `temAtor` ⇒ `atuou`; `temGenero` ⇒ `filmesDoGenero` |
| simétrica | `similarA` vale nos dois sentidos |
| classe definida | `temGenero Terror` ⇒ `FilmeDeTerror`; `gostaDeGenero Terror` ⇒ `FanDeTerror`; `temClassificacao Livre/Maior12` ⇒ `FilmeParaFamilia` |

Cada tripla inferida guarda a regra e as premissas. A função `explicar` mostra essa cadeia. Exemplo:

```
silencio_dos_inocentes tipo FilmeDeTerror   [inferida por: definida FilmeDeTerror (temGenero Terror)]
  silencio_dos_inocentes temGenero Terror   [afirmada]
```

As classes inferidas batem com as da Q9 (raciocinador HermiT): `FilmeDeTerror`, `FilmeParaFamilia` e `FanDeTerror` têm os mesmos membros nas duas implementações.

## Recomendação por caminhos

Para um usuário, cada caminho do grafo até um filme que ele não viu soma pontos. O motivo de cada pontuação é o próprio caminho:

| Caminho | Forma | Peso |
|---|---|---|
| gênero | `usuário → gostaDeGenero → gênero ← temGenero ← filme` | 2 |
| diretor | `usuário → gostaDeDiretor → diretor ← dirigidoPor ← filme` | 3 |
| ator | `usuário → gostaDeAtor → ator ← temAtor ← filme` | 2 |
| parecido | `usuário → viu → f0 ← similarA ← filme` | 1 |
| colaborativo | `usuário → viu → f0 ← viu ← outro → viu → filme` | 1 |

Filmes com classificação acima da idade do usuário são descartados. Os pesos são os mesmos da Q9, e foram escolhidos pelo autor de forma didática.

**Resultado**: as quatro listas de recomendação são idênticas às da Q9 (Ana, Bruno, Carla e Diego). Essa igualdade é testada em `test_recomendacoes_batem_com_q9`.

## Aplicação comentada

A parte de pesquisa comenta o Google Knowledge Graph e usa o grafo deste projeto para mostrar a inferência: "Ana é fã de Terror?" é respondido porque a regra "gosta de Terror ⇒ é fã de Terror" é aplicada à aresta afirmada. Detalhes no texto.

## Decisões

- **Python em vez de Neo4j para a execução.** O enunciado sugere Neo4j como ferramenta, mas o banco não estava disponível neste ambiente (ver Limitações). Para que a inferência e as explicações funcionassem de verdade, implementei o grafo e as regras em Python. O Cypher é uma exportação das triplas afirmadas, para quem quiser carregar no Neo4j.
- **Forward chaining em vez de raciocinador OWL.** A Q9 já usa OWL e HermiT. Aqui o objetivo é mostrar o mecanismo de regras e a procedência, que o raciocinador não expõe da mesma forma.
- **Procedência em cada tripla inferida.** É o recurso que permite explicar a recomendação. Sem isso, o resultado seria só uma lista de nomes.
- **Mundo fechado.** Um fato ausente é tratado como falso, porque o catálogo é a lista completa do sistema.
- **Catálogo reaproveitado da Q9.** Os dados são exatamente os da Q9, o que permite comparar as duas implementações.

## Limitações

- **Neo4j não foi executado.** Tentei usar o banco: o daemon do Docker não estava rodando, o download direto do Neo4j foi negado (403), não há driver Python nem binário instalados. Por isso, **o arquivo `data/grafo_filmes.cypher` não foi testado no Neo4j.** A sintaxe segue o padrão Cypher, mas ela precisa ser validada ao carregar o arquivo. O script começa com `MATCH (n) DETACH DELETE n`, que apaga todo o banco. Use em um banco vazio ou de teste.
- **Valores numéricos viram texto no Cypher.** `idade`, `ano` e `idadeMinima` são exportados como strings. Nas consultas Neo4j, é preciso usar `toInteger(...)`.
- **Consultas Neo4j não verificadas.** Se for usar o banco, por exemplo para achar filmes de Terror:

  ```cypher
  MATCH (f:Entidade)-[:temGenero]->(:Entidade {id: "Terror"})
  RETURN f.titulo
  ```

  Essa consulta não foi executada aqui. No Neo4j, as inferências precisam ser reproduzidas por consultas ou regras (APOC, por exemplo), e este projeto não fez isso.
- **Pesos da recomendação são arbitrários.** Eles não foram ajustados com dados reais, e o catálogo é pequeno (17 filmes, 4 usuários).
- **Regras escritas à mão.** Um conjunto maior de regras pode gerar conflitos ou inferências que não se desejam. Não há checagem de consistência neste grafo.

## Referências

As referências estão no fim de `pesquisa_knowledge_graph.md`.
