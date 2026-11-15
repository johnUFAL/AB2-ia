import json

from planejador import ATIVIDADES, ferramenta_planejar, minutos, verificar

PEDIDO = ("Preciso preparar uma aula de Inteligência Artificial, corrigir trabalhos de alunos e "
          "participar de uma reunião de pesquisa. Tenho apenas quatro horas disponíveis hoje. "
          "A preparação da aula é urgente, mas a correção dos trabalhos precisa ser concluída até "
          "amanhã. Organize minhas atividades da melhor maneira possível.")

# Dados que seriam extraídos do pedido antes de chamar o planejador.
INTERPRETACAO_ESPERADA = {
    "janela": {"inicio": "14:00", "fim": "18:00"},
    "atividades": [
        {"id": "A", "nome": "Preparar aula de IA", "duracao_min": 90, "prioridade": "Alta", "prazo": "hoje"},
        {"id": "B", "nome": "Corrigir trabalhos", "duracao_min": 120, "prioridade": "Media", "prazo": "amanha"},
        {"id": "C", "nome": "Reunião de pesquisa", "duracao_min": 60, "prioridade": "Alta", "prazo": "hoje",
         "inicio_fixo": "16:00"},
        {"id": "D", "nome": "Revisar artigo", "duracao_min": 60, "prioridade": "Baixa", "prazo": "semana"},
    ],
}

# Exemplos de planos inválidos para testar o verificador.
PLANOS_INGENUOS = {
    "Correção antes da reunião": [
        ("B", "14:00", "16:00"), ("C", "16:00", "17:00"), ("A", "17:00", "18:30"),
    ],
    "Aula com duração insuficiente": [
        ("A", "14:00", "15:00"), ("B", "15:00", "17:00"), ("C", "16:00", "17:00"),
    ],
    "Aula dividida em dois horários": [
        ("A", "14:00", "15:00"), ("B", "15:00", "16:00"), ("C", "16:00", "17:00"), ("A", "17:00", "17:30"),
    ],
}


def main() -> None:
    print("Demonstração com dados definidos no código (sem chamada a modelo).")
    print("\nPedido:\n  " + PEDIDO)

    print("\nDados estruturados enviados ao planejador:")
    print(json.dumps(INTERPRETACAO_ESPERADA, ensure_ascii=False, indent=2))
    resposta = ferramenta_planejar(INTERPRETACAO_ESPERADA)

    print("\nPlano calculado:")
    for b in resposta["plano"]:
        print(f"  {b['inicio']}-{b['fim']}  {b['id']}")
    violacoes = ", ".join(resposta["violacoes"]) if resposta["violacoes"] else "nenhuma"
    print(f"  Utilidade: {resposta['utilidade']} | violações: {violacoes}")
    for i, motivo in resposta["nao_realizadas"].items():
        print(f"  Pendente {i}: {motivo}")

    print("\nPlanos rejeitados pelo verificador:")
    for titulo, plano in PLANOS_INGENUOS.items():
        blocos = [(i, minutos(a), minutos(b)) for i, a, b in plano]
        erros = verificar(blocos, ATIVIDADES)
        print(f"\n{titulo}")
        print("  " + " | ".join(f"{a}-{b} {i}" for i, a, b in plano))
        print("  " + ("Válido" if not erros else "Inválido:"))
        for e in erros:
            print(f"    - {e}")


if __name__ == "__main__":
    main()
