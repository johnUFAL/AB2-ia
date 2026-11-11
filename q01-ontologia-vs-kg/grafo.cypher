MERGE (g:Genero {nome: 'Acao'})
MERGE (d:Diretor:Pessoa {nome: 'Lana Wachowski'})
MERGE (f:Filme {nome: 'Matrix', anoLancamento: 1999})
MERGE (d)-[:DIRIGIU]->(f)
MERGE (f)-[:TEM_GENERO]->(g)
RETURN d, f, g;

MATCH (f:Filme)-[:TEM_GENERO]->(:Genero {nome: 'Acao'})
SET f:FilmeDeAcao;

MATCH (d:Diretor)-[r:DIRIGIU]->(f:Filme)-[:TEM_GENERO]->(g:Genero)
RETURN d.nome AS diretor, type(r) AS relacao, f.nome AS filme,
       f.anoLancamento AS ano, g.nome AS genero;

MATCH (f:FilmeDeAcao)
RETURN f.nome AS filmeDeAcao;
