// Carga: indivíduos, labels e relações correspondentes aos fatos OWL.
MERGE (g:Genero {nome: 'Acao'})
MERGE (d:Diretor:Pessoa {nome: 'Lana Wachowski'})
MERGE (f:Filme {nome: 'Matrix', anoLancamento: 1999})
MERGE (d)-[:DIRIGIU]->(f)
MERGE (f)-[:TEM_GENERO]->(g);

// Inferência explicitada: materializa em label a regra FilmeDeAcao equivalente
// a "temGenero Acao". Um property graph não aplica esse axioma OWL sozinho.
MATCH (f:Filme)-[:TEM_GENERO]->(:Genero {nome: 'Acao'})
SET f:FilmeDeAcao;

// Consultas para conferir os fatos e o tipo materializado.
MATCH (d:Diretor)-[r:DIRIGIU]->(f:Filme)-[:TEM_GENERO]->(g:Genero)
RETURN d.nome AS diretor, type(r) AS relacao, f.nome AS filme,
       f.anoLancamento AS ano, g.nome AS genero;

MATCH (f:FilmeDeAcao)
RETURN f.nome AS filmeDeAcao;
