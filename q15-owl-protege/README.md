# Q15: Aplicação com ontologia OWL 2

O trabalho modela um departamento universitário com professores, alunos,
disciplinas, projetos e laboratórios. O notebook define axiomas e indivíduos,
executa raciocínio e consultas e demonstra validação de inconsistências e a
hipótese do mundo aberto. A ontologia serializada está em `universidade.owl`.

## Como executar

As bibliotecas `owlready2` e `pandas` estão listadas em `requirements.txt`.
Para executar interativamente, instale Jupyter no ambiente e abra o notebook
a partir desta pasta:

```powershell
python -m pip install jupyter
Set-Location q15-owl-protege
python -m jupyter notebook questao_15.ipynb
```

O reasoner HermiT utilizado pela demonstração requer uma instalação de Java
compatível. As células que executam raciocínio devem ser rodadas em ordem. A
API do reasoner não requer uma chave de serviço externa.

## Arquivos

| Arquivo | Conteúdo |
|---|---|
| `questao_15.ipynb` | Modelo, axiomas, consultas e exemplos de raciocínio |
| `universidade.owl` | Ontologia OWL 2 serializada |

## Status

- [x] Código/conteúdo
- [x] Relatório (no notebook)
- [ ] Demo/vídeo (se aplicável)
