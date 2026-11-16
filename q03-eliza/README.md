# Q3: ELIZA em português

Implementação reduzida do ELIZA, inspirada no algoritmo de Joseph Weizenbaum.
O programa aplica palavras-chave com prioridades, transforma pronomes,
seleciona respostas de remontagem e mantém uma pequena memória de falas.

## Como executar

Na raiz do repositório:

```powershell
python q03-eliza\eliza.py
```

Digite `tchau` ou `adeus` para encerrar.

## Testes

```powershell
python -m unittest discover -s q03-eliza -p "test_*.py" -v
```

Os testes cobrem a seleção de respostas, a transformação da fala, a memória e
o encerramento da conversa.

## Status

- [x] Código/conteúdo
- [x] Testes automatizados
- [x] Relatório (este README)
- [ ] Demo/vídeo (se aplicável)
