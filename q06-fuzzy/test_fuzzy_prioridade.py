import math

import pytest

import fuzzy_prioridade as fuzzy


@pytest.mark.parametrize(
    ("prazo", "importancia", "esforco"),
    [
        (2, 9, 150),
        (24, 5, 60),
        (60, 2, 20),
        (72, 10, 180),
    ],
)
def test_inferencias_automatica_e_manual_coincidem(
    prazo, importancia, esforco
):
    automatica = fuzzy.inferir(prazo, importancia, esforco)
    manual, agregada = fuzzy.inferencia_manual(
        prazo, importancia, esforco, verbose=False
    )

    assert automatica == pytest.approx(manual, abs=1e-6)
    assert 0 <= automatica <= 100
    assert agregada.shape == fuzzy.u_prio.shape
    assert agregada.any()


@pytest.mark.parametrize(
    ("prazo", "importancia", "esforco"),
    [
        (-1, 5, 60),
        (73, 5, 60),
        (24, -1, 60),
        (24, 11, 60),
        (24, 5, -1),
        (24, 5, 181),
        (math.nan, 5, 60),
        (24, math.inf, 60),
    ],
)
@pytest.mark.parametrize("inferidor", ["inferir", "inferencia_manual"])
def test_entradas_fora_do_universo_sao_rejeitadas(
    prazo, importancia, esforco, inferidor
):
    funcao = getattr(fuzzy, inferidor)

    with pytest.raises(ValueError):
        if inferidor == "inferencia_manual":
            funcao(prazo, importancia, esforco, verbose=False)
        else:
            funcao(prazo, importancia, esforco)


def test_esforco_grande_eleva_prioridade_com_prazo_proximo():
    prioridade_esforco_pequeno = fuzzy.inferir(24, 5, 20)
    prioridade_esforco_grande = fuzzy.inferir(24, 5, 150)

    assert prioridade_esforco_grande > prioridade_esforco_pequeno


def test_esforco_pequeno_reduz_prioridade_com_prazo_folgado():
    prioridade_esforco_pequeno = fuzzy.inferir(45, 5, 20)
    prioridade_esforco_grande = fuzzy.inferir(45, 5, 150)

    assert prioridade_esforco_pequeno < prioridade_esforco_grande
