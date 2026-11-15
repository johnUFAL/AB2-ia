import unittest

from demo_hibrido import INTERPRETACAO_ESPERADA, PLANOS_INGENUOS
from planejador import (ATIVIDADES, Atividade, ferramenta_planejar, minutos, planejar, verificar)


class TestCasoBase(unittest.TestCase):
    def setUp(self):
        self.r = planejar()

    def test_plano_otimo(self):
        self.assertEqual(self.r.blocos, [("A", 840, 930), ("C", 960, 1020), ("D", 1020, 1080)])
        self.assertEqual(self.r.utilidade, 11)

    def test_so_quatro_planos_viaveis(self):
        self.assertEqual(self.r.viaveis, 4)

    def test_b_nao_realizada_com_justificativa(self):
        self.assertEqual(list(self.r.nao_realizadas), ["B"])
        self.assertIn("120 min contínuos", self.r.nao_realizadas["B"])
        self.assertIn("amanhã", self.r.nao_realizadas["B"])

    def test_resultado_passa_no_verificador(self):
        self.assertEqual(verificar(self.r.blocos), [])

    def test_resultado_independe_dos_pesos(self):
        for p in ({"Alta": 5, "Media": 3, "Baixa": 1}, {"Alta": 5, "Media": 1, "Baixa": 3}):
            self.assertEqual(planejar(peso=p).blocos, self.r.blocos)


class TestVarianteDivisivel(unittest.TestCase):
    def setUp(self):
        self.ativ = [Atividade(a.id, a.nome, a.duracao, a.prioridade, a.prazo, a.inicio_fixo,
                               divisivel=(a.id == "B")) for a in ATIVIDADES]

    def test_dividir_b_aumenta_a_utilidade(self):
        r = planejar(self.ativ)
        self.assertEqual(r.utilidade, 12.25)
        self.assertEqual(sum(f - i for x, i, f in r.blocos if x == "B"), 90)
        self.assertEqual(verificar(r.blocos, self.ativ), [])

    def test_pesos_podem_mudar_a_decisao(self):
        r = planejar(self.ativ, peso={"Alta": 5, "Media": 1, "Baixa": 3})
        self.assertIn("D", {x for x, _, _ in r.blocos})


class TestRestricoes(unittest.TestCase):
    def test_sem_plano_viavel_levanta_erro(self):
        impossivel = [Atividade("X", "x", 240, "Alta", "hoje"), Atividade("Y", "y", 60, "Alta", "hoje")]
        with self.assertRaises(ValueError):
            planejar(impossivel)

    def test_duracao_fora_da_grade(self):
        with self.assertRaises(ValueError):
            planejar([Atividade("X", "x", 45, "Alta", "hoje")])


class TestVerificador(unittest.TestCase):
    def _erros(self, plano):
        return verificar([(i, minutos(a), minutos(b)) for i, a, b in plano])

    def test_planos_ingenuos_sao_todos_rejeitados(self):
        for plano in PLANOS_INGENUOS.values():
            self.assertTrue(self._erros(plano))

    def test_plano_1_fora_da_janela(self):
        erros = self._erros(list(PLANOS_INGENUOS.values())[0])
        self.assertTrue(any("fora da janela" in e for e in erros))

    def test_plano_2_sobreposicao_e_duracao(self):
        erros = self._erros(list(PLANOS_INGENUOS.values())[1])
        self.assertTrue(any("sobreposição" in e for e in erros))
        self.assertTrue(any("A: prazo hoje" in e for e in erros))

    def test_plano_3_atividade_indivisivel(self):
        erros = self._erros(list(PLANOS_INGENUOS.values())[2])
        self.assertTrue(any("indivisível" in e for e in erros))

    def test_compromisso_fixo(self):
        erros = self._erros([("A", "14:00", "15:30"), ("C", "16:30", "17:30")])
        self.assertTrue(any("compromisso fixo" in e for e in erros))


class TestFerramenta(unittest.TestCase):
    def test_json_de_entrada_gera_o_mesmo_plano(self):
        r = ferramenta_planejar(INTERPRETACAO_ESPERADA)
        self.assertEqual([(b["id"], b["inicio"], b["fim"]) for b in r["plano"]],
                         [("A", "14:00", "15:30"), ("C", "16:00", "17:00"), ("D", "17:00", "18:00")])
        self.assertEqual(r["violacoes"], [])
        self.assertEqual(r["utilidade"], 11.0)


if __name__ == "__main__":
    unittest.main()
