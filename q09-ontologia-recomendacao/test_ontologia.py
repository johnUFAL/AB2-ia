"""Testes da Q9. Rodar com:  python3 -m unittest -v   (usa o HermiT; precisa de Java)"""

import unittest

from owlready2 import World

from ontologia_filmes import CAMINHO_OWL, construir, raciocinar
from recomendador import carregar, individuo, recomendar


class TestOntologia(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.onto = construir()
        raciocinar(cls.onto)

    def nomes(self, classe):
        return {i.name for i in classe.instances()}

    def test_numero_de_classes_e_propriedades(self):
        self.assertGreaterEqual(len(list(self.onto.classes())), 10)
        total = len(list(self.onto.object_properties())) + len(list(self.onto.data_properties()))
        self.assertGreaterEqual(total, 15)
        self.assertEqual(len(list(self.onto.object_properties())), 13)
        self.assertEqual(len(list(self.onto.data_properties())), 5)

    def test_hierarquia(self):
        self.assertIn(self.onto.Diretor, self.onto.Pessoa.subclasses())
        self.assertIn(self.onto.Ator, self.onto.Pessoa.subclasses())
        self.assertIn(self.onto.Terror, self.onto.Genero.subclasses())
        self.assertEqual(len(list(self.onto.ClassificacaoIndicativa.subclasses())), 4)

    def test_inferencia_filmes_de_terror(self):
        self.assertEqual(self.nomes(self.onto.FilmeDeTerror),
                         {"o_iluminado", "silencio_dos_inocentes"})

    def test_inferencia_filmes_para_familia(self):
        esperado = {"toy_story", "up", "titanic", "forrest_gump", "la_la_land",
                    "interestelar", "jurassic_park", "amelie"}
        self.assertEqual(self.nomes(self.onto.FilmeParaFamilia), esperado)

    def test_inferencia_fa_de_terror(self):
        self.assertEqual(self.nomes(self.onto.FanDeTerror), {"ana"})

    def test_propriedade_inversa(self):
        titulos = {f.titulo for f in self.onto.christopher_nolan.dirigiu}
        self.assertEqual(titulos, {"Interestelar"})

    def test_propriedade_simetrica(self):
        o_iluminado = self.onto.search_one(iri="*#o_iluminado")
        silencio = self.onto.search_one(iri="*#silencio_dos_inocentes")
        self.assertIn(silencio, o_iluminado.similarA)

    def test_ontologia_inconsistente_e_detectada(self):
        mundo = World()
        ruim = construir(iri="http://exemplo.org/inconsistente.owl", mundo=mundo, inconsistente=True)
        with self.assertRaises(Exception) as ctx:
            raciocinar(ruim)
        self.assertIn("Inconsistent", type(ctx.exception).__name__)


class TestRecomendacao(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.onto = carregar()

    def test_arquivo_owl_existe(self):
        self.assertTrue(CAMINHO_OWL.exists())

    def test_nao_recomenda_filme_ja_visto(self):
        ana = [r.titulo for r in recomendar(self.onto, "ana", k=50)]
        self.assertNotIn("Matrix", ana)
        self.assertNotIn("Interestelar", ana)

    def test_respeita_idade_minima(self):
        bruno = [r.titulo for r in recomendar(self.onto, "bruno", k=50)]
        self.assertNotIn("Se Beber, Não Case!", bruno)   # classificação 16, Bruno tem 12
        self.assertIn("Forrest Gump", bruno)              # classificação 12, permitida

    def test_ana_recebe_os_filmes_de_terror_em_primeiro(self):
        top = recomendar(self.onto, "ana", k=2)
        self.assertEqual({r.titulo for r in top}, {"O Iluminado", "O Silêncio dos Inocentes"})
        self.assertTrue(all(r.pontos == 4 for r in top))

    def test_diretor_favorito_pesa_mais(self):
        diego = recomendar(self.onto, "diego", k=1)[0]
        self.assertEqual(diego.titulo, "Pulp Fiction")
        self.assertEqual(diego.pontos, 8)
        self.assertTrue(any("diretor favorito" in m for m in diego.motivos))

    def test_toda_recomendacao_tem_motivos(self):
        for uid in ["ana", "bruno", "carla", "diego"]:
            for r in recomendar(self.onto, uid, k=10):
                self.assertTrue(r.motivos)
                self.assertEqual(sum(int(m.split()[0]) for m in r.motivos), r.pontos)

    def test_usuario_inexistente(self):
        with self.assertRaises(KeyError):
            individuo(self.onto, "fulano")


if __name__ == "__main__":
    unittest.main()
