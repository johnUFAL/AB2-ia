"""Testes do knowledge graph (Q14). Executar com: python3 -m unittest -v test_kg.py"""

import unittest

import kg
from kg import GrafoConhecimento, raciocinar, recomendar, explicar, construir


class RegrasBasicas(unittest.TestCase):
    """Cada regra de inferência isolada, em um grafo pequeno."""

    def test_heranca_de_subclasse(self):
        g = GrafoConhecimento()
        g.adicionar("A", kg.SUBCLASSE, "B")
        g.adicionar("B", kg.SUBCLASSE, "C")
        g.adicionar("x", kg.TIPO, "A")
        raciocinar(g)
        self.assertIn(("x", kg.TIPO, "B"), g.todas())
        self.assertIn(("x", kg.TIPO, "C"), g.todas())

    def test_transitividade_de_subclasse(self):
        g = GrafoConhecimento()
        g.adicionar("A", kg.SUBCLASSE, "B")
        g.adicionar("B", kg.SUBCLASSE, "C")
        raciocinar(g)
        self.assertIn(("A", kg.SUBCLASSE, "C"), g.todas())

    def test_inversa(self):
        g = GrafoConhecimento()
        g.adicionar("filme", "dirigidoPor", "diretor")
        raciocinar(g)
        self.assertIn(("diretor", "dirigiu", "filme"), g.todas())

    def test_simetrica(self):
        g = GrafoConhecimento()
        g.adicionar("a", "similarA", "b")
        raciocinar(g)
        self.assertIn(("b", "similarA", "a"), g.todas())

    def test_classe_definida_por_condicao(self):
        g = GrafoConhecimento()
        g.adicionar("f", "temGenero", "Terror")
        g.adicionar("g", "temGenero", "Comedia")
        raciocinar(g)
        self.assertIn(("f", kg.TIPO, "FilmeDeTerror"), g.todas())
        self.assertNotIn(("g", kg.TIPO, "FilmeDeTerror"), g.todas())

    def test_ponto_fixo(self):
        """Depois de saturar, uma nova rodada não infere nada."""
        g = GrafoConhecimento()
        g.adicionar("A", kg.SUBCLASSE, "B")
        g.adicionar("B", kg.SUBCLASSE, "C")
        g.adicionar("x", kg.TIPO, "A")
        raciocinar(g)
        self.assertEqual(raciocinar(g), 0)

    def test_nao_infere_o_que_ja_e_afirmado(self):
        g = GrafoConhecimento()
        g.adicionar("a", "similarA", "b")
        g.adicionar("b", "similarA", "a")
        self.assertEqual(raciocinar(g), 0)


class GrafoDeFilmes(unittest.TestCase):
    """Inferências sobre o catálogo real (mesmas definições da Q9)."""

    @classmethod
    def setUpClass(cls):
        cls.g = construir()
        raciocinar(cls.g)

    def test_classes_definidas(self):
        self.assertEqual(set(self.g.sujeitos(kg.TIPO, "FilmeDeTerror")),
                         {"o_iluminado", "silencio_dos_inocentes"})
        self.assertEqual(set(self.g.sujeitos(kg.TIPO, "FanDeTerror")), {"ana"})
        self.assertEqual(set(self.g.sujeitos(kg.TIPO, "FilmeParaFamilia")),
                         {"toy_story", "up", "titanic", "forrest_gump", "la_la_land",
                          "interestelar", "jurassic_park", "amelie"})

    def test_pessoa_por_subclasse(self):
        self.assertIn(("christopher_nolan", kg.TIPO, "Pessoa"), self.g.todas())

    def test_diretor_inverso(self):
        self.assertIn(("christopher_nolan", "dirigiu", "interestelar"), self.g.todas())

    def test_explicacao_de_inferencia(self):
        linhas = explicar(self.g, ("ana", kg.TIPO, "FanDeTerror"))
        self.assertIn("inferida por: definida FanDeTerror (gostaDeGenero Terror)", linhas[0])
        self.assertIn("[afirmada]", linhas[1])

    def test_explicacao_de_afirmada(self):
        linhas = explicar(self.g, ("ana", "gostaDeGenero", "Terror"))
        self.assertEqual(len(linhas), 1)
        self.assertIn("[afirmada]", linhas[0])

    def test_explicacao_de_tripla_inexistente(self):
        linhas = explicar(self.g, ("ana", "viu", "nada"))
        self.assertIn("não existe", linhas[0])

    def test_recomendacoes_batem_com_q9(self):
        esperado = {
            "ana": [("O Iluminado", 4), ("O Silêncio dos Inocentes", 4), ("Clube da Luta", 2),
                    ("Jurassic Park", 2), ("Parasita", 2)],
            "bruno": [("Up - Altas Aventuras", 3), ("Amélie", 2), ("Forrest Gump", 2)],
            "carla": [("La La Land", 6), ("Forrest Gump", 3), ("Amélie", 2)],
            "diego": [("Pulp Fiction", 8), ("Clube da Luta", 4), ("O Silêncio dos Inocentes", 4),
                      ("Parasita", 4), ("Forrest Gump", 2)],
        }
        for uid, lista in esperado.items():
            with self.subTest(usuario=uid):
                obtido = [(r.titulo, r.pontos) for r in recomendar(self.g, uid)]
                self.assertEqual(obtido, lista)

    def test_nao_recomenda_filme_ja_visto(self):
        for uid in ["ana", "bruno", "carla", "diego"]:
            vistos = set(self.g.objetos(uid, "viu"))
            for r in recomendar(self.g, uid, k=50):
                self.assertNotIn(r.filme, vistos)

    def test_respeita_classificacao_indicativa(self):
        idade = {uid: int(self.g.objetos(uid, "idade")[0]) for uid in ["ana", "bruno", "carla", "diego"]}
        for uid in idade:
            for r in recomendar(self.g, uid, k=50):
                classif = self.g.objetos(r.filme, "temClassificacao")[0]
                minima = int(self.g.objetos(classif, "idadeMinima")[0])
                self.assertLessEqual(minima, idade[uid], f"{uid} recebeu {r.titulo} ({classif})")

    def test_motivos_do_bruno_incluem_caminho_de_similaridade(self):
        up = next(r for r in recomendar(self.g, "bruno") if r.filme == "up")
        self.assertTrue(any("similarA" in m for m in up.caminhos))
        self.assertTrue(any("gosta de Animacao" in m for m in up.caminhos))


class Cypher(unittest.TestCase):

    def test_exporta_so_triplas_afirmadas(self):
        g = construir()
        raciocinar(g)
        destino = kg.PASTA / "data" / "_teste_export.cypher"
        try:
            kg.exportar_cypher(g, destino)
            texto = destino.read_text(encoding="utf-8")
        finally:
            destino.unlink(missing_ok=True)
        self.assertIn('MERGE (:Entidade {id: "ana"})', texto)
        self.assertNotIn("SET n:FanDeTerror", texto)   # classe inferida: não deve sair
        self.assertNotIn("[:dirigiu]", texto)          # inferida
        self.assertIn("[:dirigidoPor]", texto)         # afirmada
        self.assertIn("SET n:Filme", texto)


if __name__ == "__main__":
    unittest.main()
