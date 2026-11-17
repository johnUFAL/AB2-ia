import json
import os
import unittest
from unittest.mock import patch

import agente_llm


class TestFerramentasPlanejador(unittest.TestCase):
    def test_agenda_e_plano_usam_o_planejador_da_q11(self):
        agenda = agente_llm.f_consultar_agenda()
        resultado = agente_llm.f_planejar()

        self.assertEqual(agenda["horario_disponivel"], ["14:00", "18:00"])
        self.assertEqual(
            [(bloco["id"], bloco["inicio"], bloco["fim"]) for bloco in resultado["plano"]],
            [("A", "14:00", "15:30"), ("C", "16:00", "17:00"), ("D", "17:00", "18:00")],
        )
        self.assertEqual(resultado["utilidade"], 11.0)

    def test_verificador_rejeita_plano_incompleto(self):
        verificacao = agente_llm.f_verificar_plano(
            [{"atividade": "A", "inicio": "14:00", "fim": "15:00"}]
        )

        self.assertFalse(verificacao["valido"])
        self.assertTrue(any("prazo hoje" in erro for erro in verificacao["violacoes"]))

    def test_divisao_de_trabalho_so_e_permitida_na_variante_solicitada(self):
        sem_divisao = agente_llm.f_planejar()
        com_divisao = agente_llm.f_planejar(permitir_divisao=True)
        blocos_b = [bloco for bloco in com_divisao["plano"] if bloco["id"] == "B"]

        self.assertFalse(any(bloco["id"] == "B" for bloco in sem_divisao["plano"]))
        self.assertGreater(len(blocos_b), 1)
        self.assertTrue(
            agente_llm.f_verificar_plano(com_divisao["plano"], permitir_divisao=True)["valido"]
        )

    def test_utilidade_so_e_calculada_para_plano_valido(self):
        plano = agente_llm.f_planejar()["plano"]

        self.assertEqual(agente_llm.f_calcular_utilidade(plano), {"utilidade": 11.0})
        with self.assertRaises(ValueError):
            agente_llm.f_calcular_utilidade(
                [{"atividade": "A", "inicio": "14:00", "fim": "15:00"}]
            )


class TestCicloDoAgente(unittest.TestCase):
    def test_plano_invalido_volta_ao_llm_antes_de_ser_aceito(self):
        respostas = iter(
            [
                json.dumps(
                    {
                        "pensamento": "O plano inicial está incompleto.",
                        "resposta_final": "Plano inicial.",
                        "plano": [{"atividade": "A", "inicio": "14:00", "fim": "15:00"}],
                    }
                ),
                json.dumps(
                    {
                        "pensamento": "Corrijo a duração da aula.",
                        "resposta_final": "Plano corrigido.",
                        "plano": [
                            {"atividade": "A", "inicio": "14:00", "fim": "15:30"},
                            {"atividade": "C", "inicio": "16:00", "fim": "17:00"},
                            {"atividade": "D", "inicio": "17:00", "fim": "18:00"},
                        ],
                    }
                ),
            ]
        )
        mensagens_recebidas = []

        def llm(_sistema, mensagens):
            mensagens_recebidas.append(list(mensagens))
            return next(respostas)

        resultado = agente_llm.executar_agente("Organize minha agenda.", llm=llm)

        self.assertEqual(resultado["resposta"], "Plano corrigido.")
        self.assertEqual(len(resultado["registro"]), 2)
        self.assertIn("violações", mensagens_recebidas[1][-1]["content"])

    def test_json_invalido_recebe_observacao_de_formato(self):
        respostas = iter(
            [
                "Não consigo.",
                json.dumps(
                    {
                        "resposta_final": "Agenda válida.",
                        "plano": [
                            {"atividade": "A", "inicio": "14:00", "fim": "15:30"},
                            {"atividade": "C", "inicio": "16:00", "fim": "17:00"},
                            {"atividade": "D", "inicio": "17:00", "fim": "18:00"},
                        ],
                    }
                ),
            ]
        )

        resultado = agente_llm.executar_agente(
            "Organize minha agenda.", llm=lambda _s, _m: next(respostas)
        )

        self.assertEqual(resultado["resposta"], "Agenda válida.")
        self.assertEqual(resultado["registro"][0]["acao"], "resposta fora do formato")

    def test_sem_chave_a_chamada_externa_falha_explicitamente(self):
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": ""}):
            with self.assertRaisesRegex(RuntimeError, "ANTHROPIC_API_KEY"):
                agente_llm.chamar_llm(agente_llm.SISTEMA, [])

    def test_pedido_vazio_e_rejeitado(self):
        with self.assertRaises(ValueError):
            agente_llm.executar_agente(" ")


if __name__ == "__main__":
    unittest.main()
