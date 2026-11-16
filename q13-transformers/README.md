# Q13: Arquitetura Transformer

O notebook explica o fluxo do Transformer de ponta a ponta: tokenização,
embeddings, codificação posicional, atenção, encoder, decoder e geração de
tokens. Os exemplos numéricos são didáticos e usam pesos aleatórios; não
carregam nem treinam um modelo de linguagem externo.

## Como executar

O notebook usa NumPy, pandas e Matplotlib, já listados em `requirements.txt`.
Para abrir interativamente, instale Jupyter no ambiente Python e execute, na
raiz do repositório:

```powershell
python -m pip install jupyter
python -m jupyter notebook q13-transformers\questao_13.ipynb
```

Também é possível executar as células em ordem no VS Code com a extensão
Jupyter.

## Arquivos

| Arquivo | Conteúdo |
|---|---|
| `questao_13.ipynb` | Explicação conceitual e demonstrações numéricas |

## Status

- [x] Código/conteúdo
- [x] Relatório (no notebook)
- [ ] Demo/vídeo (se aplicável)
