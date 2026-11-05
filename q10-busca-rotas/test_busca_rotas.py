"""Testes da Q10. Rodar com:  python3 -m unittest -v"""

import unittest

from busca_rotas import (
    DESTINO,
    HEURISTICA,
    INICIO,
    OBRIGATORIOS,
    VIZINHOS,
    busca_a_estrela,
    busca_custo_uniforme,
    busca_em_largura,
    busca_em_profundidade,
    custo_do_caminho,
    heuristica_do_no,
    problema_com_obrigatorios,
    problema_original,
    verificar_heuristica,
)


class TestProblemaOriginal(unittest.TestCase):
    def setUp(self):
        self.p = problema_original()

    def test_bfs_rota_e_custo(self):
        r = busca_em_largura(self.p)
        self.assertEqual(r.rota, ["A", "B", "C", "F", "I"])
        self.assertEqual(r.custo, 15)
        # BFS minimiza o número de trechos (4), não o tempo.
        self.assertEqual(len(r.rota) - 1, 4)

    def test_bfs_ordem_de_expansao(self):
        r = busca_em_largura(self.p)
        self.assertEqual([e.rotulo for e in r.expansoes], list("ABDCEGFH"))

    def test_dfs_rota_e_custo(self):
        r = busca_em_profundidade(self.p)
        self.assertEqual(r.rota, ["A", "B", "C", "F", "E", "D", "G", "H", "I"])
        self.assertEqual(r.custo, 29)

    def test_dfs_ordem_de_expansao(self):
        r = busca_em_profundidade(self.p)
        self.assertEqual([e.rotulo for e in r.expansoes], list("ABCFEDGH"))

    def test_ucs_rota_e_custo(self):
        r = busca_custo_uniforme(self.p)
        self.assertEqual(r.rota, ["A", "B", "E", "F", "I"])
        self.assertEqual(r.custo, 13)

    def test_ucs_expande_nos_com_g_crescente(self):
        r = busca_custo_uniforme(self.p)
        gs = [e.g for e in r.expansoes]
        self.assertEqual(gs, sorted(gs))
        self.assertEqual(
            [(e.rotulo, e.g) for e in r.expansoes],
            [("A", 0), ("D", 3), ("B", 4), ("E", 6), ("G", 9), ("C", 9), ("F", 9), ("H", 11)],
        )

    def test_astar_rota_e_custo(self):
        r = busca_a_estrela(self.p, heuristica_do_no(self.p))
        self.assertEqual(r.rota, ["A", "B", "E", "F", "I"])
        self.assertEqual(r.custo, 13)

    def test_astar_valores_de_g_h_f(self):
        r = busca_a_estrela(self.p, heuristica_do_no(self.p))
        tabela = [(e.rotulo, e.g, e.h, e.f) for e in r.expansoes]
        self.assertEqual(
            tabela,
            [
                ("A", 0, 10, 10),
                ("D", 3, 9, 12),
                ("B", 4, 8, 12),
                ("E", 6, 6, 12),
                ("F", 9, 4, 13),
                ("H", 11, 2, 13),
            ],
        )

    def test_astar_expande_menos_nos_que_ucs(self):
        ucs = busca_custo_uniforme(self.p)
        astar = busca_a_estrela(self.p, heuristica_do_no(self.p))
        self.assertLess(len(astar.expansoes), len(ucs.expansoes))
        self.assertEqual(astar.custo, ucs.custo)

    def test_custo_do_caminho_confere_com_o_grafo(self):
        for alg in (busca_em_largura, busca_em_profundidade, busca_custo_uniforme):
            r = alg(self.p)
            self.assertEqual(custo_do_caminho(r.rota), r.custo)


class TestHeuristica(unittest.TestCase):
    def test_admissivel_e_consistente(self):
        _, admissivel, consistente = verificar_heuristica()
        self.assertTrue(admissivel)
        self.assertTrue(consistente)

    def test_custos_reais_ate_I(self):
        reais, _, _ = verificar_heuristica()
        self.assertEqual(
            reais,
            {"A": 13, "B": 9, "C": 6, "D": 11, "E": 7, "F": 4, "G": 5, "H": 2, "I": 0},
        )

    def test_grafo_tem_12_trechos(self):
        arestas = {frozenset((u, v)) for u in VIZINHOS for v in VIZINHOS[u]}
        self.assertEqual(len(arestas), 12)
        self.assertEqual(set(VIZINHOS), set(HEURISTICA))


def melhor_rota_por_forca_bruta(limite: int) -> int | None:
    """Enumera todos os passeios de A com custo <= limite e devolve o menor custo que
    termina em I visitando D e F. Serve como referência independente da busca."""
    melhor = None
    pilha = [(INICIO, 0, frozenset({INICIO}) & OBRIGATORIOS)]
    while pilha:
        no, custo, visitados = pilha.pop()
        if no == DESTINO and OBRIGATORIOS <= visitados and (melhor is None or custo < melhor):
            melhor = custo
        for v, c in VIZINHOS[no].items():
            if custo + c <= limite:
                pilha.append((v, custo + c, visitados | ({v} & OBRIGATORIOS)))
    return melhor


class TestVersaoModificada(unittest.TestCase):
    def setUp(self):
        self.p = problema_com_obrigatorios()

    def test_ucs_rota_e_custo(self):
        r = busca_custo_uniforme(self.p)
        self.assertEqual(r.rota, ["A", "D", "E", "F", "I"])
        self.assertEqual(r.custo, 14)

    def test_rota_passa_por_D_e_F_antes_de_I(self):
        r = busca_custo_uniforme(self.p)
        self.assertTrue(OBRIGATORIOS <= set(r.rota[:-1]))
        self.assertEqual(r.rota[-1], DESTINO)

    def test_astar_chega_ao_mesmo_custo(self):
        r = busca_a_estrela(self.p, heuristica_do_no(self.p))
        self.assertEqual(r.custo, 14)

    def test_bate_com_forca_bruta(self):
        # Nenhum passeio de custo < 14 satisfaz a restrição; existe um de custo 14.
        self.assertIsNone(melhor_rota_por_forca_bruta(13))
        self.assertEqual(melhor_rota_por_forca_bruta(14), 14)
        self.assertEqual(busca_custo_uniforme(self.p).custo, 14)

    def test_original_e_modificada_diferem_so_pela_restricao(self):
        original = busca_custo_uniforme(problema_original())
        modificada = busca_custo_uniforme(self.p)
        self.assertEqual(original.custo, 13)
        self.assertEqual(modificada.custo - original.custo, 1)


if __name__ == "__main__":
    unittest.main()
