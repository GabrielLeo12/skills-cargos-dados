"""
Etapa 3: análises.

Métrica (igual ao projeto 1): % = vagas do cargo que citam a skill ÷ total de vagas do cargo.

Rode sozinho com:  python -m src.analise
Saídas em outputs/tabelas/: perfil_cargos.csv, top10_por_cargo.csv, base_comum.csv,
caracteristicas.csv, similaridade.csv, pontes.csv, senioridade_por_cargo.csv (se houver
amostra), modelo_trabalho.csv, base_dashboard.csv, resumo.md
"""

import re
from pathlib import Path

import numpy as np
import pandas as pd

from src import config, graficos

ARQUIVO_LIMPO = Path("data/processed/vagas_limpas.csv")
PASTA = Path("outputs/tabelas")


# ---------------------------------------------------------------------------
# Marcação das skills
# ---------------------------------------------------------------------------
def _cita_fora_da_formacao(texto: str, padrao: str) -> bool:
    for achado in re.finditer(padrao, texto):
        janela = texto[max(0, achado.start() - 120): achado.end() + 60]
        if not re.search(config.PADRAO_FORMACAO, janela):
            return True
    return False


def marcar_skills(df: pd.DataFrame) -> pd.DataFrame:
    for skill, (_, padrao) in config.SKILLS.items():
        if skill in config.IGNORAR_EM_FORMACAO:
            df[skill] = df["descricao_norm"].map(lambda t: _cita_fora_da_formacao(t, padrao))
        else:
            df[skill] = df["descricao_norm"].str.contains(padrao, regex=True)
    return df


def skills_ranking() -> list[str]:
    return [s for s in config.SKILLS if s not in config.FORA_DO_GRAFICO]


# ---------------------------------------------------------------------------
# Cálculos
# ---------------------------------------------------------------------------
def perfil(df: pd.DataFrame) -> pd.DataFrame:
    """Linhas = skills, colunas = cargos, valores = % das vagas (sem arredondar)."""
    tab = df.groupby("cargo")[list(config.SKILLS)].mean().T * 100
    return tab[config.CARGOS]


def top_por_cargo(p: pd.DataFrame) -> pd.DataFrame:
    p = p.loc[skills_ranking()]
    linhas = []
    for c in config.CARGOS:
        for pos, (skill, pct) in enumerate(p[c].sort_values(ascending=False).head(config.TOP_N_PERFIL).items(), 1):
            linhas.append({"cargo": c, "posicao": pos, "skill": skill, "percentual": pct})
    return pd.DataFrame(linhas)


def base_comum(p: pd.DataFrame) -> pd.DataFrame:
    p = p.loc[skills_ranking()]
    comum = p[(p >= config.LIMIAR_BASE_COMUM).all(axis=1)].copy()
    comum["minimo"] = comum.min(axis=1)
    return comum.sort_values("minimo", ascending=False)


def caracteristicas(p: pd.DataFrame) -> pd.DataFrame:
    """Diferença (p.p.) entre o cargo e a média dos outros dois."""
    p = p.loc[skills_ranking()]
    linhas = []
    for c in config.CARGOS:
        outros = [o for o in config.CARGOS if o != c]
        dif = p[c] - p[outros].mean(axis=1)
        for skill, d in dif.sort_values(ascending=False).head(config.TOP_N_PERFIL).items():
            linhas.append({"cargo": c, "skill": skill, "pct_cargo": p.at[skill, c],
                           "pct_media_outros": p.loc[skill, outros].mean(), "diferenca_pp": d})
    return pd.DataFrame(linhas)


def similaridade(p: pd.DataFrame) -> pd.DataFrame:
    """Similaridade de cosseno entre os vetores de % dos cargos. Também damos a
    distância média em p.p., que é mais fácil de explicar no artigo."""
    p = p.loc[skills_ranking()]
    linhas = []
    for i, a in enumerate(config.CARGOS):
        for b in config.CARGOS[i + 1:]:
            va, vb = p[a].values, p[b].values
            cos = float(va @ vb / (np.linalg.norm(va) * np.linalg.norm(vb)))
            linhas.append({"par": f"{a} × {b}", "cosseno": cos,
                           "diferenca_media_pp": float(np.abs(va - vb).mean())})
    return pd.DataFrame(linhas).sort_values("cosseno", ascending=False)


def pontes(p: pd.DataFrame) -> pd.DataFrame:
    """Skills com maior diferença entre o cargo-alvo e o Analista."""
    p = p.loc[skills_ranking()]
    linhas = []
    for alvo in ["Cientista", "Engenheiro"]:
        dif = (p[alvo] - p["Analista"]).sort_values(ascending=False).head(config.TOP_N_PONTES)
        for skill, d in dif.items():
            linhas.append({"alvo": alvo, "skill": skill, "pct_analista": p.at[skill, "Analista"],
                           "pct_alvo": p.at[skill, alvo], "diferenca_pp": d})
    return pd.DataFrame(linhas)


def senioridade_por_cargo(df: pd.DataFrame) -> tuple[pd.DataFrame | None, dict]:
    contagem = {c: df[df["cargo"] == c]["senioridade"].value_counts().to_dict() for c in config.CARGOS}
    blocos = []
    for c in config.CARGOS:
        d = df[df["cargo"] == c]
        nj, ns = (d["senioridade"] == "Júnior").sum(), (d["senioridade"] == "Sênior").sum()
        if nj >= config.MIN_VAGAS_SENIORIDADE and ns >= config.MIN_VAGAS_SENIORIDADE:
            t = d[d["senioridade"].isin(["Júnior", "Sênior"])].groupby("senioridade")[skills_ranking()].mean().T * 100
            t["diferenca_pp"] = t["Sênior"] - t["Júnior"]
            t["cargo"] = c
            blocos.append(t.reset_index(names="skill"))
    return (pd.concat(blocos) if blocos else None), contagem


def modelo_trabalho(df: pd.DataFrame) -> pd.DataFrame:
    return (pd.crosstab(df["modelo_trabalho"], df["cargo"], normalize="columns") * 100)[config.CARGOS]


def periodo(df: pd.DataFrame) -> str:
    meses = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
    d = pd.to_datetime(df["date_posted"], errors="coerce").dropna()
    if d.empty:
        return ""
    a, b = d.min(), d.max()
    return f"{meses[a.month-1]}–{meses[b.month-1]}/{b.year}" if a.year == b.year else f"{meses[a.month-1]}/{a.year}–{meses[b.month-1]}/{b.year}"


def exportar_base_dashboard(df: pd.DataFrame) -> None:
    cols = {"title": "titulo", "company": "empresa", "location": "local", "date_posted": "data_publicacao",
            "cargo": "cargo", "senioridade": "senioridade", "modelo_trabalho": "modelo_trabalho", "job_url": "link"}
    base = df[list(cols)].rename(columns=cols)
    for s in config.SKILLS:
        base[s] = df[s].map({True: "Sim", False: "Não"})
    base.to_csv(PASTA / "base_dashboard.csv", index=False, encoding="utf-8-sig", sep=";")


def escrever_resumo(df, p, comum, carac, sim, pts, sen, contagem_sen, modelo, per) -> None:
    n = df["cargo"].value_counts()
    L = ["# Resumo — Analista × Cientista × Engenheiro de Dados", "",
         f"- Vagas analisadas: **{len(df)}** ({config.FONTE}, {per}, janela desde {df['janela_inicio'].iloc[0]})"]
    L += [f"  - {c}: **{n.get(c, 0)}**" for c in config.CARGOS]
    L += ["", "## Top 10 por cargo", ""]
    top = top_por_cargo(p)
    tabela = pd.DataFrame({c: [f"{r.skill} ({r.percentual:.0f}%)" for r in top[top.cargo == c].itertuples()]
                           for c in config.CARGOS}, index=range(1, config.TOP_N_PERFIL + 1))
    L += [tabela.to_markdown(), "", f"## Base comum (≥ {config.LIMIAR_BASE_COMUM}% nos três)", ""]
    L += [f"- {s}: " + " · ".join(f"{c} {r[c]:.0f}%" for c in config.CARGOS) for s, r in comum.iterrows()] or ["- (nenhuma)"]
    L += ["", "## Proximidade entre cargos", "", sim.round(3).to_markdown(index=False), ""]
    L += ["## Pontes (o que falta ao Analista)", ""]
    for alvo in ["Cientista", "Engenheiro"]:
        L.append(f"**Para {alvo}:** " + "; ".join(
            f"{r.skill} ({r.pct_analista:.0f}% → {r.pct_alvo:.0f}%, +{r.diferenca_pp:.0f} p.p.)"
            for r in pts[pts.alvo == alvo].itertuples()))
        L.append("")
    L += ["## Skills características (cargo − média dos outros dois)", ""]
    for c in config.CARGOS:
        L.append(f"**{c}:** " + "; ".join(f"{r.skill} (+{r.diferenca_pp:.0f} p.p.)"
                                          for r in carac[carac.cargo == c].head(5).itertuples()))
    L += ["", "## Júnior × Sênior", ""]
    if sen is None:
        L.append(f"Fora da análise: nenhum cargo tem ≥ {config.MIN_VAGAS_SENIORIDADE} vagas júnior E sênior.")
    else:
        L.append(f"Cargos com amostra suficiente: {', '.join(sen['cargo'].unique())}")
    L.append(f"Contagens: {contagem_sen}")
    L += ["", "## Modelo de trabalho (% das vagas do cargo)", "", modelo.round(0).to_markdown(), ""]
    L += ["## Inglês", ""] + [f"- {c}: {p.at['Inglês', c]:.0f}%" for c in config.CARGOS]
    (PASTA / "resumo.md").write_text("\n".join(L), encoding="utf-8")


def analisar():
    PASTA.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(ARQUIVO_LIMPO, encoding="utf-8-sig")
    df["descricao_norm"] = df["descricao_norm"].fillna("")
    df = marcar_skills(df)
    per = periodo(df)

    p = perfil(df)
    contagem = df.groupby("cargo")[list(config.SKILLS)].sum().T[config.CARGOS]
    saida = p.round(1).add_prefix("pct_").join(contagem.add_prefix("vagas_"))
    saida.insert(0, "categoria", [config.SKILLS[s][0] for s in saida.index])
    saida.to_csv(PASTA / "perfil_cargos.csv", encoding="utf-8-sig", index_label="skill")

    top_por_cargo(p).round(1).to_csv(PASTA / "top10_por_cargo.csv", index=False, encoding="utf-8-sig")
    comum = base_comum(p); comum.round(1).to_csv(PASTA / "base_comum.csv", encoding="utf-8-sig", index_label="skill")
    carac = caracteristicas(p); carac.round(1).to_csv(PASTA / "caracteristicas.csv", index=False, encoding="utf-8-sig")
    sim = similaridade(p); sim.round(4).to_csv(PASTA / "similaridade.csv", index=False, encoding="utf-8-sig")
    pts = pontes(p); pts.round(1).to_csv(PASTA / "pontes.csv", index=False, encoding="utf-8-sig")
    sen, contagem_sen = senioridade_por_cargo(df)
    if sen is not None:
        sen.round(1).to_csv(PASTA / "senioridade_por_cargo.csv", index=False, encoding="utf-8-sig")
    modelo = modelo_trabalho(df); modelo.round(1).to_csv(PASTA / "modelo_trabalho.csv", encoding="utf-8-sig")
    exportar_base_dashboard(df)
    escrever_resumo(df, p, comum, carac, sim, pts, sen, contagem_sen, modelo, per)

    n = df["cargo"].value_counts().reindex(config.CARGOS).fillna(0).astype(int)
    print("\n👥 Vagas por cargo:", n.to_dict())
    print("\n🏆 Top 5 por cargo:")
    for c in config.CARGOS:
        print(f"   {c:<11}", " | ".join(f"{s} {v:.0f}%" for s, v in p.loc[skills_ranking(), c].nlargest(5).items()))
    print("\n🤝 Base comum:", ", ".join(comum.index) or "(nenhuma)")
    print("\n📐 Proximidade (cosseno):")
    for r in sim.itertuples():
        print(f"   {r.par:<26} {r.cosseno:.3f}   (diferença média {r.diferenca_media_pp:.1f} p.p.)")
    print("\n🌉 Pontes:")
    for alvo in ["Cientista", "Engenheiro"]:
        print(f"   → {alvo}:", ", ".join(f"{r.skill} +{r.diferenca_pp:.0f}" for r in pts[pts.alvo == alvo].itertuples()))

    print("\n🎨 Gráficos:")
    print("  ", graficos.heatmap(p.loc[skills_ranking()], n, per))
    print("  ", graficos.grafico_pontes(pts, n, per))
    print(f"\n📝 {PASTA / 'resumo.md'}")


if __name__ == "__main__":
    analisar()
