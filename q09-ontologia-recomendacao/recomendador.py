"""
Q9 - Sistema de recomendação de filmes baseado na ontologia OWL.

Fluxo:
  1. Carrega a ontologia (data/filmes.owl) e roda o raciocinador HermiT.
  2. Para o usuário, consulta os filmes que ele ainda não viu e que são compatíveis com a idade.
  3. Pontua cada filme pelas relações do conhecimento (gênero, diretor, ator, filme parecido)
     e devolve os motivos de cada pontuação, para que a recomendação seja justificada.

Pesos (escolhidos pelo autor, didáticos):
  gênero que o usuário gosta    +2 por gênero em comum
  diretor favorito              +3
  ator favorito                 +2 por ator em comum
  parecido com um filme visto   +1 por filme visto que está em similarA

Uso:
    python3 recomendador.py          # recomendações para os usuários da ontologia
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from owlready2 import World, sync_reasoner_hermit

PASTA = Path(__file__).resolve().parent
CAMINHO_OWL = PASTA / "data" / "filmes.owl"

PESO_GENERO = 2
PESO_DIRETOR = 3
PESO_ATOR = 2
PESO_SIMILAR = 1


@dataclass
class Recomendacao:
    titulo: str
    pontos: int
    motivos: list[str] = field(default_factory=list)


def carregar(caminho: Path = CAMINHO_OWL):
    """Carrega a ontologia em um mundo próprio e roda o raciocinador."""
    mundo = World()
    onto = mundo.get_ontology(f"file://{caminho}").load()
    sync_reasoner_hermit(onto, infer_property_values=True)
    return onto


def individuo(onto, nome: str):
    """Indivíduo pelo nome (o identificador usado no arquivo)."""
    achado = onto.search_one(iri=f"*#{nome}")
    if achado is None:
        raise KeyError(f"indivíduo não encontrado: {nome}")
    return achado


def _nome_genero(g) -> str:
    return g.name.replace("genero_", "")


def recomendar(onto, usuario_id: str, k: int = 5) -> list[Recomendacao]:
    """Os k filmes mais adequados ao usuário, com os motivos de cada pontuação."""
    usuario = individuo(onto, usuario_id)
    ja_vistos = set(usuario.viu)

    resultados: list[Recomendacao] = []
    for filme in onto.Filme.instances():
        if filme in ja_vistos:
            continue
        # Restrição de idade: a classificação do filme não pode ser mais restrita que o usuário.
        if filme.temClassificacao.idadeMinima > usuario.idadeUsuario:
            continue

        pontos = 0
        motivos: list[str] = []

        for g in filme.temGenero:
            if g in usuario.gostaDeGenero:
                pontos += PESO_GENERO
                motivos.append(f"+{PESO_GENERO} gênero {_nome_genero(g)} (que você gosta)")

        for d in filme.dirigidoPor:
            if d in usuario.gostaDeDiretor:
                pontos += PESO_DIRETOR
                motivos.append(f"+{PESO_DIRETOR} dirigido por {d.nome} (diretor favorito)")

        for a in filme.temAtor:
            if a in usuario.gostaDeAtor:
                pontos += PESO_ATOR
                motivos.append(f"+{PESO_ATOR} com {a.nome} (ator favorito)")

        for outro in filme.similarA:
            if outro in ja_vistos:
                pontos += PESO_SIMILAR
                motivos.append(f"+{PESO_SIMILAR} parecido com {outro.titulo}, que você já viu")

        if pontos > 0:
            resultados.append(Recomendacao(filme.titulo, pontos, motivos))

    resultados.sort(key=lambda r: (-r.pontos, r.titulo))
    return resultados[:k]


def perfil_inferido(onto, usuario_id: str) -> list[str]:
    """Classes definidas por axioma às quais o usuário pertence (inferidas pelo raciocinador)."""
    usuario = individuo(onto, usuario_id)
    return sorted(c.name for c in usuario.is_a if c in (onto.FanDeTerror,))


def main() -> None:
    onto = carregar()
    for uid in ["ana", "bruno", "carla", "diego"]:
        usuario = individuo(onto, uid)
        perfil = perfil_inferido(onto, uid)
        print(f"\n{uid.capitalize()} (idade {usuario.idadeUsuario})"
              + (f"  | perfil inferido: {', '.join(perfil)}" if perfil else ""))
        for i, r in enumerate(recomendar(onto, uid), 1):
            print(f"  {i}. {r.titulo}  (pontos: {r.pontos})")
            for m in r.motivos:
                print(f"       {m}")


if __name__ == "__main__":
    main()
