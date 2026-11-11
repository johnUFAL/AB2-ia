"""
Q14 - Knowledge Graph de recomendação de filmes: representação, inferência e explicação.

Um Knowledge Graph é um conjunto de triplas (sujeito, predicado, objeto). Este módulo:
  * guarda as triplas afirmadas e as inferidas, com a procedência de cada inferência
    (qual regra gerou a tripla e quais triplas foram usadas como premissas);
  * aplica regras de inferência por encadeamento para frente (forward chaining) até não surgir
    nenhum fato novo (ponto fixo);
  * recomenda filmes por caminhos no grafo (gosto por gênero, diretor, ator e colaborativo);
  * explica por que um fato foi inferido;
  * exporta o grafo para Cypher (Neo4j), para ser carregado no banco.

O domínio é o mesmo da Q9 (filmes). Os dados vêm de data/catalogo_filmes.json.

Uso:
    python3 kg.py                    # monta o grafo, raciocina, recomenda e explica
    python3 kg.py --cypher           # gera data/grafo_filmes.cypher para o Neo4j
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable

PASTA = Path(__file__).resolve().parent
CATALOGO = PASTA / "data" / "catalogo_filmes.json"
CYPHER = PASTA / "data" / "grafo_filmes.cypher"

Tripla = tuple[str, str, str]
TIPO = "tipo"            # predicado "é instância de"
SUBCLASSE = "subClasseDe"  # predicado "é subclasse de"

# Predicados cujo objeto é um valor literal (texto ou número), e não uma entidade.
LITERAIS = {"titulo", "ano", "nome", "idade", "idadeMinima"}

PESOS_CAMINHO = {"genero": 2, "diretor": 3, "ator": 2, "similar": 1, "colaborativo": 1}


# ---------------------------------------------------------------------------
# Grafo com procedência
# ---------------------------------------------------------------------------


@dataclass
class GrafoConhecimento:
    afirmadas: set[Tripla] = field(default_factory=set)
    # tripla inferida -> (nome da regra, premissas usadas)
    inferidas: dict[Tripla, tuple[str, list[Tripla]]] = field(default_factory=dict)

    def adicionar(self, s: str, p: str, o: str) -> None:
        self.afirmadas.add((s, p, o))

    def contem(self, t: Tripla) -> bool:
        return t in self.afirmadas or t in self.inferidas

    def todas(self) -> set[Tripla]:
        return self.afirmadas | set(self.inferidas)

    def buscar(self, s: str | None = None, p: str | None = None, o: str | None = None) -> list[Tripla]:
        """Consulta por padrão: None é curinga."""
        return [t for t in self.todas()
                if (s is None or t[0] == s) and (p is None or t[1] == p) and (o is None or t[2] == o)]

    def objetos(self, s: str, p: str) -> list[str]:
        return [t[2] for t in self.buscar(s=s, p=p)]

    def sujeitos(self, p: str, o: str) -> list[str]:
        return [t[0] for t in self.buscar(p=p, o=o)]


# ---------------------------------------------------------------------------
# Regras de inferência
#
# Cada regra recebe o grafo e devolve pares (tripla nova, premissas usadas).
# ---------------------------------------------------------------------------

Regra = Callable[[GrafoConhecimento], Iterable[tuple[Tripla, list[Tripla]]]]


def regra_inversa(p: str, q: str) -> Regra:
    """(x p y)  ⇒  (y q x). Ex.: (filme dirigidoPor diretor) ⇒ (diretor dirigiu filme)."""
    def regra(g: GrafoConhecimento):
        for (x, _, y) in g.buscar(p=p):
            yield (y, q, x), [(x, p, y)]
    return regra


def regra_simetrica(p: str) -> Regra:
    """(x p y)  ⇒  (y p x)."""
    def regra(g: GrafoConhecimento):
        for (x, _, y) in g.buscar(p=p):
            yield (y, p, x), [(x, p, y)]
    return regra


def regra_subclasse(g: GrafoConhecimento):
    """Transitividade de subClasseDe e herança de tipo: (x tipo A), (A subClasseDe B) ⇒ (x tipo B)."""
    for (a, _, b) in g.buscar(p=SUBCLASSE):
        for (x, _, _) in g.buscar(p=TIPO, o=a):
            yield (x, TIPO, b), [(x, TIPO, a), (a, SUBCLASSE, b)]
        for (c, _, d) in g.buscar(p=SUBCLASSE, o=None):
            if c == b:
                yield (a, SUBCLASSE, d), [(a, SUBCLASSE, b), (b, SUBCLASSE, d)]


def regra_definida(p: str, valor: str, classe: str) -> Regra:
    """Classe definida por condição: (x p valor) ⇒ (x tipo classe).

    Ex.: quem tem gênero Terror entra na classe FilmeDeTerror, e quem gosta de Terror entra em FanDeTerror.
    """
    def regra(g: GrafoConhecimento):
        for (x, _, _) in g.buscar(p=p, o=valor):
            yield (x, TIPO, classe), [(x, p, valor)]
    return regra


# Conjunto de regras da ontologia de filmes (mesmas definições da Q9).
REGRAS: list[tuple[str, Regra]] = [
    ("subclasse", regra_subclasse),
    ("inversa dirigidoPor->dirigiu", regra_inversa("dirigidoPor", "dirigiu")),
    ("inversa dirigiu->dirigidoPor", regra_inversa("dirigiu", "dirigidoPor")),
    ("inversa temAtor->atuou", regra_inversa("temAtor", "atuou")),
    ("inversa temGenero->filmesDoGenero", regra_inversa("temGenero", "filmesDoGenero")),
    ("simetrica similarA", regra_simetrica("similarA")),
    ("definida FilmeDeTerror (temGenero Terror)", regra_definida("temGenero", "Terror", "FilmeDeTerror")),
    ("definida FanDeTerror (gostaDeGenero Terror)", regra_definida("gostaDeGenero", "Terror", "FanDeTerror")),
    ("definida FilmeParaFamilia (Livre)", regra_definida("temClassificacao", "Livre", "FilmeParaFamilia")),
    ("definida FilmeParaFamilia (Maior12)", regra_definida("temClassificacao", "Maior12", "FilmeParaFamilia")),
]


def raciocinar(g: GrafoConhecimento, regras: list[tuple[str, Regra]] = REGRAS) -> int:
    """Forward chaining até o ponto fixo. Devolve quantas triplas foram inferidas."""
    novas = 0
    mudou = True
    while mudou:
        mudou = False
        for nome, regra in regras:
            for tripla, premissas in list(regra(g)):
                if not g.contem(tripla):
                    g.inferidas[tripla] = (nome, premissas)
                    novas += 1
                    mudou = True
    return novas


def explicar(g: GrafoConhecimento, tripla: Tripla, profundidade: int = 2, nivel: int = 0) -> list[str]:
    """Explica uma tripla: se foi afirmada, ou qual regra a inferiu e a partir de quais premissas."""
    indent = "  " * nivel
    if tripla in g.afirmadas:
        return [f"{indent}{tripla[0]} {tripla[1]} {tripla[2]}   [afirmada]"]
    if tripla not in g.inferidas:
        return [f"{indent}{tripla[0]} {tripla[1]} {tripla[2]}   [não existe no grafo]"]
    regra, premissas = g.inferidas[tripla]
    linhas = [f"{indent}{tripla[0]} {tripla[1]} {tripla[2]}   [inferida por: {regra}]"]
    if nivel < profundidade:
        for pr in premissas:
            linhas += explicar(g, pr, profundidade, nivel + 1)
    return linhas


# ---------------------------------------------------------------------------
# Construção do grafo a partir do catálogo
# ---------------------------------------------------------------------------


def construir(catalogo_path: Path = CATALOGO) -> GrafoConhecimento:
    dados = json.loads(catalogo_path.read_text(encoding="utf-8"))
    g = GrafoConhecimento()

    # Esquema: hierarquia de classes
    for sub, sup in [("Diretor", "Pessoa"), ("Ator", "Pessoa"),
                     ("Livre", "ClassificacaoIndicativa"), ("Maior12", "ClassificacaoIndicativa"),
                     ("Maior16", "ClassificacaoIndicativa"), ("Maior18", "ClassificacaoIndicativa")]:
        g.adicionar(sub, SUBCLASSE, sup)
    for classif, idade in dados["idade_minima"].items():
        g.adicionar(classif, "idadeMinima", str(idade))

    # Gêneros, idiomas
    generos = sorted({gen for f in dados["filmes"] for gen in f["generos"]}
                     | {gen for u in dados["usuarios"] for gen in u["gostos"]})
    for gen in generos:
        g.adicionar(gen, TIPO, "Genero")
    for idioma in ["Ingles", "Frances", "Coreano"]:
        g.adicionar(idioma, TIPO, "Idioma")

    # Pessoas (diretores e atores)
    for pid, nome in dados["pessoas"].items():
        g.adicionar(pid, TIPO, "Diretor" if pid in dados["diretores"] else "Ator")
        g.adicionar(pid, "nome", nome)

    # Filmes
    for f in dados["filmes"]:
        fid = f["id"]
        g.adicionar(fid, TIPO, "Filme")
        g.adicionar(fid, "titulo", f["titulo"])
        g.adicionar(fid, "ano", str(f["ano"]))
        for gen in f["generos"]:
            g.adicionar(fid, "temGenero", gen)
        g.adicionar(fid, "dirigidoPor", f["diretor"])
        for a in f["atores"]:
            g.adicionar(fid, "temAtor", a)
        g.adicionar(fid, "temIdioma", f["idioma"])
        g.adicionar(fid, "temClassificacao", f["classificacao"])

    for a, b in dados["similares"]:
        g.adicionar(a, "similarA", b)

    # Usuários
    for u in dados["usuarios"]:
        uid = u["id"]
        g.adicionar(uid, TIPO, "Usuario")
        g.adicionar(uid, "nome", u["nome"])
        g.adicionar(uid, "idade", str(u["idade"]))
        for gen in u["gostos"]:
            g.adicionar(uid, "gostaDeGenero", gen)
        for d in u["diretores"]:
            g.adicionar(uid, "gostaDeDiretor", d)
        for a in u["atores"]:
            g.adicionar(uid, "gostaDeAtor", a)
        for v in u["viu"]:
            g.adicionar(uid, "viu", v)

    return g


# ---------------------------------------------------------------------------
# Recomendação por caminhos no grafo
# ---------------------------------------------------------------------------


@dataclass
class Recomendacao:
    filme: str
    titulo: str
    pontos: int
    caminhos: list[str] = field(default_factory=list)


def _titulo(g: GrafoConhecimento, f: str) -> str:
    return (g.objetos(f, "titulo") or [f])[0]


def _nome(g: GrafoConhecimento, x: str) -> str:
    return (g.objetos(x, "nome") or [x])[0]


def recomendar(g: GrafoConhecimento, uid: str, k: int = 5) -> list[Recomendacao]:
    """Cada caminho que liga o usuário a um filme soma pontos. Os motivos são os caminhos."""
    vistos = set(g.objetos(uid, "viu"))
    pontos: dict[str, int] = defaultdict(int)
    caminhos: dict[str, list[str]] = defaultdict(list)

    def somar(filme: str, peso: int, texto: str) -> None:
        pontos[filme] += peso
        caminhos[filme].append(texto)

    # Caminho 1: usuário -gostaDeGenero-> gênero <-temGenero- filme
    for gen in g.objetos(uid, "gostaDeGenero"):
        for f in g.sujeitos("temGenero", gen):
            if f not in vistos:
                somar(f, PESOS_CAMINHO["genero"], f"gosta de {gen} (gostaDeGenero → temGenero)")

    # Caminho 2: usuário -gostaDeDiretor-> diretor <-dirigidoPor- filme
    for d in g.objetos(uid, "gostaDeDiretor"):
        for f in g.sujeitos("dirigidoPor", d):
            if f not in vistos:
                somar(f, PESOS_CAMINHO["diretor"],
                      f"dirigido por {_nome(g, d)} (gostaDeDiretor → dirigidoPor)")

    # Caminho 3: usuário -gostaDeAtor-> ator <-temAtor- filme
    for a in g.objetos(uid, "gostaDeAtor"):
        for f in g.sujeitos("temAtor", a):
            if f not in vistos:
                somar(f, PESOS_CAMINHO["ator"], f"com {_nome(g, a)} (gostaDeAtor → temAtor)")

    # Caminho 4 (colaborativo): usuário -viu-> f0 <-viu- outro -viu-> filme
    for f0 in vistos:
        for outro in g.sujeitos("viu", f0):
            if outro == uid:
                continue
            for f in g.objetos(outro, "viu"):
                if f not in vistos:
                    somar(f, PESOS_CAMINHO["colaborativo"],
                          f"{_nome(g, outro)} viu {_titulo(g, f0)} e também viu este (viu → viu)")

    # Caminho 5 (parecido): usuário -viu-> f0 <-similarA- filme (similarA é simétrica)
    for f0 in vistos:
        for f in g.sujeitos("similarA", f0):
            if f not in vistos:
                somar(f, PESOS_CAMINHO["similar"], f"parecido com {_titulo(g, f0)}, que você já viu (similarA)")

    # Restrição de idade: classificação do filme (temClassificacao → idadeMinima)
    idade = int(g.objetos(uid, "idade")[0])
    resultados = []
    for f, p in pontos.items():
        classif = g.objetos(f, "temClassificacao")[0]
        if int(g.objetos(classif, "idadeMinima")[0]) > idade:
            continue
        resultados.append(Recomendacao(f, _titulo(g, f), p, caminhos[f]))

    resultados.sort(key=lambda r: (-r.pontos, r.titulo))
    return resultados[:k]


# ---------------------------------------------------------------------------
# Exportação para Neo4j (Cypher)
# ---------------------------------------------------------------------------


def _cypher_str(valor: str) -> str:
    return json.dumps(valor, ensure_ascii=False)


def exportar_cypher(g: GrafoConhecimento, caminho: Path = CYPHER) -> int:
    """Gera um script Cypher com as triplas afirmadas.

    Entidades viram nós :Entidade {id}. Predicados literais viram propriedades.
    Os outros predicados viram relacionamentos. As triplas inferidas não são exportadas: o Neo4j
    deve reproduzir a inferência com consultas (ver as consultas no README).
    """
    linhas = ["// Gerado por kg.py (NÃO executado no ambiente de desenvolvimento: ver README).",
              "// ATENÇÃO: o comando abaixo apaga TODOS os nós e relações do banco antes de carregar.",
              "// Carregue com: cypher-shell -f grafo_filmes.cypher",
              "MATCH (n) DETACH DELETE n;"]
    entidades = sorted({s for s, _, _ in g.afirmadas} | {o for _, p, o in g.afirmadas
                                                         if p not in LITERAIS})
    for e in entidades:
        linhas.append(f"MERGE (:Entidade {{id: {_cypher_str(e)}}});")
    for s, p, o in sorted(g.afirmadas):
        if p in LITERAIS:
            linhas.append(f"MATCH (n:Entidade {{id: {_cypher_str(s)}}}) SET n.{p} = {_cypher_str(o)};")
        elif p == TIPO:
            linhas.append(f"MATCH (n:Entidade {{id: {_cypher_str(s)}}}) SET n:{o};")
        else:
            rel = "SUBCLASSE_DE" if p == SUBCLASSE else p
            linhas.append(f"MATCH (a:Entidade {{id: {_cypher_str(s)}}}), (b:Entidade {{id: {_cypher_str(o)}}}) "
                          f"MERGE (a)-[:{rel}]->(b);")
    caminho.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    return len(linhas)


# ---------------------------------------------------------------------------
# Apresentação
# ---------------------------------------------------------------------------


def imprimir_resumo(g: GrafoConhecimento, n_inferidas: int) -> None:
    print(f"Triplas afirmadas: {len(g.afirmadas)}")
    print(f"Triplas inferidas pelas regras: {n_inferidas}")
    print(f"Total no grafo: {len(g.todas())}")


def main() -> None:
    g = construir()
    if "--cypher" in sys.argv:
        n = exportar_cypher(g)
        print(f"Script Cypher gerado em {CYPHER} ({n} comandos).")
        return

    imprimir_resumo(g, raciocinar(g))

    print("\n--- Classes definidas por regra (inferidas) ---")
    for classe in ["FilmeDeTerror", "FilmeParaFamilia", "FanDeTerror"]:
        membros = sorted(g.sujeitos("tipo", classe))
        print(f"  {classe} ({len(membros)}): {', '.join(membros)}")

    print("\n--- Explicação de inferências ---")
    for tripla in [("ana", "tipo", "FanDeTerror"),
                   ("silencio_dos_inocentes", "tipo", "FilmeDeTerror"),
                   ("christopher_nolan", "dirigiu", "interestelar")]:
        print("\n".join(explicar(g, tripla)))
        print()

    for uid in ["ana", "bruno"]:
        print(f"--- Recomendações para {uid} (por caminhos no grafo) ---")
        for i, r in enumerate(recomendar(g, uid), 1):
            print(f"  {i}. {r.titulo} ({r.pontos} pontos)")
            for c in r.caminhos:
                print(f"       {c}")
        print()


if __name__ == "__main__":
    main()
