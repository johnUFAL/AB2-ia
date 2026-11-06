"""Testes da Q8. Rodar com:  python3 -m unittest -v"""

import shutil
import tempfile
import unittest
import warnings
from pathlib import Path

from bn_diagnostico import (
    ARESTAS,
    CAMINHO_BIF,
    DOENCAS,
    FAIXAS,
    P_DURACAO_DADA_DOENCA,
    P_DOENCA_DADA_FAIXA,
    P_FAIXA,
    P_SINTOMA_DADA_DOENCA,
    SINTOMAS,
    carregar_bif,
    construir_modelo,
    diagnostico,
    diagnostico_direto,
    salvar_bif,
)

warnings.filterwarnings("ignore")


class TestEstrutura(unittest.TestCase):
    def setUp(self):
        self.modelo = construir_modelo()

    def test_17_variaveis_e_16_arestas(self):
        self.assertEqual(len(self.modelo.nodes()), 17)
        self.assertEqual(len(self.modelo.edges()), 16)

    def test_doenca_principal_e_14_sintomas_observaveis(self):
        self.assertIn("Doenca", self.modelo.nodes())
        self.assertEqual(len(SINTOMAS), 14)
        self.assertGreaterEqual(len(SINTOMAS), 3)

    def test_sintomas_dependem_so_da_doenca(self):
        for s in SINTOMAS:
            self.assertEqual(set(self.modelo.get_parents(s)), {"Doenca"})

    def test_modelo_consistente(self):
        self.assertTrue(self.modelo.check_model())

    def test_arestas_declaradas_existem_no_modelo(self):
        self.assertEqual(set(self.modelo.edges()), set(ARESTAS))


class TestTabelas(unittest.TestCase):
    def test_distribuicoes_somam_1(self):
        for faixa in FAIXAS:
            self.assertAlmostEqual(sum(P_DOENCA_DADA_FAIXA[faixa]), 1.0)
        self.assertAlmostEqual(sum(P_FAIXA.values()), 1.0)
        for i in range(len(DOENCAS)):
            self.assertAlmostEqual(sum(P_DURACAO_DADA_DOENCA[d][i] for d in P_DURACAO_DADA_DOENCA), 1.0)

    def test_probabilidades_entre_0_e_1(self):
        todas = [p for linha in P_SINTOMA_DADA_DOENCA.values() for p in linha]
        todas += [p for linha in P_DOENCA_DADA_FAIXA.values() for p in linha]
        self.assertTrue(all(0.0 <= p <= 1.0 for p in todas))

    def test_priori_da_doenca_bate_com_a_conta_manual(self):
        priori = diagnostico(construir_modelo(), {})
        esperado = {"Gripe": 0.2525, "Dengue": 0.175, "Pneumonia": 0.135,
                    "Enxaqueca": 0.2125, "Gastrite": 0.225}
        for d in DOENCAS:
            self.assertAlmostEqual(priori[d], esperado[d], places=6)


class TestInferencia(unittest.TestCase):
    def setUp(self):
        self.modelo = construir_modelo()

    def assertMesmaInferencia(self, ev):
        a = diagnostico(self.modelo, ev)
        b = diagnostico_direto(ev)
        for d in DOENCAS:
            self.assertAlmostEqual(a[d], b[d], places=9, msg=f"{ev} -> {d}")

    def test_pgmpy_bate_com_a_formula_direta(self):
        casos = [
            {},
            {"Febre": "Sim"},
            {"Febre": "Sim", "Tosse": "Sim", "DorMuscular": "Sim"},
            {"Febre": "Sim", "Tosse": "Nao", "FaltaDeAr": "Sim", "DorNoPeito": "Sim"},
            {"DorAtrasDosOlhos": "Sim", "ManchasNaPele": "Sim"},
            {"Faixa": "Idoso", "Febre": "Sim", "Tosse": "Sim"},
            {"Duracao": "mais_7_dias", "DorNoPeito": "Sim"},
            {"Faixa": "Jovem", "Duracao": "ate_3_dias", "Nausea": "Sim", "Azia": "Sim"},
        ]
        for ev in casos:
            self.assertMesmaInferencia(ev)

    def test_exemplo_do_enunciado_gripe_perto_de_67_por_cento(self):
        dist = diagnostico(self.modelo, {"Febre": "Sim", "Tosse": "Sim", "DorMuscular": "Sim"})
        self.assertAlmostEqual(dist["Gripe"], 0.669, places=3)
        self.assertAlmostEqual(dist["Pneumonia"], 0.230, places=3)
        self.assertAlmostEqual(dist["Dengue"], 0.099, places=3)

    def test_distribuicao_soma_1_com_evidencia_parcial(self):
        dist = diagnostico(self.modelo, {"Azia": "Sim"})
        self.assertAlmostEqual(sum(dist.values()), 1.0)

    def test_falta_de_ar_aumenta_pneumonia(self):
        base = {"Febre": "Sim", "Tosse": "Sim"}
        sem = diagnostico(self.modelo, base)["Pneumonia"]
        com = diagnostico(self.modelo, {**base, "FaltaDeAr": "Sim"})["Pneumonia"]
        self.assertGreater(com, sem)

    def test_idoso_aumenta_pneumonia_em_relacao_a_jovem(self):
        ev = {"Febre": "Sim", "Tosse": "Sim", "DorMuscular": "Sim"}
        jovem = diagnostico(self.modelo, {**ev, "Faixa": "Jovem"})["Pneumonia"]
        idoso = diagnostico(self.modelo, {**ev, "Faixa": "Idoso"})["Pneumonia"]
        self.assertGreater(idoso, jovem)

    def test_sintoma_ausente_reduz_a_doenca_tipica(self):
        sem_febre = diagnostico(self.modelo, {"Febre": "Nao"})["Dengue"]
        com_febre = diagnostico(self.modelo, {"Febre": "Sim"})["Dengue"]
        self.assertGreater(com_febre, sem_febre)


class TestArquivoBIF(unittest.TestCase):
    def test_salvar_e_carregar_mantem_a_inferencia(self):
        with tempfile.TemporaryDirectory() as tmp:
            caminho = Path(tmp) / "rede.bif"
            salvar_bif(construir_modelo(), caminho)
            recarregado = carregar_bif(caminho)
            ev = {"Febre": "Sim", "Tosse": "Sim", "DorMuscular": "Sim"}
            a = diagnostico(recarregado, ev)
            b = diagnostico_direto(ev)
            for d in DOENCAS:
                self.assertAlmostEqual(a[d], b[d], places=6)

    def test_arquivo_do_projeto_existe(self):
        self.assertTrue(CAMINHO_BIF.exists())


if __name__ == "__main__":
    unittest.main()
