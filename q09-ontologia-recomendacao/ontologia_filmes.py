"""
Q9 - Ontologia de recomendação de filmes em OWL 2 (Lista 2, AB2, IA PPGI 2026.2).

Domínio: filmes, gêneros, pessoas (diretores e atores), idiomas, classificação indicativa e usuários.

A ontologia tem:
  * 26 classes (hierarquias de pessoas, gêneros e classificações, mais 3 classes definidas)
  * 13 propriedades de objeto e 5 de dados (18 no total), com propriedade simétrica e inversas
  * axiomas de disjunção e definições de classe (equivalências)
  * indivíduos: 17 filmes, 4 usuários e as pessoas e gêneros que eles referenciam

Os valores de classificação indicativa e de idade mínima são ILUSTRATIVOS (para fins didáticos).
Os títulos, anos, diretores e elencos são de filmes reais.

Uso:
    python3 ontologia_filmes.py     # monta a ontologia, salva data/filmes.owl, roda o raciocinador e mostra inferências
"""

from __future__ import annotations

from pathlib import Path

from owlready2 import (
    AllDisjoint,
    FunctionalProperty,
    ObjectProperty,
    DataProperty,
    SymmetricProperty,
    Thing,
    World,
    sync_reasoner_hermit,
)

PASTA = Path(__file__).resolve().parent
CAMINHO_OWL = PASTA / "data" / "filmes.owl"
IRI_PADRAO = "http://exemplo.org/recomendacao-filmes.owl"

GENEROS = ["Acao", "Aventura", "Animacao", "Comedia", "Crime", "Drama",
           "FiccaoCientifica", "Musical", "Romance", "Suspense", "Terror"]

# (id, título, ano, gêneros, id do diretor, ids dos atores, idioma, classificação)
FILMES = [
    ("poderoso_chefao", "O Poderoso Chefão", 1972, ["Drama", "Crime"], "francis_coppola",
     ["marlon_brando", "al_pacino"], "Ingles", "Maior16"),
    ("pulp_fiction", "Pulp Fiction", 1994, ["Crime", "Drama"], "quentin_tarantino",
     ["samuel_l_jackson", "john_travolta"], "Ingles", "Maior18"),
    ("silencio_dos_inocentes", "O Silêncio dos Inocentes", 1991, ["Suspense", "Terror", "Crime"],
     "jonathan_demme", ["jodie_foster", "anthony_hopkins"], "Ingles", "Maior16"),
    ("o_iluminado", "O Iluminado", 1980, ["Terror", "Suspense"], "stanley_kubrick",
     ["jack_nicholson"], "Ingles", "Maior16"),
    ("matrix", "Matrix", 1999, ["Acao", "FiccaoCientifica"], "lana_wachowski",
     ["keanu_reeves", "carrie_anne_moss"], "Ingles", "Maior16"),
    ("interestelar", "Interestelar", 2014, ["FiccaoCientifica", "Drama"], "christopher_nolan",
     ["matthew_mcconaughey", "anne_hathaway"], "Ingles", "Maior12"),
    ("jurassic_park", "Jurassic Park", 1993, ["FiccaoCientifica", "Acao", "Aventura"],
     "steven_spielberg", ["sam_neill"], "Ingles", "Maior12"),
    ("toy_story", "Toy Story", 1995, ["Animacao", "Comedia"], "john_lasseter",
     ["tom_hanks"], "Ingles", "Livre"),
    ("up", "Up - Altas Aventuras", 2009, ["Animacao", "Aventura"], "pete_docter",
     ["ed_asner"], "Ingles", "Livre"),
    ("titanic", "Titanic", 1997, ["Romance", "Drama"], "james_cameron",
     ["leonardo_dicaprio", "kate_winslet"], "Ingles", "Maior12"),
    ("la_la_land", "La La Land", 2016, ["Musical", "Romance"], "damien_chazelle",
     ["ryan_gosling", "emma_stone"], "Ingles", "Maior12"),
    ("se_beber_nao_case", "Se Beber, Não Case!", 2009, ["Comedia"], "todd_phillips",
     ["bradley_cooper"], "Ingles", "Maior16"),
    ("parasita", "Parasita", 2019, ["Suspense", "Drama"], "bong_joon_ho",
     ["song_kang_ho"], "Coreano", "Maior16"),
    ("gladiador", "Gladiador", 2000, ["Acao", "Drama"], "ridley_scott",
     ["russell_crowe"], "Ingles", "Maior16"),
    ("forrest_gump", "Forrest Gump", 1994, ["Drama", "Romance"], "robert_zemeckis",
     ["tom_hanks"], "Ingles", "Maior12"),
    ("clube_da_luta", "Clube da Luta", 1999, ["Suspense", "Drama"], "david_fincher",
     ["brad_pitt", "edward_norton"], "Ingles", "Maior18"),
    ("amelie", "Amélie", 2001, ["Comedia", "Romance"], "jean_pierre_jeunet",
     ["audrey_tautou"], "Frances", "Maior12"),
]

# Nome de exibição das pessoas (ids sem acento para os nomes dos indivíduos).
NOMES_PESSOAS = {
    "francis_coppola": "Francis Ford Coppola", "marlon_brando": "Marlon Brando",
    "al_pacino": "Al Pacino", "quentin_tarantino": "Quentin Tarantino",
    "samuel_l_jackson": "Samuel L. Jackson", "john_travolta": "John Travolta",
    "jonathan_demme": "Jonathan Demme", "jodie_foster": "Jodie Foster",
    "anthony_hopkins": "Anthony Hopkins", "stanley_kubrick": "Stanley Kubrick",
    "jack_nicholson": "Jack Nicholson", "lana_wachowski": "Lana Wachowski",
    "keanu_reeves": "Keanu Reeves", "carrie_anne_moss": "Carrie-Anne Moss",
    "christopher_nolan": "Christopher Nolan", "matthew_mcconaughey": "Matthew McConaughey",
    "anne_hathaway": "Anne Hathaway", "steven_spielberg": "Steven Spielberg",
    "sam_neill": "Sam Neill", "john_lasseter": "John Lasseter", "tom_hanks": "Tom Hanks",
    "pete_docter": "Pete Docter", "ed_asner": "Ed Asner", "james_cameron": "James Cameron",
    "leonardo_dicaprio": "Leonardo DiCaprio", "kate_winslet": "Kate Winslet",
    "damien_chazelle": "Damien Chazelle", "ryan_gosling": "Ryan Gosling",
    "emma_stone": "Emma Stone", "todd_phillips": "Todd Phillips",
    "bradley_cooper": "Bradley Cooper", "bong_joon_ho": "Bong Joon-ho",
    "song_kang_ho": "Song Kang-ho", "ridley_scott": "Ridley Scott",
    "russell_crowe": "Russell Crowe", "robert_zemeckis": "Robert Zemeckis",
    "david_fincher": "David Fincher", "brad_pitt": "Brad Pitt",
    "edward_norton": "Edward Norton", "jean_pierre_jeunet": "Jean-Pierre Jeunet",
    "audrey_tautou": "Audrey Tautou",
}

DIRETORES = {"francis_coppola", "quentin_tarantino", "jonathan_demme", "stanley_kubrick",
             "lana_wachowski", "christopher_nolan", "steven_spielberg", "john_lasseter",
             "pete_docter", "james_cameron", "damien_chazelle", "todd_phillips",
             "bong_joon_ho", "ridley_scott", "robert_zemeckis", "david_fincher",
             "jean_pierre_jeunet"}

# Usuários: (id, nome, idade, gêneros de que gosta, diretores favoritos, atores favoritos, já assistiram)
USUARIOS = [
    ("ana", "Ana", 28, ["Terror", "Suspense", "FiccaoCientifica"], ["christopher_nolan"], [],
     ["matrix", "interestelar"]),
    ("bruno", "Bruno", 12, ["Animacao", "Comedia"], [], ["tom_hanks"], ["toy_story"]),
    ("carla", "Carla", 35, ["Romance", "Musical"], [], ["ryan_gosling"], ["titanic"]),
    ("diego", "Diego", 20, ["Crime", "Drama", "Suspense"], ["quentin_tarantino"], [],
     ["poderoso_chefao"]),
]

# Pares de filmes parecidos (a propriedade é simétrica: basta declarar um sentido).
SIMILARES = [
    ("toy_story", "up"), ("titanic", "forrest_gump"), ("silencio_dos_inocentes", "o_iluminado"),
    ("matrix", "interestelar"), ("pulp_fiction", "clube_da_luta"), ("poderoso_chefao", "pulp_fiction"),
]

# Classificação indicativa: idade mínima ILUSTRATIVA
IDADE_MINIMA = {"Livre": 0, "Maior12": 12, "Maior16": 16, "Maior18": 18}


def construir(iri: str = IRI_PADRAO, mundo: World | None = None,
              inconsistente: bool = False):
    """Monta a ontologia. Com `inconsistente=True`, acrescenta uma contradição (para testes)."""
    mundo = mundo or World()
    onto = mundo.get_ontology(iri)

    with onto:
        # ---------------- Classes ----------------
        class Pessoa(Thing): pass
        class Diretor(Pessoa): pass
        class Ator(Pessoa): pass
        class Filme(Thing): pass
        class Genero(Thing): pass
        class Usuario(Thing): pass
        class Idioma(Thing): pass
        class ClassificacaoIndicativa(Thing): pass
        class Livre(ClassificacaoIndicativa): pass
        class Maior12(ClassificacaoIndicativa): pass
        class Maior16(ClassificacaoIndicativa): pass
        class Maior18(ClassificacaoIndicativa): pass

        generos = {nome: type(nome, (Genero,), {"namespace": onto}) for nome in GENEROS}
        Terror = generos["Terror"]
        # Os valores das propriedades são INDIVÍDUOS; cada gênero tem um indivíduo da sua classe.
        generos_ind = {nome: generos[nome](f"genero_{nome}") for nome in GENEROS}

        # Classes definidas por axiomas: as equivalências são declaradas mais abaixo,
        # e o raciocinador preenche as instâncias.
        class FilmeDeTerror(Filme): pass
        class FilmeParaFamilia(Filme): pass
        class FanDeTerror(Usuario): pass

        # ---------------- Propriedades de objeto ----------------
        class temGenero(ObjectProperty):
            domain = [Filme]; range = [Genero]
        class dirigidoPor(ObjectProperty):
            domain = [Filme]; range = [Diretor]
        class temAtor(ObjectProperty):
            domain = [Filme]; range = [Ator]
        class temIdioma(ObjectProperty):
            domain = [Filme]; range = [Idioma]
        class temClassificacao(ObjectProperty, FunctionalProperty):
            domain = [Filme]; range = [ClassificacaoIndicativa]
        class gostaDeGenero(ObjectProperty):
            domain = [Usuario]; range = [Genero]
        class gostaDeDiretor(ObjectProperty):
            domain = [Usuario]; range = [Diretor]
        class gostaDeAtor(ObjectProperty):
            domain = [Usuario]; range = [Ator]
        class viu(ObjectProperty):
            domain = [Usuario]; range = [Filme]
        class similarA(ObjectProperty, SymmetricProperty):
            domain = [Filme]; range = [Filme]
        class dirigiu(ObjectProperty):
            domain = [Diretor]; range = [Filme]
        class atuou(ObjectProperty):
            domain = [Ator]; range = [Filme]
        class filmesDoGenero(ObjectProperty):
            domain = [Genero]; range = [Filme]

        dirigiu.inverse_property = dirigidoPor
        atuou.inverse_property = temAtor
        filmesDoGenero.inverse_property = temGenero

        # ---------------- Propriedades de dados ----------------
        class titulo(DataProperty, FunctionalProperty):
            domain = [Filme]; range = [str]
        class ano(DataProperty, FunctionalProperty):
            domain = [Filme]; range = [int]
        class nome(DataProperty, FunctionalProperty):
            domain = [Pessoa]; range = [str]
        class idadeUsuario(DataProperty, FunctionalProperty):
            domain = [Usuario]; range = [int]
        class idadeMinima(DataProperty, FunctionalProperty):
            domain = [ClassificacaoIndicativa]; range = [int]

        # ---------------- Axiomas ----------------
        AllDisjoint([Filme, Pessoa, Genero, Usuario, Idioma, ClassificacaoIndicativa])
        AllDisjoint([Livre, Maior12, Maior16, Maior18])

        FilmeDeTerror.equivalent_to = [Filme & temGenero.some(Terror)]
        FilmeParaFamilia.equivalent_to = [Filme & temClassificacao.some(Livre | Maior12)]
        FanDeTerror.equivalent_to = [Usuario & gostaDeGenero.some(Terror)]

        # ---------------- Indivíduos: idiomas e classificações ----------------
        ingles = Idioma("Ingles")
        frances = Idioma("Frances")
        coreano = Idioma("Coreano")
        idiomas = {"Ingles": ingles, "Frances": frances, "Coreano": coreano}
        classificacoes = {"Livre": Livre("Livre_ind"), "Maior12": Maior12("Maior12_ind"),
                          "Maior16": Maior16("Maior16_ind"), "Maior18": Maior18("Maior18_ind")}
        for cod, ind in classificacoes.items():
            ind.idadeMinima = IDADE_MINIMA[cod]

        # ---------------- Indivíduos: pessoas ----------------
        pessoas = {}
        for pid, nome_pessoa in NOMES_PESSOAS.items():
            classe = Diretor if pid in DIRETORES else Ator
            indiv = classe(pid)
            indiv.nome = nome_pessoa
            pessoas[pid] = indiv

        # ---------------- Indivíduos: gêneros (já criados como classes) ----------------
        # ---------------- Indivíduos: filmes ----------------
        filmes = {}
        for fid, titulo_f, ano_f, gens, diretor, atores, idioma, classif in FILMES:
            f = Filme(fid)
            f.titulo = titulo_f
            f.ano = ano_f
            f.temGenero = [generos_ind[g] for g in gens]
            f.dirigidoPor = [pessoas[diretor]]
            f.temAtor = [pessoas[a] for a in atores]
            f.temIdioma = [idiomas[idioma]]
            f.temClassificacao = classificacoes[classif]
            filmes[fid] = f

        for a, b in SIMILARES:
            filmes[a].similarA.append(filmes[b])

        # ---------------- Indivíduos: usuários ----------------
        for uid, nome_u, idade, gostos, dirs, atrs, vistos in USUARIOS:
            u = Usuario(uid)
            u.idadeUsuario = idade
            u.gostaDeGenero = [generos_ind[g] for g in gostos]
            u.gostaDeDiretor = [pessoas[d] for d in dirs]
            u.gostaDeAtor = [pessoas[a] for a in atrs]
            u.viu = [filmes[v] for v in vistos]

        if inconsistente:
            # Um indivíduo que é, ao mesmo tempo, Livre e Maior18: classes disjuntas.
            contradicao = Livre("classificacao_contraditoria")
            contradicao.is_a.append(Maior18)

    return onto


def raciocinar(onto) -> None:
    """Roda o raciocinador HermiT (classificação, propriedades inferidas, consistência)."""
    sync_reasoner_hermit(onto, infer_property_values=True)


def demonstrar_inferencias(onto) -> None:
    """Mostra o que o raciocinador concluiu, sem que nada disso tenha sido afirmado à mão."""
    filmes = {f.name: f for f in onto.Filme.instances()}
    print("Classes definidas por axioma (preenchidas pelo raciocinador):")
    for cls in (onto.FilmeDeTerror, onto.FilmeParaFamilia, onto.FanDeTerror):
        nomes = sorted(i.name for i in cls.instances())
        print(f"  {cls.name:<16}({len(nomes)}): {', '.join(nomes)}")

    print("\nPropriedade inversa (dirigiu) inferida a partir de dirigidoPor:")
    print(f"  Christopher Nolan dirigiu: {', '.join(sorted(f.titulo for f in onto.christopher_nolan.dirigiu))}")

    print("\nPropriedade simétrica (similarA):")
    o_iluminado = filmes["o_iluminado"]
    silencio = filmes["silencio_dos_inocentes"]
    print(f"  Asserido: silencio -> o_iluminado. Inferido: o_iluminado similarA "
          f"{[x.titulo for x in o_iluminado.similarA]}")
    print(f"  Confere: silencio em similarA de o_iluminado? {silencio in o_iluminado.similarA}")


def main() -> None:
    onto = construir()
    raciocinar(onto)
    onto.save(file=str(CAMINHO_OWL), format="rdfxml")
    n_classes = len(list(onto.classes()))
    n_obj = len(list(onto.object_properties()))
    n_dat = len(list(onto.data_properties()))
    n_ind = len(list(onto.individuals()))
    print(f"Ontologia: {n_classes} classes, {n_obj} propriedades de objeto, "
          f"{n_dat} de dados, {n_ind} indivíduos.")
    print(f"Arquivo salvo: {CAMINHO_OWL}\n")
    demonstrar_inferencias(onto)


if __name__ == "__main__":
    main()
