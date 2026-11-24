"""Gráficos do projeto 2, com a mesma identidade visual do projeto 1 (1080 × 1350 px)."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.transforms import blended_transform_factory

from src import config

PASTA = Path("outputs/graficos")
FUNDO, TINTA, TINTA_2, TINTA_FRACA, GRADE = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9"
COR_CARGO = {"Analista": "#2a78d6", "Cientista": "#eb6834", "Engenheiro": "#1baf7a"}
RAMPA = LinearSegmentedColormap.from_list(
    "azul", ["#f4f8fd", "#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"])


def _base(fig):
    fig.patch.set_facecolor(FUNDO)


def _textos(fig, titulo, subtitulo, rodape):
    fig.text(0.06, 0.965, titulo, fontsize=22, fontweight="bold", color=TINTA, va="top")
    fig.text(0.06, 0.928, subtitulo, fontsize=12.5, color=TINTA_2, va="top")
    fig.text(0.06, 0.022, rodape, fontsize=10.5, color=TINTA_FRACA, va="bottom")


GRUPOS = ["Base comum"] + config.CARGOS


def _escolher_skills(p: pd.DataFrame) -> pd.DataFrame:
    """As N skills com maior % em algum cargo. Ficam no topo as da base comum
    (>= LIMIAR nos três); as outras, agrupadas pelo cargo em que são mais fortes."""
    sel = p.loc[p.max(axis=1).nlargest(config.N_SKILLS_HEATMAP).index].copy()
    comum = (sel[config.CARGOS] >= config.LIMIAR_BASE_COMUM).all(axis=1)
    sel["grupo"] = np.where(comum, "Base comum", sel[config.CARGOS].idxmax(axis=1))
    sel["ordem_grupo"] = sel["grupo"].map({g: i for i, g in enumerate(GRUPOS)})
    sel["valor_grupo"] = sel.apply(lambda r: r[config.CARGOS].min() if r["grupo"] == "Base comum" else r[r["grupo"]], axis=1)
    return sel.sort_values(["ordem_grupo", "valor_grupo"], ascending=[True, False])


def heatmap(p: pd.DataFrame, n: pd.Series, per: str) -> Path:
    sel = _escolher_skills(p)
    dados = sel[config.CARGOS].values

    fig = plt.figure(figsize=(10.8, 13.5), dpi=100)
    _base(fig)
    ax = fig.add_axes([0.30, 0.07, 0.62, 0.78])
    ax.set_facecolor(FUNDO)
    ax.imshow(dados, cmap=RAMPA, vmin=0, vmax=100, aspect="auto")

    for i in range(dados.shape[0]):
        for j in range(dados.shape[1]):
            v = dados[i, j]
            ax.text(j, i, f"{v:.0f}%", ha="center", va="center", fontsize=15,
                    fontweight="bold" if v >= 40 else "normal",
                    color="#ffffff" if v >= 55 else TINTA)
    # linhas finas separando as células e os grupos
    ax.set_xticks(np.arange(-.5, 3, 1), minor=True)
    ax.set_yticks(np.arange(-.5, len(sel), 1), minor=True)
    ax.grid(which="minor", color=FUNDO, linewidth=3)
    ax.tick_params(which="both", length=0)
    # separadores e rótulos dos grupos na lateral esquerda
    grupos = sel["grupo"].tolist()
    inicio = 0
    for k in range(1, len(grupos) + 1):
        if k == len(grupos) or grupos[k] != grupos[k - 1]:
            if k < len(grupos):
                ax.axhline(k - 0.5, color=TINTA_2, linewidth=1.2)
            meio = (inicio + k - 1) / 2
            rotulo = grupos[inicio] if grupos[inicio] == "Base comum" else f"+ {grupos[inicio]}"
            ax.annotate(rotulo, xy=(0, meio), xycoords=("figure fraction", "data"), xytext=(0.035, meio),
                        textcoords=("figure fraction", "data"), rotation=90, ha="center", va="center",
                        fontsize=12, fontweight="bold",
                        color=COR_CARGO.get(grupos[inicio], TINTA_2), annotation_clip=False)
            trans = blended_transform_factory(fig.transFigure, ax.transData)
            ax.plot([0.052, 0.052], [inicio - 0.42, k - 0.58], transform=trans, clip_on=False,
                    color=COR_CARGO.get(grupos[inicio], TINTA_2), linewidth=2.5)
            inicio = k

    ax.set_xlim(-0.5, 2.5)
    ax.set_ylim(len(sel) - 0.5, -0.5)
    ax.set_xticks(range(3))
    ax.set_xticklabels([f"{c}\n(n={n[c]})" for c in config.CARGOS], fontsize=14, color=TINTA)
    ax.xaxis.tick_top()
    ax.set_yticks(range(len(sel)))
    ax.set_yticklabels(sel.index, fontsize=14, color=TINTA)
    for s in ax.spines.values():
        s.set_visible(False)

    _textos(fig, "O que cada cargo de dados pede",
            f"% das vagas que citam cada skill · {n.sum()} vagas · {config.FONTE} · {per}\n"
            f"Agrupadas: base comum (≥ {config.LIMIAR_BASE_COMUM}% nos três) e o cargo em que cada skill é mais pedida",
            f"Fonte: vagas públicas do {config.FONTE} · Análise: {config.AUTOR}")
    arq = PASTA / "heatmap_cargos.png"
    PASTA.mkdir(parents=True, exist_ok=True)
    fig.savefig(arq, facecolor=FUNDO)
    plt.close(fig)
    return arq


def grafico_pontes(pts: pd.DataFrame, n: pd.Series, per: str) -> Path:
    fig = plt.figure(figsize=(10.8, 13.5), dpi=100)
    _base(fig)
    paineis = [("Cientista", [0.30, 0.50, 0.62, 0.33]), ("Engenheiro", [0.30, 0.08, 0.62, 0.33])]
    for alvo, pos in paineis:
        d = pts[pts["alvo"] == alvo].iloc[::-1]
        ax = fig.add_axes(pos)
        ax.set_facecolor(FUNDO)
        y = np.arange(len(d))
        ax.hlines(y, d["pct_analista"], d["pct_alvo"], color=GRADE, linewidth=5, zorder=1)
        ax.scatter(d["pct_analista"], y, s=210, color=COR_CARGO["Analista"], edgecolor=FUNDO, linewidth=2, zorder=2)
        ax.scatter(d["pct_alvo"], y, s=210, color=COR_CARGO[alvo], edgecolor=FUNDO, linewidth=2, zorder=3)
        for yi, r in zip(y, d.itertuples()):
            ax.text(r.pct_alvo + 2.5, yi, f"+{r.diferenca_pp:.0f} p.p.", va="center", fontsize=13,
                    fontweight="bold", color=TINTA)
        ax.set_yticks(y)
        ax.set_yticklabels(d["skill"], fontsize=15, color=TINTA)
        ax.set_xlim(0, 105)
        ax.set_xticks([0, 25, 50, 75, 100])
        ax.set_xticklabels(["0%", "25%", "50%", "75%", "100%"], fontsize=11, color=TINTA_FRACA)
        ax.grid(axis="x", color=GRADE, linewidth=0.8)
        ax.set_axisbelow(True)
        ax.tick_params(length=0)
        for s in ax.spines.values():
            s.set_visible(False)
        topo = pos[1] + pos[3] + 0.035
        fig.text(0.06, topo, f"De Analista para {alvo}", fontsize=17, fontweight="bold", color=TINTA)
        for x, cargo in [(0.06, "Analista"), (0.30, alvo)]:
            fig.text(x, topo - 0.028, "●", fontsize=14, color=COR_CARGO[cargo])
            fig.text(x + 0.022, topo - 0.028, f"{cargo} (n={n[cargo]})", fontsize=12.5, color=TINTA_2)

    _textos(fig, "O que o Analista precisa somar para migrar",
            f"As 5 skills com maior diferença · % das vagas que citam a skill · {config.FONTE} · {per}",
            f"Fonte: vagas públicas do {config.FONTE} · Análise: {config.AUTOR}")
    arq = PASTA / "pontes.png"
    fig.savefig(arq, facecolor=FUNDO)
    plt.close(fig)
    return arq
