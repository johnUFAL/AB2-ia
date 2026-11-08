"""Testes da Q2. Rodar com:  python3 -m unittest -v"""

import unittest
from collections import Counter

from knn import (
    ATRIBUTOS,
    CONSULTA_EXEMPLO,
    Instancia,
    carregar_base,
    classificar,
    distancia_hamming,
    leave_one_out,
    vizinhos_mais_proximos,
)


class TestBase(unittest.TestCase):
    def setUp(self):
        self.base = carregar_base()

    def test_30_instancias_com_nomes_E1_a_E30(self):
        self.assertEqual(len(self.base), 30)
        self.assertEqual([i.nome for i in self.base], [f"E{n}" for n in range(1, 31)])

    def test_distribuicao_das_classes(self):
        contagem = Counter(i.classe for i in self.base)
        self.assertEqual(contagem, Counter({"Alto": 9, "Moderado": 11, "Baixo": 10}))

    def test_sem_vetores_repetidos_nem_contraditorios(self):
        por_vetor = {}
        for i in self.base:
            por_vetor.setdefault(i.valores, set()).add(i.classe)
        self.assertTrue(all(len(classes) == 1 for classes in por_vetor.values()))
        self.assertEqual(len(por_vetor), 30)

    def test_valores_de_E1_e_E7(self):
        e1, e7 = self.base[0], self.base[6]
        self.assertEqual(e1.valores, ("Ruim", "Alta", "Nenhuma", "0-15k", "Estavel", "Adulto"))
        self.assertEqual(e7.valores, ("Ruim", "Baixa", "Nenhuma", "0-15k", "Estavel", "Senior"))


class TestDistanciaHamming(unittest.TestCase):
    def test_E1_e_E7_diferem_em_dois_atributos(self):
        base = carregar_base()
        self.assertEqual(distancia_hamming(base[0].valores, base[6].valores), 2)

    def test_identidade_simetria_e_limite(self):
        a = ("Boa", "Baixa", "Nenhuma", ">35k", "Estavel", "Adulto")
        b = ("Ruim", "Alta", "Adequada", "0-15k", "Instavel", "Senior")
        self.assertEqual(distancia_hamming(a, a), 0)
        self.assertEqual(distancia_hamming(a, b), distancia_hamming(b, a))
        self.assertEqual(distancia_hamming(a, b), 6)

    def test_vizinhos_ordenados_por_distancia(self):
        base = carregar_base()
        vz = vizinhos_mais_proximos(base[0].valores, base)
        distancias = [v.distancia for v in vz]
        self.assertEqual(distancias, sorted(distancias))
        self.assertEqual(vz[0].instancia.nome, "E1")  # o próprio exemplo, distância 0


class TestClassificacao(unittest.TestCase):
    def setUp(self):
        self.base = carregar_base()

    def test_k1_com_exemplo_da_base_devolve_a_propria_classe(self):
        e5 = self.base[4]
        self.assertEqual(classificar(e5.valores, self.base, k=1).classe, e5.classe)

    def test_consulta_de_exemplo_k5(self):
        q = tuple(CONSULTA_EXEMPLO[a] for a in ATRIBUTOS)
        r = classificar(q, self.base, k=5)
        self.assertEqual(r.classe, "Moderado")
        self.assertEqual(r.votos, Counter({"Moderado": 4, "Baixo": 1}))
        self.assertEqual(len(r.vizinhos), 5)

    def test_previsao_nao_depende_do_desempate_na_fronteira(self):
        # Na consulta de exemplo, o k=5 corta um empate de distância 2 (E3, E9, E17, E22, E25).
        # Qualquer escolha entre eles mantém a classe Moderado.
        from itertools import combinations
        q = tuple(CONSULTA_EXEMPLO[a] for a in ATRIBUTOS)
        vz = vizinhos_mais_proximos(q, self.base)
        fixos = [v.instancia for v in vz if v.distancia < 2]
        empates = [v.instancia for v in vz if v.distancia == 2]
        for escolha in combinations(empates, 5 - len(fixos)):
            votos = Counter(i.classe for i in fixos + list(escolha)).most_common()
            self.assertEqual(votos[0][0], "Moderado")
            self.assertNotEqual(votos[0][1], votos[1][1])

    def test_empate_de_votos_vai_para_o_vizinho_mais_proximo(self):
        base = [
            Instancia("X1", ("a", "a", "a", "a", "a", "a"), "Sim"),
            Instancia("X2", ("a", "a", "a", "a", "a", "b"), "Nao"),
        ]
        # k=2: um voto para cada classe. X1 é mais próximo da consulta, então vence.
        r = classificar(("a", "a", "a", "a", "a", "a"), base, k=2)
        self.assertEqual(r.classe, "Sim")

    def test_k_fora_do_intervalo_levanta_erro(self):
        with self.assertRaises(ValueError):
            classificar(self.base[0].valores, self.base, k=0)
        with self.assertRaises(ValueError):
            classificar(self.base[0].valores, self.base, k=31)


class TestLeaveOneOut(unittest.TestCase):
    def setUp(self):
        self.base = carregar_base()

    def test_resultados_de_referencia(self):
        self.assertEqual(leave_one_out(self.base, 1)[0], 14)
        self.assertEqual(leave_one_out(self.base, 3)[0], 17)
        self.assertEqual(leave_one_out(self.base, 5)[0], 18)
        self.assertEqual(leave_one_out(self.base, 9)[0], 20)

    def test_detalhes_cobrem_todas_as_instancias(self):
        _, detalhes = leave_one_out(self.base, 5)
        self.assertEqual(len(detalhes), 30)
        self.assertEqual([d[0] for d in detalhes], [i.nome for i in self.base])


if __name__ == "__main__":
    unittest.main()
