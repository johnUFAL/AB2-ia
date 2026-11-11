# Q9: Sistema de recomendação de filmes baseado em ontologia OWL 2

Questão 9 da Lista 2 (AB2), IA PPGI 2026.2, prof. Evandro Costa.

> Desenvolver um sistema de recomendação baseado em ontologias: escolher um domínio, modelar uma ontologia OWL 2 que represente conceitos, relacionamentos e restrições do domínio, e usar um raciocinador para classificar indivíduos e inferir relações implícitas. A ontologia alimenta um sistema que recomenda itens com base no perfil do usuário e mostra os elementos usados na decisão.

Domínio escolhido: **recomendação de filmes**. As questões 14 e 15 da lista usam o mesmo domínio.

> **Observação:** os títulos, anos, diretores e elencos são de filmes reais. As classificações indicativas (idade mínima) e os perfis de usuário são **ilustrativos**, para fins didáticos.

## Como rodar

Requer **Java** (o raciocinador HermiT roda em Java; testado com OpenJDK 21) e **Owlready2**.

```bash
pip install owlready2             # ou o equivalente no seu ambiente

python3 ontologia_filmes.py      # monta a ontologia, salva data/filmes.owl e mostra as inferências
python3 recomendador.py          # recomendações e justificativas para os quatro usuários
python3 -m unittest -v           # roda os 15 testes (inclui a detecção de inconsistência)
```

## Arquivos

| Arquivo | Conteúdo |
|---|---|
| `ontologia_filmes.py` | Construção da ontologia (classes, propriedades, axiomas, indivíduos), raciocínio e demonstração das inferências |
| `recomendador.py` | Carrega o arquivo OWL, roda o raciocinador e gera as recomendações com justificativas |
| `data/filmes.owl` | A ontologia em OWL 2 (formato RDF/XML), o arquivo do projeto |
| `test_ontologia.py` | Testes: estrutura, inferências, inversa, simetria, detecção de inconsistência e recomendações |
| `README.md` | Este arquivo |

---

## 1. Modelagem conceitual

### 1.1. Classes (26)

A ontologia tem uma hierarquia de classes com três ramos principais:

```
Thing
├── Pessoa
│   ├── Diretor
│   └── Ator
├── Filme
├── Genero
│   ├── Acao, Aventura, Animacao, Comedia, Crime, Drama,
│   └── FiccaoCientifica, Musical, Romance, Suspense, Terror   (11 subclasses)
├── Usuario
├── Idioma
└── ClassificacaoIndicativa
    ├── Livre, Maior12, Maior16, Maior18                        (4 subclasses)

Classes definidas por axioma (preenchidas pelo raciocinador):
├── FilmeDeTerror     ≡ Filme ⊓ ∃temGenero.Terror
├── FilmeParaFamilia  ≡ Filme ⊓ ∃temClassificacao.(Livre ⊔ Maior12)
└── FanDeTerror       ≡ Usuario ⊓ ∃gostaDeGenero.Terror
```

**Por que esta hierarquia:**
- **Gênero como hierarquia de classes** (e não como texto): permite que o raciocinador use a relação "é um tipo de", e que um gênero específico seja referenciado como classe em uma restrição (`∃temGenero.Terror`).
- **Classificação indicativa como classes disjuntas**: um filme tem exatamente uma classificação. Isso é usado na verificação de consistência (seção 4).
- **Pessoa com Diretor e Ator**: uma mesma pessoa pode ser diretora e atriz em filmes diferentes, então as duas classes não são disjuntas. Por isso o indivíduo `tom_hanks` é `Ator` (ele aparece em *Toy Story* e *Forrest Gump*).

### 1.2. Propriedades (18: 13 de objeto e 5 de dados)

| Propriedade | Tipo | Domínio → imagem | Característica | Papel no domínio |
|---|---|---|---|---|
| `temGenero` | objeto | Filme → Genero | | Gêneros do filme |
| `dirigidoPor` | objeto | Filme → Diretor | | Diretor do filme |
| `temAtor` | objeto | Filme → Ator | | Elenco principal |
| `temIdioma` | objeto | Filme → Idioma | | Idioma original |
| `temClassificacao` | objeto | Filme → ClassificacaoIndicativa | **funcional** | Uma única classificação por filme |
| `gostaDeGenero` | objeto | Usuario → Genero | | Preferência do usuário |
| `gostaDeDiretor` | objeto | Usuario → Diretor | | Diretor favorito |
| `gostaDeAtor` | objeto | Usuario → Ator | | Ator favorito |
| `viu` | objeto | Usuario → Filme | | Histórico do usuário |
| `similarA` | objeto | Filme → Filme | **simétrica** | Filmes parecidos (curadoria) |
| `dirigiu` | objeto | Diretor → Filme | **inversa de `dirigidoPor`** | Propriedade derivada |
| `atuou` | objeto | Ator → Filme | **inversa de `temAtor`** | Propriedade derivada |
| `filmesDoGenero` | objeto | Genero → Filme | **inversa de `temGenero`** | Propriedade derivada |
| `titulo` | dados | Filme → string | funcional | Título |
| `ano` | dados | Filme → inteiro | funcional | Ano de lançamento |
| `nome` | dados | Pessoa → string | funcional | Nome da pessoa |
| `idadeUsuario` | dados | Usuario → inteiro | funcional | Idade do usuário |
| `idadeMinima` | dados | ClassificacaoIndicativa → inteiro | funcional | Idade mínima da classificação |

As propriedades inversas e a simétrica não precisam ser afirmadas nos dois sentidos: o raciocinador deriva a relação contrária. Por exemplo, afirmamos apenas `Interestelar dirigidoPor Christopher Nolan`, e o raciocinador conclui que `Christopher Nolan dirigiu Interestelar`.

### 1.3. Axiomas e restrições

- **Disjunção de níveis superiores:** `Filme`, `Pessoa`, `Genero`, `Usuario`, `Idioma` e `ClassificacaoIndicativa` são mutuamente disjuntas. Um indivíduo não pode ser, por exemplo, filme e usuário ao mesmo tempo.
- **Classificações mutuamente disjuntas:** `Livre`, `Maior12`, `Maior16` e `Maior18`.
- **Definições por equivalência:** `FilmeDeTerror`, `FilmeParaFamilia` e `FanDeTerror` são definidas por condições necessárias e suficientes, então o raciocinador classifica os indivíduos nelas automaticamente.
- **Domínio e imagem** de cada propriedade (tabela acima).
- **Funcionalidade:** `temClassificacao`, `titulo`, `ano` etc. têm um único valor.

### 1.4. Indivíduos (80)

- **17 filmes** com título, ano, gêneros, diretor, elenco, idioma e classificação.
- **17 diretores** e **24 atores** (com nome).
- **11 gêneros** (um indivíduo por classe de gênero), **3 idiomas** (Inglês, Francês, Coreano) e **4 classificações**.
- **4 usuários** com idade, gostos e histórico de filmes vistos.
- **6 pares de filmes parecidos** (`similarA`).

Os filmes cobrem gêneros variados, mais de um idioma e classificações diferentes, para que as recomendações tenham casos para diferenciar.

## 2. Consultas e inferências

Depois de rodar `ontologia_filmes.py`, o raciocinador HermiT mostra as seguintes conclusões. **Nenhuma delas foi afirmada diretamente.**

| Inferência | Resultado | Como foi obtida |
|---|---|---|
| `FilmeDeTerror` | O Iluminado, O Silêncio dos Inocentes | Ambos têm gênero Terror, e a classe é definida por essa condição |
| `FilmeParaFamilia` | Toy Story, Up, Titanic, Forrest Gump, La La Land, Interestelar, Jurassic Park, Amélie | Classificação Livre ou Maior12 |
| `FanDeTerror` | Ana | Ana gosta do gênero Terror |
| `dirigiu` (inversa) | Christopher Nolan dirigiu Interestelar | Derivada de `dirigidoPor` |
| `similarA` (simétrica) | O Iluminado é similar a O Silêncio dos Inocentes | Afirmado só no sentido contrário |

A inferência `FanDeTerror` é a mais relevante para o sistema: ela transforma um fato simples ("Ana gosta de Terror") em uma categoria de perfil que pode ser usada em outras consultas, sem que alguém tenha classificado a Ana à mão.

## 3. Mecanismo de recomendação

Para um usuário, o sistema:

1. **Filtra** os filmes que o usuário ainda não viu.
2. **Filtra** pela idade: a idade mínima da classificação do filme não pode ser maior que a idade do usuário.
3. **Pontua** cada filme restante com as relações da ontologia:

| Relação | Pontos | Exemplo de justificativa |
|---|---|---|
| Gênero que o usuário gosta | +2 por gênero em comum | "+2 gênero Terror (que você gosta)" |
| Diretor favorito | +3 | "+3 dirigido por Quentin Tarantino (diretor favorito)" |
| Ator favorito | +2 por ator em comum | "+2 com Tom Hanks (ator favorito)" |
| Parecido com um filme visto | +1 por filme visto em `similarA` | "+1 parecido com Toy Story, que você já viu" |

4. **Ordena** pela pontuação e devolve os k primeiros, com os motivos de cada pontuação.

Os pesos são escolhidos pelo autor e são didáticos. Eles não foram ajustados por avaliação de usuários.

### Exemplos de recomendações

**Ana** (28 anos; perfil inferido: **FanDeTerror**; já viu *Matrix* e *Interestelar*):
1. O Iluminado (4 pontos): +2 Suspense, +2 Terror
2. O Silêncio dos Inocentes (4 pontos): +2 Suspense, +2 Terror
3. Clube da Luta (2 pontos): +2 Suspense
4. Jurassic Park (2 pontos): +2 Ficção científica

**Bruno** (12 anos; já viu *Toy Story*):
1. Up - Altas Aventuras (3 pontos): +2 Animação, +1 parecido com Toy Story
2. Amélie (2 pontos): +2 Comédia
3. Forrest Gump (2 pontos): +2 com Tom Hanks

*Se Beber, Não Case!* não aparece para o Bruno, porque a classificação é 16 e ele tem 12 anos.

**Diego** (20 anos; já viu *O Poderoso Chefão*):
1. Pulp Fiction (8 pontos): +2 Crime, +2 Drama, +3 dirigido por Quentin Tarantino, +1 parecido com O Poderoso Chefão

Pulp Fiction fica em primeiro porque combina três fatores: gênero, diretor favorito e um filme parecido ao que ele já viu.

## 4. Verificação de consistência

A ontologia é verificada pelo raciocinador antes do uso. O teste `test_ontologia_inconsistente_e_detectada` cria uma cópia com um indivíduo que pertence a duas classes disjuntas (`Livre` e `Maior18`) e confirma que o HermiT recusa a ontologia. Assim, uma contradição na base de conhecimento não passa despercebida.

## 5. Análise crítica

### Vantagens da abordagem

- **O conhecimento é explícito e reutilizável.** Gêneros, pessoas e relações estão no modelo, não espalhados em código. Outro sistema pode consultar o mesmo arquivo `.owl`.
- **Inferências automáticas.** Perfis (`FanDeTerror`), relações inversas e simétricas e classificações (`FilmeDeTerror`) são derivados sem código de regras específico.
- **Consistência verificável.** O raciocinador detecta contradições, o que um banco de dados comum não faz.
- **Justificativas.** Cada recomendação mostra quais relações pesaram, o que atende ao requisito de exibir os elementos usados na decisão.

### Limitações

- **Pesos escolhidos à mão.** A pontuação (2, 3, 2, 1) é uma escolha didática. Ela não foi ajustada com dados de avaliações reais, então a ordem das recomendações depende dessa escolha.
- **Catálogo pequeno.** Com 17 filmes, o sistema não tem variedade suficiente para ser comparado com um serviço real. Com milhares de filmes, a lógica de pontuação em Python precisaria de índices.
- **Não usa o raciocinador na recomendação.** A pontuação é feita em Python, e o raciocinador só classifica. Um sistema mais completo poderia usar consultas DL diretamente (por exemplo, "filmes de terror que não foram vistos") para que a própria lógica formal selecione os candidatos.
- **Sem aprendizado.** O sistema não aprende com as escolhas do usuário. Os pesos e o perfil são fixos.
- **Classificações ilustrativas.** A idade mínima de cada classificação não corresponde necessariamente à classificação oficial, e as relações de `similarA` foram escritas à mão.
- **Mundo aberto.** O raciocinador assume o mundo aberto: a ausência de uma relação não significa que ela é falsa. Por exemplo, não afirmar que um filme é de Terror não o torna "não-terror" para o raciocinador. Para tratar isso, seria preciso declarar explicitamente as negações ou usar a suposição de mundo fechado.

### Possíveis melhorias

1. Expressar os critérios de candidatos como consultas DL, e não em Python.
2. Ajustar os pesos com dados de avaliações reais, ou aprendê-los com base no histórico.
3. Adicionar propriedades de intensidade de gênero e de elenco mais detalhadas.
4. Expor a ontologia por uma interface (por exemplo, SPARQL com um endpoint) para integração com outros sistemas.
