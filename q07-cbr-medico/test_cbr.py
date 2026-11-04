"""Testes da Q7. Rodar com:  python3 -m unittest -v"""

import shutil
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from cbr import (
    CAMINHO_PADRAO,
    DURACOES,
    FAIXAS_ETARIAS,
    SINTOMAS,
    Caso,
    Descricao,
    Recuperado,
    avaliar_loo,
    carregar_casos,
    recuperar,
    reter,
    reutilizar,
    revisar,
    similaridade,
    similaridade_ordinal,
    similaridade_sintomas,
    tratamento_para,
)


def _rec(id_, diag, score, trat="t"):
    desc = Descricao("Adulto", "ate_3_dias", frozenset({"febre"}))
    return Recuperado(Caso(id_, desc, diag, trat), score, {})


class TestBaseDeCasos(unittest.TestCase):
    def setUp(self):
        self.base = carregar_casos()

    def test_20_casos_5_doencas_4_por_doenca(self):
        self.assertEqual(len(self.base), 20)
        contagem = Counter(c.diagnostico for c in self.base)
        self.assertEqual(len(contagem), 5)
        self.assertTrue(all(n == 4 for n in contagem.values()))

    def test_ids_unicos(self):
        self.assertEqual(len({c.id for c in self.base}), len(self.base))

    def test_atributos_validos(self):
        for c in self.base:
            self.assertIn(c.descricao.faixa_etaria, FAIXAS_ETARIAS)
            self.assertIn(c.descricao.duracao, DURACOES)
            self.assertTrue(c.descricao.sintomas <= set(SINTOMAS), c.id)
            self.assertTrue(c.descricao.sintomas, c.id)
            self.assertTrue(c.tratamento.strip(), c.id)


class TestSimilaridade(unittest.TestCase):
    def test_jaccard(self):
        self.assertAlmostEqual(similaridade_sintomas(frozenset({"febre", "tosse"}),
                                                     frozenset({"febre", "coriza"})), 1 / 3)
        self.assertEqual(similaridade_sintomas(frozenset({"febre"}), frozenset({"febre"})), 1.0)
        self.assertEqual(similaridade_sintomas(frozenset({"febre"}), frozenset({"tosse"})), 0.0)

    def test_ordinal(self):
        self.assertEqual(similaridade_ordinal(FAIXAS_ETARIAS, "Jovem", "Jovem"), 1.0)
        self.assertEqual(similaridade_ordinal(FAIXAS_ETARIAS, "Jovem", "Adulto"), 0.5)
        self.assertEqual(similaridade_ordinal(FAIXAS_ETARIAS, "Jovem", "Idoso"), 0.0)

    def test_identidade_e_simetria(self):
        a = Descricao("Adulto", "4_a_7_dias", frozenset({"febre", "tosse"}))
        b = Descricao("Idoso", "ate_3_dias", frozenset({"febre", "coriza", "tosse"}))
        self.assertAlmostEqual(similaridade(a, a)[0], 1.0)
        self.assertAlmostEqual(similaridade(a, b)[0], similaridade(b, a)[0])

    def test_peso_global(self):
        a = Descricao("Adulto", "4_a_7_dias", frozenset({"febre", "tosse"}))
        b = Descricao("Jovem", "mais_7_dias", frozenset({"febre", "coriza"}))
        total, partes = similaridade(a, b)
        # sintomas 1/3 (peso 0,6); faixa Adulto-Jovem 0,5 (peso 0,2); duração 4_a_7-mais_7 0,5 (peso 0,2)
        self.assertAlmostEqual(partes["sintomas"], 1 / 3)
        self.assertAlmostEqual(total, 0.6 * (1 / 3) + 0.2 * 0.5 + 0.2 * 0.5)


class TestRetrieve(unittest.TestCase):
    def setUp(self):
        self.base = carregar_casos()

    def test_retorna_k_casos_em_ordem_decrescente(self):
        desc = self.base[0].descricao
        recuperados = recuperar(desc, self.base, k=5)
        self.assertEqual(len(recuperados), 5)
        scores = [r.score for r in recuperados]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_caso_identico_fica_em_primeiro_com_score_1(self):
        caso = self.base[9]  # C10
        primeiro = recuperar(caso.descricao, self.base, k=3)[0]
        self.assertEqual(primeiro.caso.id, caso.id)
        self.assertAlmostEqual(primeiro.score, 1.0)


class TestReuse(unittest.TestCase):
    def test_voto_ponderado_pela_similaridade_nao_pela_contagem(self):
        # Dois casos de A com 0,3 cada (total 0,6) contra um de B com 0,9: B vence.
        recuperados = [_rec("X1", "A", 0.3), _rec("X2", "A", 0.3), _rec("X3", "B", 0.9)]
        self.assertEqual(reutilizar(recuperados).diagnostico, "B")

    def test_tratamento_do_caso_mais_similar_com_o_diagnostico_vencedor(self):
        # B vence pelo peso total (0,8 + 0,7 > 0,4). O tratamento vem do B mais similar (0,8),
        # não do caso A, que tem o maior score isolado mas perde a votação.
        recuperados = [
            _rec("X1", "A", 0.4, trat="tratamento de A"),
            _rec("X2", "B", 0.8, trat="tratamento de B (1)"),
            _rec("X3", "B", 0.7, trat="tratamento de B (2)"),
        ]
        s = reutilizar(recuperados)
        self.assertEqual(s.diagnostico, "B")
        self.assertEqual(s.tratamento, "tratamento de B (1)")

    def test_confianca_entre_0_e_1(self):
        base = carregar_casos()
        s = reutilizar(recuperar(base[0].descricao, base))
        self.assertTrue(0.0 <= s.confianca <= 1.0)

    def test_consulta_de_pneumonia_e_de_dengue(self):
        base = carregar_casos()
        pneumonia = Descricao("Adulto", "4_a_7_dias",
                              frozenset({"febre", "tosse", "falta_de_ar", "dor_no_peito"}))
        dengue = Descricao("Adulto", "ate_3_dias",
                           frozenset({"febre", "dor_atras_dos_olhos", "manchas_na_pele", "dor_muscular"}))
        self.assertEqual(reutilizar(recuperar(pneumonia, base)).diagnostico, "Pneumonia")
        self.assertEqual(reutilizar(recuperar(dengue, base)).diagnostico, "Dengue")


class TestRevise(unittest.TestCase):
    def setUp(self):
        self.sugestao = reutilizar([_rec("X1", "Gripe", 0.9)])

    def test_aceitar_sugestao(self):
        self.assertEqual(revisar(self.sugestao), "Gripe")
        self.assertEqual(revisar(self.sugestao, "   "), "Gripe")

    def test_corrigir_diagnostico(self):
        self.assertEqual(revisar(self.sugestao, " Dengue "), "Dengue")


class TestRetain(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.caminho = Path(self.tmp.name) / "casos.csv"
        shutil.copy(CAMINHO_PADRAO, self.caminho)

    def tearDown(self):
        self.tmp.cleanup()

    def test_reter_grava_no_arquivo_e_na_base(self):
        base = carregar_casos(self.caminho)
        novo_desc = Descricao("Jovem", "ate_3_dias", frozenset({"febre", "azia"}))
        novo = reter(base, novo_desc, "Gastrite", "tratamento de teste", self.caminho)
        self.assertEqual(novo.id, "C21")
        self.assertEqual(len(base), 21)
        recarregada = carregar_casos(self.caminho)
        self.assertEqual(len(recarregada), 21)
        self.assertEqual(recarregada[-1].descricao, novo_desc)
        self.assertEqual(recarregada[-1].diagnostico, "Gastrite")

    def test_caso_retido_passa_a_ser_recuperado(self):
        base = carregar_casos(self.caminho)
        novo_desc = Descricao("Jovem", "ate_3_dias", frozenset({"febre", "azia", "nausea"}))
        novo = reter(base, novo_desc, "Gastrite", "tratamento de teste", self.caminho)
        primeiro = recuperar(novo_desc, base, k=1)[0]
        self.assertEqual(primeiro.caso.id, novo.id)
        self.assertAlmostEqual(primeiro.score, 1.0)

    def test_tratamento_para_diagnostico_existente(self):
        base = carregar_casos()
        self.assertIn("Dengue", {c.diagnostico for c in base})
        self.assertIsNotNone(tratamento_para(base, "Dengue"))
        self.assertIsNone(tratamento_para(base, "Doença inventada"))


class TestAvaliacao(unittest.TestCase):
    def test_resultados_de_referencia(self):
        base = carregar_casos()
        self.assertEqual(avaliar_loo(base, 1)[0], 16)
        self.assertEqual(avaliar_loo(base, 3)[0], 20)
        self.assertEqual(avaliar_loo(base, 5)[0], 19)


if __name__ == "__main__":
    unittest.main()
