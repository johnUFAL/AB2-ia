# Q2: K-vizinhos mais próximos (KNN) sobre a base de crédito

Questão 2 da Lista 2 (AB2), IA PPGI 2026.2, prof. Evandro Costa.

> "Mostre e explique o funcionamento do algoritmo dos K-vizinhos mais próximos (KNN) sobre a base de dados com as 30 instâncias que você usou na lista de exercício 1."

## Como rodar

Só a biblioteca padrão do Python 3.10 ou mais recente (testado com 3.13).

```bash
python3 knn.py              # mostra a base, uma classificação passo a passo e a validação
python3 -m unittest -v      # roda os 14 testes
```

## Arquivos

| Arquivo | Conteúdo |
|---|---|
| `knn.py` | Implementação do KNN, da distância de Hamming e da validação leave-one-out, com a saída formatada |
| `test_knn.py` | Testes: integridade da base, distância, ordenação, desempates e validação |
| `data/credito_ampliado.csv` | As 30 instâncias da Lista 1 (cópia do arquivo usado lá, para o repositório ser autocontido) |
| `README.md` | Este arquivo |

---

## 1. A base

A base tem 30 exemplos (E1 a E30) e 6 atributos categóricos, mais a classe de risco:

| Atributo | Valores possíveis |
|---|---|
| Historia (histórico de crédito) | Ruim, Desconhecida, Boa |
| Divida | Alta, Baixa |
| Garantia | Nenhuma, Adequada |
| Renda | 0-15k, 15-35k, >35k |
| Emprego | Estavel, Instavel |
| Idade | Jovem, Adulto, Senior |
| **Decision** (classe) | Alto (9), Moderado (11), Baixo (10) |

Conferi a base antes de usar: não há vetores de atributos repetidos, nem vetores repetidos com classes diferentes. Assim, nenhum exemplo "conflita" com outro.

## 2. Como o KNN funciona

O KNN é um algoritmo **preguiçoso**: não há fase de treino. Para classificar um exemplo novo, ele faz o seguinte:

1. **Escolhe k**, o número de vizinhos que vão votar.
2. **Mede a distância** entre o exemplo novo e cada um dos 30 exemplos da base.
3. **Ordena** os exemplos pela distância e pega os **k mais próximos**.
4. **Vota**: a classe mais frequente entre os k vizinhos é a previsão.

Os três pontos que mudam o resultado são a **métrica de distância**, o **valor de k** e a **regra de desempate**. Cada um é tratado abaixo.

### 2.1. Métrica: distância de Hamming

Os atributos são categóricos (`Boa`, `Ruim`, `Alta`...), e não números. Por isso a distância euclidiana, que soma diferenças numéricas, não se aplica diretamente. Usei a **distância de Hamming**: conta quantos atributos têm valores diferentes.

- Distância 0: os seis atributos são iguais.
- Distância 6: os seis atributos são diferentes.

Exemplo: E1 = (Ruim, Alta, Nenhuma, 0-15k, Estavel, Adulto) e E7 = (Ruim, Baixa, Nenhuma, 0-15k, Estavel, Senior) diferem em **Divida** e **Idade**. A distância é 2.

**Por que essa métrica é uma escolha defensável:**
- Ela é a distância euclidiana que se obtém ao codificar cada atributo em one-hot. Nesse caso, a distância euclidiana ao quadrado é exatamente 2 × Hamming. Então a ordenação dos vizinhos é a mesma.
- O complemento dela é a sobreposição (*overlap*): sobreposição = 6 − Hamming. Usar uma ou outra dá o mesmo resultado.

**Limitação:** Hamming trata todos os atributos com o mesmo peso. Na Lista 1, a árvore ID3 mostrou que Renda e Emprego são muito mais informativos que Idade. O KNN com Hamming não sabe disso (ver seção 5).

### 2.2. Valor de k e desempate

Com seis atributos, a distância só pode ser 0, 1, ..., 6. Há muitos empates, e isso precisa de uma regra explícita:

- **Ordenação dos vizinhos:** em empate de distância, vale a ordem da base (E1 antes de E2...). A ordenação é estável.
- **Empate de votos:** fica a classe empatada que aparece primeiro na lista de vizinhos, ou seja, a do vizinho mais próximo entre as empatadas.

Com três classes, empates de voto podem acontecer mesmo com k ímpar. A validação testa só k ímpar (1, 3, 5, 7, 9), para reduzir esse caso. Na consulta de exemplo (seção 3), o resultado não depende da regra de desempate.

## 3. Exemplo passo a passo

Consulta: um cliente com **Historia = Boa, Divida = Baixa, Garantia = Nenhuma, Renda = 15-35k, Emprego = Estavel, Idade = Adulto**. Esse cliente não está na base.

**Passo 1: distância até cada um dos 30 exemplos.** Os mais próximos (k = 5):

| Exemplo | Distância | Classe | Historia | Divida | Garantia | Renda | Emprego | Idade |
|---|---|---|---|---|---|---|---|---|
| E27 | **1** | Moderado | Boa | Baixa | Nenhuma | 0-15k | Estavel | Adulto |
| E3 | **2** | Moderado | Desconhecida | Baixa | Nenhuma | 15-35k | Estavel | Jovem |
| E9 | **2** | Baixo | Boa | Baixa | Nenhuma | >35k | Instavel | Adulto |
| E17 | **2** | Moderado | Ruim | Baixa | Adequada | 15-35k | Estavel | Adulto |
| E22 | **2** | Moderado | Desconhecida | Baixa | Nenhuma | >35k | Estavel | Adulto |
| *E25 (fora do k)* | *2* | *Baixo* | *Boa* | *Baixa* | *Nenhuma* | *15-35k* | *Instavel* | *Senior* |

Os outros 24 exemplos estão a distância 3 ou mais. O código imprime a tabela completa.

**Passo 2: votos entre os 5 vizinhos.** Moderado = 4, Baixo = 1.

**Passo 3: previsão.** Moderado.

**Sobre o empate na fronteira:** E25 também está a distância 2, mas ficou de fora porque o k = 5 corta no meio desse grupo. Testei todas as escolhas possíveis entre os cinco empatados na fronteira. Em todas, a previsão continua **Moderado**. Então o resultado não depende da regra de desempate.

## 4. Validação: leave-one-out

Para medir a qualidade do KNN, usei **leave-one-out** (LOO): para cada um dos 30 exemplos, tiro ele da base, classifico-o com os outros 29 e comparo com a classe real.

| k | Acertos | Acurácia |
|---|---|---|
| 1 | 14/30 | 46,7% |
| 3 | 17/30 | 56,7% |
| 5 | 18/30 | 60,0% |
| 7 | 19/30 | 63,3% |
| **9** | **20/30** | **66,7%** |

Testei também k de 11 a 21. Os valores ficam entre 18 e 20 acertos para k de 5 a 19, e caem para 14 em k = 21. Ou seja, a acurácia é razoavelmente estável para k intermediário.

**Cuidado com a escolha de k:** escolhi k = 9 olhando o LOO, que usa os mesmos dados. Isso é otimista, porque a escolha foi feita olhando o resultado. Com 30 exemplos, cada acerto vale 3,3 pontos percentuais, então diferenças de um ou dois acertos não são conclusivas.

## 5. Comparação com as árvores da Lista 1

Os resultados abaixo vêm do leave-one-out da Lista 1, na mesma base:

| Método | Acertos LOO | Acurácia |
|---|---|---|
| ID3 | 22/30 | 73,3% |
| CART (manual) | 21/30 | 70,0% |
| C4.5 | 16/30 | 53,3% |
| **KNN, Hamming, k = 9** | **20/30** | **66,7%** |

O KNN fica atrás do ID3 e do CART. A hipótese mais provável é o peso igual dado aos atributos, mas não testei isso formalmente. Na Lista 1, o ganho de informação colocou Renda e Emprego como os atributos mais informativos, e Idade com ganho quase nulo (0,0105). O KNN com Hamming trata Idade com o mesmo peso que Renda, então pode estar dando peso demais a um atributo pouco informativo.

Uma melhoria natural seria **ponderar os atributos** (por exemplo, pelo ganho de informação da Lista 1). Isso não foi feito aqui, porque o enunciado pede o KNN básico.

## 6. Limitações

- **Base pequena:** 30 exemplos e 6 atributos com poucos valores. A distância de Hamming só assume sete valores (0 a 6), então há muitos empates.
- **Pesos iguais:** todos os atributos contam o mesmo na distância, mesmo com relevância diferente.
- **Custo de consulta:** cada classificação calcula a distância até os 30 exemplos. Isso é barato aqui, mas cresce linearmente com a base.
- **Sem normalização estatística:** como os atributos são categóricos, não há escala a normalizar. Se a base crescer com atributos numéricos, a distância precisaria de normalização antes.
