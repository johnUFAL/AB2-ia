"""Testes da Q12. Executar na raiz do repositório:
    python -m unittest discover -s q12-agente-llm -p "test_*.py" -v

Os testes de planejador dependem de q11-agentes-classico-vs-llm/planejador.py.
"""

import io
import json
import os
import unittest
from unittest.mock import patch

import agente_llm


class TestProvedorOllama(unittest.TestCase):
    def test_nao_exige_chave_de_api(self):
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": ""}, clear=False):
            self.assertIs(agente_llm.escolher_llm(), agente_llm.chamar_ollama)

    def test_padrao_e_ollama_e_provedor_desconhecido_falha(self):
        with patch.dict(os.environ, {"LLM_PROVIDER": ""}, clear=False):
            self.assertIs(agente_llm.escolher_llm(), agente_llm.chamar_ollama)
        with patch.dict(os.environ, {"LLM_PROVIDER": "xpto"}, clear=False):
            with self.assertRaisesRegex(RuntimeError, "Provedor desconhecido"):
                agente_llm.escolher_llm()

    def test_envia_pedido_no_formato_do_ollama_e_le_resposta(self):
        capturado = {}

        class RespostaFalsa(io.BytesIO):
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

        def fake_urlopen(pedido, timeout=None):
            capturado["url"] = pedido.full_url
            capturado["corpo"] = json.loads(pedido.data.decode("utf-8"))
            dados = {"message": {"role": "assistant", "content": '{"resposta_final": "ok"}'}}
            return RespostaFalsa(json.dumps(dados).encode("utf-8"))

        with patch.dict(os.environ, {"OLLAMA_MODEL": "meu-modelo", "OLLAMA_HOST": "http://x:1"}):
            with patch("agente_llm.urllib.request.urlopen", side_effect=fake_urlopen):
                texto = agente_llm.chamar_ollama("SISTEMA", [{"role": "user", "content": "oi"}])

        self.assertEqual(texto, '{"resposta_final": "ok"}')
        self.assertEqual(capturado["url"], "http://x:1/api/chat")
        self.assertEqual(capturado["corpo"]["model"], "meu-modelo")
        self.assertEqual(capturado["corpo"]["format"], "json")
        self.assertFalse(capturado["corpo"]["stream"])
        self.assertEqual(capturado["corpo"]["messages"][0], {"role": "system", "content": "SISTEMA"})

    def test_servidor_fora_do_ar_gera_erro_explicativo(self):
        import urllib.error

        with patch(
            "agente_llm.urllib.request.urlopen",
            side_effect=urllib.error.URLError("connection refused"),
        ):
            with self.assertRaisesRegex(RuntimeError, "Não foi possível conectar ao Ollama"):
                agente_llm.chamar_ollama("SISTEMA", [{"role": "user", "content": "oi"}])


class TestVerificacaoDoOllama(unittest.TestCase):
    def _resposta(self, dados):
        class R(io.BytesIO):
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

        return R(json.dumps(dados).encode("utf-8"))

    def test_servidor_fora_do_ar_falha_rapido_com_mensagem(self):
        import urllib.error

        with patch("agente_llm.urllib.request.urlopen", side_effect=urllib.error.URLError("refused")):
            with self.assertRaisesRegex(RuntimeError, "Ollama não responde"):
                agente_llm.verificar_ollama()

    def test_modelo_ausente_indica_o_pull(self):
        with patch.dict(os.environ, {"OLLAMA_MODEL": "modelo-x"}):
            with patch("agente_llm.urllib.request.urlopen",
                       return_value=self._resposta({"models": [{"name": "outro:latest"}]})):
                with self.assertRaisesRegex(RuntimeError, "ollama pull modelo-x"):
                    agente_llm.verificar_ollama()

    def test_modelo_instalado_passa(self):
        with patch.dict(os.environ, {"OLLAMA_MODEL": "llama3.2"}):
            with patch("agente_llm.urllib.request.urlopen",
                       return_value=self._resposta({"models": [{"name": "llama3.2:latest"}]})):
                agente_llm.verificar_ollama()  # não deve levantar erro


class TestProvedorAnthropic(unittest.TestCase):
    def test_sem_chave_falha_explicitamente(self):
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": ""}):
            with self.assertRaisesRegex(RuntimeError, "ANTHROPIC_API_KEY"):
                agente_llm.chamar_anthropic(agente_llm.SISTEMA, [])


class TestCicloComLLMInjetado(unittest.TestCase):
    """Não chamam API nem Ollama: o LLM é uma função falsa."""

    def test_ferramenta_inexistente_recebe_lista_de_ferramentas_validas(self):
        mensagens = []

        def llm(_s, m):
            mensagens.append(list(m))
            if len(mensagens) == 1:
                return json.dumps({"pensamento": "x", "acao": "reorganizar", "argumentos": {}})
            return "Não consigo."

        agente_llm.executar_agente("Organize.", llm=llm, max_passos=2)
        erro = json.loads(mensagens[1][-1]["content"])["erro"]
        self.assertIn("consultar_agenda", erro)
        self.assertIn("planejar", erro)

    def test_pedido_vazio_e_rejeitado(self):
        with self.assertRaises(ValueError):
            agente_llm.executar_agente(" ", llm=lambda _s, _m: "")

    def test_json_invalido_recebe_observacao_de_formato(self):
        resultado = agente_llm.executar_agente(
            "Organize minha agenda.", llm=lambda _s, _m: "Não consigo.", max_passos=1
        )
        self.assertEqual(resultado["registro"][0]["acao"], "resposta fora do formato")
        self.assertIsNone(resultado["plano"])

    def test_limite_de_passos_retorna_mensagem_sem_plano(self):
        resultado = agente_llm.executar_agente(
            "Organize.",
            llm=lambda _s, _m: json.dumps({"pensamento": "x", "acao": "inexistente"}),
            max_passos=2,
        )
        self.assertIsNone(resultado["plano"])
        self.assertEqual(len(resultado["registro"]), 2)


class TestRegrasDoAgente(unittest.TestCase):
    """Não dependem da Q11 (usam LLM falso e ferramentas substituídas)."""

    def test_divisao_sem_autorizacao_e_recusada(self):
        mensagens = []
        respostas = iter(
            [
                json.dumps({"pensamento": "x", "acao": "planejar",
                            "argumentos": {"permitir_divisao": True}}),
                "Não consigo.",
            ]
        )

        def llm(_s, m):
            mensagens.append(list(m))
            return next(respostas)

        agente_llm.executar_agente("Organize.", llm=llm, max_passos=2, aceita_divisao=False)
        self.assertIn("não foi autorizada", mensagens[1][-1]["content"])

    def test_plano_em_formato_de_objeto_e_aceito(self):
        bloco = agente_llm._ler_plano(
            {"plano": [{"atividade": "A", "inicio": "14:00", "fim": "15:00"}]}
        )
        self.assertEqual(bloco, [("A", 840, 900)])

    def test_plano_valido_pede_resposta_final(self):
        mensagens = []
        respostas = iter(
            [
                json.dumps({"pensamento": "x", "acao": "verificar_plano",
                            "argumentos": {"plano": [{"atividade": "A", "inicio": "14:00",
                                                      "fim": "15:30"}]}}),
                "Não consigo.",
            ]
        )

        def llm(_s, m):
            mensagens.append(list(m))
            return next(respostas)

        with patch.dict(agente_llm.FERRAMENTAS,
                        {"verificar_plano": lambda plano, permitir_divisao=False:
                         {"valido": True, "violacoes": []}}):
            agente_llm.executar_agente("Organize.", llm=llm, max_passos=2)
        self.assertIn("proximo_passo", mensagens[1][-1]["content"])

    def test_resposta_final_com_plano_malformado_usa_plano_do_planejador(self):
        def planejar_falso(permitir_divisao=False):
            return {
                "plano": [{"atividade": "Preparar aula de IA", "id": "A",
                           "inicio": "14:00", "fim": "15:30"}],
                "utilidade": 11.0,
                "pendencias": {},
            }

        def verificar_falso(plano, permitir_divisao=False):
            if not isinstance(plano, list):
                raise ValueError("plano deve ser uma lista")
            return {"valido": True, "violacoes": []}

        respostas = iter([
            json.dumps({"pensamento": "x", "acao": "planejar", "argumentos": {}}),
            json.dumps({"pensamento": "y", "resposta_final": "Aula às 14h.",
                        "plano": "texto no lugar da lista"}),
        ])
        with patch.dict(agente_llm.FERRAMENTAS, {"planejar": planejar_falso}), \
                patch.object(agente_llm, "f_verificar_plano", side_effect=verificar_falso):
            resultado = agente_llm.executar_agente(
                "Organize.", llm=lambda _s, _m: next(respostas), max_passos=2
            )

        # Parada antecipada: o planejador já devolveu um plano verificado no primeiro passo.
        self.assertTrue(resultado["resposta"].startswith("Plano verificado pelo planejador"))
        self.assertEqual(resultado["origem_do_plano"], "planejador")
        self.assertEqual(resultado["plano"][0]["inicio"], "14:00")

    def test_resposta_copiada_do_prompt_nao_e_aceita(self):
        copia = agente_llm.SISTEMA.strip().splitlines()[-1]
        self.assertFalse(agente_llm._resposta_util(copia))
        self.assertFalse(agente_llm._resposta_util("curta"))
        self.assertTrue(agente_llm._resposta_util(
            "A aula às 14h, a reunião às 16h e a revisão às 17h. B fica para amanhã."))

    def test_para_logo_apos_plano_verificado_do_planejador(self):
        chamadas = []

        def planejar_falso(permitir_divisao=False):
            return {
                "plano": [{"atividade": "Preparar aula de IA", "id": "A",
                           "inicio": "14:00", "fim": "15:30"}],
                "utilidade": 11.0,
                "pendencias": {"B": "Não coube."},
            }

        def llm(_s, _m):
            chamadas.append(1)
            return json.dumps({"pensamento": "x", "acao": "planejar", "argumentos": {}})

        with patch.dict(agente_llm.FERRAMENTAS, {"planejar": planejar_falso}), \
                patch.object(agente_llm, "f_verificar_plano",
                             return_value={"valido": True, "violacoes": []}):
            resultado = agente_llm.executar_agente("Organize.", llm=llm, max_passos=20)

        self.assertEqual(len(chamadas), 1)  # parou na primeira chamada do planejador
        self.assertEqual(resultado["origem_do_plano"], "planejador")
        self.assertIn("14:00–15:30  Preparar aula de IA", resultado["resposta"])
        self.assertIn("Pendências: B: Não coube.", resultado["resposta"])

    def test_planejar_direto_nao_chama_o_modelo(self):
        def planejar_falso(permitir_divisao=False):
            return {
                "plano": [{"atividade": "Preparar aula de IA", "id": "A",
                           "inicio": "14:00", "fim": "15:30"}],
                "utilidade": 11.0,
                "pendencias": {},
            }

        with patch.object(agente_llm, "f_planejar", side_effect=planejar_falso), \
                patch.object(agente_llm, "f_verificar_plano",
                             return_value={"valido": True, "violacoes": []}):
            resultado = agente_llm.planejar_direto()

        self.assertEqual(resultado["origem_do_plano"], "planejador")
        self.assertIn("14:00–15:30  Preparar aula de IA", resultado["resposta"])

    def test_fallback_usa_plano_verificado_quando_o_modelo_nao_conclui(self):
        def planejar_falso(permitir_divisao=False):
            return {
                "plano": [{"atividade": "Preparar aula de IA", "id": "A",
                           "inicio": "14:00", "fim": "15:30"}],
                "utilidade": 11.0,
                "pendencias": {"B": "Não coube."},
            }

        with patch.dict(agente_llm.FERRAMENTAS, {"planejar": planejar_falso}), \
                patch.object(agente_llm, "f_verificar_plano",
                             return_value={"valido": True, "violacoes": []}):
            resultado = agente_llm.executar_agente(
                "Organize.",
                llm=lambda _s, _m: json.dumps({"pensamento": "x", "acao": "planejar",
                                               "argumentos": {}}),
                max_passos=2,
            )

        self.assertIsNotNone(resultado["plano"])
        self.assertIn("14:00–15:30  Preparar aula de IA", resultado["resposta"])
        self.assertIn("Pendências: B: Não coube.", resultado["resposta"])


class TestFerramentasDoPlanejador(unittest.TestCase):
    """Dependem de q11-agentes-classico-vs-llm/planejador.py (não rodam sem a Q11)."""

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


if __name__ == "__main__":
    unittest.main()
