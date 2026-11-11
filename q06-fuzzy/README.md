# q06-fuzzy

## Objetivo

Implementa um sistema de inferência fuzzy para estimar a prioridade de uma
atividade a partir do prazo disponível, da importância e do esforço estimado.
O resultado é um valor entre 0 e 100; valores maiores indicam prioridade maior.

## Entradas e funções de pertinência

| Variável | Universo | Termos linguísticos |
|---|---:|---|
| Prazo (horas) | 0 a 72 | urgente, próximo, folgado |
| Importância | 0 a 10 | baixa, média, alta |
| Esforço (minutos) | 0 a 180 | pequeno, médio, grande |
| Prioridade | 0 a 100 | baixa, média, alta |

As funções trapezoidais representam os extremos e as triangulares os termos
intermediários. As regiões se sobrepõem para permitir transições graduais.

## Regras

A base combina prazo e importância: prazos urgentes elevam a prioridade,
especialmente quando a importância é média ou alta; prazos folgados reduzem a
prioridade, exceto para atividades importantes. Duas regras complementares
consideram o esforço: esforço grande com prazo próximo eleva a prioridade, e
esforço pequeno com prazo folgado a reduz.

A inferência usa AND por mínimo, agregação por máximo e defuzzificação pelo
centroide. O módulo também implementa manualmente essas etapas, permitindo
comparar o cálculo manual ao sistema de controle do `scikit-fuzzy`.

## Como executar

Na raiz do repositório, com as dependências do projeto instaladas:

```powershell
python q06-fuzzy\fuzzy_prioridade.py
```

O arquivo contém as funções `inferir(prazo, importancia, esforco)` e
`inferencia_manual(prazo, importancia, esforco)`. Os valores aceitos são,
respectivamente, de 0 a 72 horas, de 0 a 10 e de 0 a 180 minutos. Valores
fora desses intervalos ou não finitos geram `ValueError`.

As funções de plotagem `plota_variaveis()`, `plota_agregacao(p, i, e, nome)` e
`plota_superficie()` salvam as imagens em `q06-fuzzy/figs/`. A superfície é
calculada com esforço fixo de 60 minutos.

## Testes

Instale `pytest` (não incluído em `requirements.txt`) e execute, a partir da
raiz do repositório:

```powershell
python -m pip install pytest
python -m pytest -q q06-fuzzy\test_fuzzy_prioridade.py
```

Os testes cobrem a concordância entre as inferências automática e manual,
saídas dentro do universo de prioridade, agregação não vazia, efeito das regras
de esforço e rejeição de entradas inválidas.

## Status

- [x] Código/conteúdo
- [x] Testes automatizados
- [ ] Relatório
- [ ] Demo/vídeo (se aplicável)
