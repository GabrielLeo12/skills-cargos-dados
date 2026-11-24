"""
Etapa de validação: gera amostras para LER antes de confiar nos números.

Rode depois da limpeza:  python -m src.validacao
Saídas em outputs/validacao/:
  amostras_skills.md   até 15 trechos por skill, com a palavra encontrada em [colchetes]
  amostras_titulos.md  títulos sorteados de cada classe (para achar erros de classificação)
  titulos_outra_area.csv (gerado na limpeza) — procure falsos negativos aqui
"""

import re
from pathlib import Path

import pandas as pd

from src import config

ARQUIVO_LIMPO = Path("data/processed/vagas_limpas.csv")
PASTA = Path("outputs/validacao")
N_AMOSTRAS = 15


def trecho(texto: str, padrao: str, raio: int = 70) -> str | None:
    m = re.search(padrao, texto)
    if not m:
        return None
    a, b = max(0, m.start() - raio), min(len(texto), m.end() + raio)
    return f"...{texto[a:m.start()]}[{texto[m.start():m.end()]}]{texto[m.end():b]}..."


def gerar(skills: list[str] | None = None, semente: int = 7) -> None:
    PASTA.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(ARQUIVO_LIMPO, encoding="utf-8-sig")
    df["descricao_norm"] = df["descricao_norm"].fillna("")
    skills = skills or list(config.SKILLS)

    L = ["# Amostras por skill", "",
         "Para cada skill: quantas vagas deram positivo e até 15 trechos sorteados.",
         "Marque mentalmente: o trecho fala MESMO da skill? Se muitos não falarem, ajuste o regex.", ""]
    for s in skills:
        padrao = config.SKILLS[s][1]
        pos = df[df["descricao_norm"].str.contains(padrao, regex=True)]
        L.append(f"## {s}  —  {len(pos)} vagas  (regex: `{padrao}`)")
        for r in pos.sample(min(N_AMOSTRAS, len(pos)), random_state=semente).itertuples():
            L.append(f"- [{r.cargo}] {trecho(r.descricao_norm, padrao)}")
        L.append("")
    (PASTA / "amostras_skills.md").write_text("\n".join(L), encoding="utf-8")

    T = ["# Amostras de títulos por classe", ""]
    for c in config.CARGOS:
        d = df[df["cargo"] == c]
        T.append(f"## {c} ({len(d)} vagas)")
        T += [f"- {t}" for t in d["title"].sample(min(40, len(d)), random_state=semente)]
        T.append("")
    (PASTA / "amostras_titulos.md").write_text("\n".join(T), encoding="utf-8")
    print(f"📝 {PASTA / 'amostras_skills.md'}\n📝 {PASTA / 'amostras_titulos.md'}")


if __name__ == "__main__":
    gerar()
