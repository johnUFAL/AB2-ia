import skfuzzy as fuzz
import os
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from skfuzzy import control as ctrl
matplotlib.use("Agg")

FIGS = os.path.join(os.path.dirname(__file__), "figs")

# Universo de discurso
u_prazo = np.arange(0, 72.1, 0.5)
u_imp = np.arange(0, 10.01, 0.1)
u_esf = np.arange(0, 180.1, 1)
u_prio = np.arange(0, 100.1, 0.5)

# Funções de pertinência (a fuzzificação)
prazo = ctrl.Antecedent(u_prazo, "prazo")
prazo["urgente"] = fuzz.trapmf(u_prazo, [0, 0, 4, 12])
prazo["proximo"] = fuzz.trimf(u_prazo, [6, 24, 48])
prazo["folgado"] = fuzz.trapmf(u_prazo, [36, 56, 72, 72])

imp = ctrl.Antecedent(u_imp, "importancia")
imp["baixa"] = fuzz.trapmf(u_imp, [0, 0, 2, 4])
imp["media"] = fuzz.trimf(u_imp, [2, 5, 8])
imp["alta"] = fuzz.trapmf(u_imp, [6, 8, 10, 10])

esf = ctrl.Antecedent(u_esf, "esforco")
esf["pequeno"] = fuzz.trapmf(u_esf, [0, 0, 20, 50])
esf["medio"] = fuzz.trimf(u_esf, [30, 75, 120])
esf["grande"] = fuzz.trapmf(u_esf, [90, 140, 180, 180])

prio = ctrl.Consequent(u_prio, "prioridade")
prio["baixa"] = fuzz.trapmf(u_prio, [0, 0, 15, 35])
prio["media"] = fuzz.trimf(u_prio, [25, 50, 75])
prio["alta"] = fuzz.trapmf(u_prio, [65, 85, 100, 100])

# Base de regras
regras = [
    ctrl.Rule(prazo["urgente"] & imp["alta"], prio["alta"]),
    ctrl.Rule(prazo["urgente"] & imp["media"], prio["alta"]),
    ctrl.Rule(prazo["urgente"] & imp["baixa"], prio["media"]),
    ctrl.Rule(prazo["proximo"] & imp["alta"], prio["alta"]),
    ctrl.Rule(prazo["proximo"] & imp["media"], prio["media"]),
    ctrl.Rule(prazo["proximo"] & imp["baixa"], prio["baixa"]),
    ctrl.Rule(prazo["folgado"] & imp["alta"], prio["media"]),
    ctrl.Rule(prazo["folgado"] & imp["media"], prio["baixa"]),
    ctrl.Rule(prazo["folgado"] & imp["baixa"], prio["baixa"]),
    ctrl.Rule(esf["grande"] & prazo["proximo"], prio["alta"]),
    ctrl.Rule(esf["pequeno"] & prazo["folgado"], prio["baixa"])
]

sistema = ctrl.ControlSystem(regras)


def _validar_entradas(p, i, e):
    limites = ((p, 0, 72, "prazo"), (i, 0, 10, "importancia"),
               (e, 0, 180, "esforco"))
    for valor, minimo, maximo, nome in limites:
        if not np.isfinite(valor) or not minimo <= valor <= maximo:
            raise ValueError(f"{nome} deve estar entre {minimo} e {maximo}")


def inferir(p, i, e):
    _validar_entradas(p, i, e)
    sim = ctrl.ControlSystemSimulation(sistema)
    sim.input["prazo"] = p
    sim.input["importancia"] = i
    sim.input["esforco"] = e
    sim.compute()
    return sim.output["prioridade"]


# Interferência gráfica
def inferencia_manual(p, i, e, verbose=True):
    _validar_entradas(p, i, e)
    gp = {k: fuzz.interp_membership(u_prazo, prazo[k].mf, p) for k in prazo.terms}
    gi = {k: fuzz.interp_membership(u_imp, imp[k].mf, i) for k in imp.terms}
    ge = {k: fuzz.interp_membership(u_esf, esf[k].mf, e) for k in esf.terms}

    R = [
        ([gp["urgente"], gi["alta"]], "alta"),
        ([gp["urgente"], gi["media"]], "alta"),
        ([gp["urgente"], gi["baixa"]], "media"),
        ([gp["proximo"], gi["alta"]], "alta"),
        ([gp["proximo"], gi["media"]], "media"),
        ([gp["proximo"], gi["baixa"]], "baixa"),
        ([gp["folgado"], gi["alta"]], "media"),
        ([gp["folgado"], gi["media"]], "baixa"),
        ([gp["folgado"], gi["baixa"]], "baixa"),
        ([ge["grande"], gp["proximo"]], "alta"),
        ([ge["pequeno"], gp["folgado"]], "baixa")
    ]
    agregada = np.zeros_like(u_prio)
    if verbose:
        print(f"  Fuzzificacao: prazo={ {k: round(v,2) for k,v in gp.items()} }")
        print(f"                import.={ {k: round(v,2) for k,v in gi.items()} }")
        print(f"                esforco={ {k: round(v,2) for k,v in ge.items()} }")
    for n, (ants, saida) in enumerate(R, 1):
        forca = min(ants)
        if forca > 0:
            corte = np.fmin(forca, prio[saida].mf)
            agregada = np.fmax(agregada, corte)
            if verbose:
                print(f"  R{n:<2} dispara com forca {forca:.2f} -> prioridade {saida}")
    return fuzz.defuzz(u_prio, agregada, "centroid"), agregada


# Graficos
def plota_variaveis():
    os.makedirs(FIGS, exist_ok=True)
    for var, nome in [(prazo, "prazo"), (imp, "importancia"),
                      (esf, "esforco"), (prio, "prioridade")]:
        var.view()
        plt.savefig(os.path.join(FIGS, f"mf_{nome}.png"), dpi=130)
        plt.close("all")


def plota_agregacao(p, i, e, nome):
    os.makedirs(FIGS, exist_ok=True)
    c, agg = inferencia_manual(p, i, e, verbose=False)
    plt.figure(figsize=(7, 3))
    for k in prio.terms:
        plt.plot(u_prio, prio[k].mf, "--", lw=1, label=k)
    plt.fill_between(u_prio, agg, alpha=0.4, color="tab:orange", label="agregada")
    plt.axvline(c, color="k", label=f"centroide = {c:.1f}")
    plt.title(f"{nome}: prazo={p}h, import.={i}, esforco={e}min")
    plt.legend(fontsize=7)
    plt.tight_layout()
    plt.savefig(os.path.join(FIGS, f"agregacao_{nome}.png"), dpi=130)
    plt.close("all")


def plota_superficie():
    os.makedirs(FIGS, exist_ok=True)
    P, I = np.meshgrid(np.linspace(0, 72, 25), np.linspace(0, 10, 25))
    Z = np.vectorize(lambda a, b: inferir(a, b, 60))(P, I)
    fig = plt.figure(figsize=(7, 5))
    ax = fig.add_subplot(111, projection="3d")
    ax.plot_surface(P, I, Z, cmap="viridis")
    ax.set_xlabel("prazo (h)")
    ax.set_ylabel("importancia")
    ax.set_zlabel("prioridade")
    plt.savefig(os.path.join(FIGS, "superficie.png"), dpi=130)
    plt.close("all")


if __name__ == "__main__":
    exemplo = (2, 9, 60)
    print(
        "Prioridade para prazo de 2 h, importancia 9 e esforco de 60 min: "
        f"{inferir(*exemplo):.1f}/100"
    )
