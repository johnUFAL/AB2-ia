# Q7: Sistema de Apoio ao Diagnóstico Médico Baseado em Casos (CBR)

Questão 7 da Lista 2 (AB2), IA PPGI 2026.2, prof. Evandro Costa.

> Desenvolver um sistema que receba sintomas informados pelo paciente, compare-os com uma base de casos previamente armazenados e implemente as etapas do ciclo de Raciocínio Baseado em Casos: Recuperação (Retrieve), Reutilização (Reuse), Revisão (Revise) e Retenção (Retain).

> **Aviso:** os casos são **fictícios** e o sistema é um protótipo acadêmico. Ele **não substitui avaliação médica** e as sugestões de tratamento são genéricas, para ilustrar o funcionamento. 

## Como rodar

Só a biblioteca padrão do Python 3.10 ou mais recente (testado com 3.13).

```bash
python3 cbr.py               # demonstração: duas consultas e a avaliação da base (não grava nada)
python3 cbr.py --interativo  # consulta com perguntas; pode gravar o caso confirmado na base
python3 -m unittest -v       # roda os 19 testes
```

O modo interativo grava de verdade em `data/casos_medicos.csv`. Para experimentar sem alterar a base, copie o arquivo antes.

## Arquivos

| Arquivo | Conteúdo |
|---|---|
| `cbr.py` | O sistema: representação, similaridade, ciclo Retrieve/Reuse/Revise/Retain, avaliação e interface de linha de comando |
| `data/casos_medicos.csv` | A base de casos (20 casos fictícios, 5 doenças) |
| `test_cbr.py` | Testes: integridade da base, similaridade, recuperação, votação, revisão, retenção e avaliação |
| `README.md` | Este arquivo |

---

## 1. Descrição da base de casos

A base tem **20 casos fictícios**, com **4 casos para cada uma de 5 doenças**: Gripe, Dengue, Pneumonia, Enxaqueca e Gastrite. Os sintomas de cada caso seguem os sintomas típicos da doença correspondente, como dor atrás dos olhos e manchas na pele na dengue, ou sensibilidade à luz na enxaqueca. Não foi feita revisão médica dos casos. Eles não correspondem a pacientes reais.

Cada caso tem:
- **id**: C01 a C20.
- **faixa etária** (Jovem, Adulto ou Idoso), **duração dos sintomas** (até 3 dias, 4 a 7 dias ou mais de 7 dias) e um **conjunto de sintomas**.
- **diagnóstico** e **tratamento**. O tratamento é genérico e indica quando é preciso orientação médica.

Os sintomas são 14: febre, tosse, dor de cabeça, dor muscular, dor de garganta, coriza, náusea, dor abdominal, azia, dor atrás dos olhos, manchas na pele, falta de ar, dor no peito e sensibilidade à luz.

## 2. Representação dos casos

Cada caso é um objeto `Caso` com a descrição do paciente (`Descricao`), o diagnóstico e o tratamento. No CSV, o conjunto de sintomas é guardado como lista separada por `;`:

```
C10,Adulto,4_a_7_dias,dor_no_peito;falta_de_ar;febre;tosse,Pneumonia,Avaliação médica imediata; ...
```

A representação tem três partes:
- **Sintomas:** conjunto (sem ordem), porque a presença de um sintoma importa e a ordem não.
- **Faixa etária e duração:** atributos ordinais (Jovem < Adulto < Idoso; até 3 dias < 4 a 7 dias < mais de 7 dias). A ordem entra na similaridade, como mostra a seção 3.

## 3. Método de cálculo de similaridade

A similaridade global entre a consulta e um caso é a média ponderada de três parcelas, cada uma entre 0 e 1:

| Atributo | Peso | Cálculo |
|---|---|---|
| Sintomas | 0,6 | **Índice de Jaccard**: `|A ∩ B| / |A ∪ B|` (sintomas em comum sobre o total citado) |
| Faixa etária | 0,2 | 1,0 se igual; 0,5 se vizinhos na escala (Jovem–Adulto, Adulto–Idoso); 0,0 caso contrário |
| Duração | 0,2 | Mesma regra ordinal da faixa etária |

`sim(consulta, caso) = 0,6 · J(sintomas) + 0,2 · S(faixa) + 0,2 · S(duração)`

**Por que Jaccard para sintomas:** ele mede a sobreposição entre os conjuntos e ignora sintomas que nenhum dos dois tem. Isso é importante porque a base tem 14 sintomas possíveis e cada caso cita poucos. Se contássemos também a ausência, dois casos quaisquer ficariam parecidos só por não ter os mesmos sintomas.

**Por que os pesos são 0,6, 0,2 e 0,2:** os sintomas são o que mais distingue as doenças, então recebem mais peso. Os pesos foram escolhidos por esse raciocínio, **não foram ajustados** para melhorar a acurácia.

**Desempate:** em caso de empate de similaridade, vale a ordem da base.

## 4. Ciclo CBR

### Retrieve (recuperação)
Calcula a similaridade da consulta com todos os casos e devolve os **k = 5 mais semelhantes**, com a parcela de cada atributo. Essa parcela é o que permite explicar por que um caso foi escolhido.

### Reuse (reutilização)
Propõe o diagnóstico por **votação ponderada**: cada caso recuperado vota no próprio diagnóstico com peso igual à sua similaridade. O diagnóstico com maior soma vence, e a **confiança** é a fração do peso total que ele recebeu. O tratamento sugerido é o do caso mais similar entre os que têm o diagnóstico vencedor.

A votação é ponderada pela similaridade, e não pela contagem simples. Assim, um caso muito parecido pesa mais que três casos pouco parecidos.

### Revise (revisão)
O profissional confirma o diagnóstico sugerido ou informa outro. No modo interativo, basta apertar Enter para aceitar. Se a correção for outra doença já existente na base, o tratamento é o registrado para ela (o do primeiro caso dessa doença). Se a doença for nova, o sistema pede o tratamento ao profissional.

### Retain (retenção)
Se o profissional confirmar, o caso (com os sintomas, o diagnóstico e o tratamento) é gravado no CSV com um novo id. A partir daí ele entra na recuperação das próximas consultas. O teste `test_caso_retido_passa_a_ser_recuperado` verifica isso.

## 5. Exemplos de consultas

### Consulta A
**Paciente:** Adulto, sintomas de 4 a 7 dias, com febre, tosse, falta de ar e dor no peito.

| Caso | Score | Sintomas | Faixa | Duração | Diagnóstico |
|---|---|---|---|---|---|
| C10 | 1,000 | 1,00 | 1,0 | 1,0 | Pneumonia |
| C12 | 0,780 | 0,80 | 1,0 | 0,5 | Pneumonia |
| C09 | 0,680 | 0,80 | 0,5 | 0,5 | Pneumonia |
| C11 | 0,660 | 0,60 | 0,5 | 1,0 | Pneumonia |
| C04 | 0,500 | 0,33 | 0,5 | 1,0 | Gripe |

- **Diagnóstico sugerido:** Pneumonia (confiança 86%).
- **Tratamento sugerido:** avaliação médica imediata; antibiótico e possível internação conforme a gravidade.

O caso C10 é idêntico à consulta, então tem score 1,0. O quinto caso recuperado é de Gripe: ele compartilha febre e tosse com a consulta, mas não tem falta de ar nem dor no peito, por isso o score é baixo.

### Consulta B
**Paciente:** Adulto, sintomas de até 3 dias, com febre, dor atrás dos olhos, manchas na pele e dor muscular.

| Caso | Score | Sintomas | Faixa | Duração | Diagnóstico |
|---|---|---|---|---|---|
| C06 | 0,900 | 1,00 | 0,5 | 1,0 | Dengue |
| C05 | 0,700 | 0,50 | 1,0 | 1,0 | Dengue |
| C08 | 0,680 | 0,80 | 0,5 | 0,5 | Dengue |
| C07 | 0,600 | 0,50 | 1,0 | 0,5 | Dengue |
| C01 | 0,550 | 0,25 | 1,0 | 1,0 | Gripe |

- **Diagnóstico sugerido:** Dengue (confiança 84%).
- **Tratamento sugerido:** hidratação oral e repouso; acompanhamento médico imediato; evitar anti-inflamatórios e AAS sem orientação médica.

### Consulta C (inclusão de caso novo)
Com `python3 cbr.py --interativo`, é possível informar um paciente, confirmar ou corrigir o diagnóstico e gravar o caso. Foi testado com uma cópia da base: o caso foi gravado como C21 e o arquivo passou de 20 para 21 casos.

## 6. Análise dos resultados

### Avaliação leave-one-out

Para cada caso, o sistema recupera nos outros 19 e compara o diagnóstico sugerido com o real:

| k | Acertos | Acurácia |
|---|---|---|
| 1 | 16/20 | 80,0% |
| 3 | 20/20 | 100,0% |
| 5 | 19/20 | 95,0% |
| 7 | 19/20 | 95,0% |
| 9 | 19/20 | 95,0% |

**Erros com k = 1:** Dengue foi confundida com Gripe (C05 e C08) e com Gastrite (C07); Pneumonia foi confundida com Gripe (C11). Com um único vizinho, uma consulta cai no caso mais parecido, mesmo que ele seja de outra doença com sintomas parecidos. O aumento de k corrige esses erros, porque a votação dilui um caso isolado.

**Erro com k = 5:** C03 (Gripe em idoso, com febre, tosse, dor muscular, dor de cabeça e coriza) foi classificado como Pneumonia. Os sintomas de Gripe e de Pneumonia se sobrepõem bastante, e a faixa etária e a duração não bastaram para separá-las.

### Limites da avaliação

- **A base foi construída pelo próprio autor do sistema.** Os sintomas foram escritos de forma coerente com cada doença, então é esperado que o sistema acerte. O resultado de 100% com k = 3 mostra que os casos são internamente consistentes. Ele **não** mostra desempenho clínico real.
- **Os pesos foram escolhidos à mão** e não ajustados por validação. Ajustá-los com os mesmos 20 casos seria otimista.
- **Com 20 casos, cada acerto vale 5 pontos percentuais.** Diferenças de um caso não são conclusivas.

### Pontos fortes e fracos

- **Forte:** a recuperação é explicável. Para cada caso recuperado, o sistema mostra quais atributos contribuíram para a similaridade.
- **Forte:** a base cresce com o uso. Casos confirmados pelo profissional (Retain) melhoram as próximas consultas.
- **Fraco:** a similaridade trata os sintomas como iguais em importância. Um sintoma específico (como manchas na pele, que aponta para dengue) conta o mesmo que um sintoma comum (como tosse).
- **Fraco:** a regra de 0,5 para atributos vizinhos é uma escolha heurística, e não foi comparada com alternativas.
- **Fraco:** a base é pequena. Com centenas de casos, seria preciso indexar a busca em vez de comparar com todos.

## 7. Relação com a Q8

A Q8 é a rede bayesiana sobre diagnóstico médico. O plano de divisão pede que as Q7 e Q8 usem **as mesmas doenças e os mesmos sintomas**, para comparar os resultados. Por isso, as 5 doenças e os 14 sintomas daqui devem ser usados na rede bayesiana.

## 8. Demonstração

O enunciado pede um vídeo ou demonstração do protótipo. O comando `python3 cbr.py` mostra as duas consultas e a avaliação, e `python3 cbr.py --interativo` mostra o fluxo completo com gravação do caso. O vídeo precisa ser gravado com essas execuções.
