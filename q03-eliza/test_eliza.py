import unittest

from eliza import Eliza


class TestEliza(unittest.TestCase):
    def setUp(self):
        self.eliza = Eliza()

    def test_palavra_chave_de_maior_prioridade_e_selecionada(self):
        resposta = self.eliza.responder("Minha mãe fala sobre computador.")

        self.assertIn("computador", resposta.lower())
        self.assertEqual(self.eliza.rastro["chave"], "computador")

    def test_transformacao_e_remontagem_de_quero(self):
        resposta = self.eliza.responder("Eu quero estudar")

        self.assertEqual(resposta, "Por que você quer estudar?")

    def test_fala_sobre_familia_pode_ser_relembrada(self):
        resposta = self.eliza.responder("Meu trabalho está difícil")

        self.assertIn('Antes você disse: "seu trabalho está difícil".', resposta)
        self.assertEqual(self.eliza.rastro["chave"], "nenhuma (memória)")

    def test_despedida_encerra_a_conversa(self):
        resposta = self.eliza.responder("Até logo, tchau!")

        self.assertEqual(resposta, "Até logo. Obrigado por conversar comigo.")
        self.assertEqual(self.eliza.rastro["chave"], "despedida")


if __name__ == "__main__":
    unittest.main()
