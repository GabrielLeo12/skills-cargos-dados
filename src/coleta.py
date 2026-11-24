"""
Etapa 1: coleta no Indeed Brasil, por cargo.

Rode sozinho com:  python -m src.coleta
Saída: data/raw/vagas_cargos_AAAA-MM-DD.csv  (uma linha por vaga encontrada em cada busca)
"""

import time
from datetime import date
from pathlib import Path

import pandas as pd
from jobspy import scrape_jobs

from src import config

PASTA_RAW = Path("data/raw")


def montar_buscas() -> list[tuple[str, str]]:
    """Lista de (cargo_da_busca, termo)."""
    buscas = []
    for cargo, termos in config.TERMOS_POR_CARGO.items():
        for termo in termos:
            buscas.append((cargo, termo))
        for nivel in config.NIVEIS_BUSCA:
            buscas.append((cargo, f"{config.TERMO_PRINCIPAL[cargo]} {nivel}"))
    return buscas


def coletar_termo(cargo: str, termo: str) -> pd.DataFrame:
    print(f"\n🔎 [{cargo}] '{termo}' ...")
    try:
        df = scrape_jobs(
            site_name=["indeed"],
            search_term=termo,
            location=config.LOCAL,
            country_indeed=config.PAIS_INDEED,
            results_wanted=config.VAGAS_POR_TERMO,
            hours_old=config.DIAS_ATRAS * 24,
            description_format="markdown",
            verbose=0,
        )
    except Exception as erro:
        print(f"   ⚠️  Erro: {erro}")
        return pd.DataFrame()
    df["cargo_busca"] = cargo
    df["termo_busca"] = termo
    df["data_coleta"] = date.today().isoformat()
    datas = pd.to_datetime(df["date_posted"], errors="coerce")
    mais_antiga = datas.min().date() if datas.notna().any() else "?"
    print(f"   ✅ {len(df)} vagas (mais antiga: {mais_antiga})")
    return df


def coletar() -> Path:
    PASTA_RAW.mkdir(parents=True, exist_ok=True)
    buscas = montar_buscas()
    print(f"Serão {len(buscas)} buscas. Isso leva de 30 a 60 minutos.")

    resultados = []
    for i, (cargo, termo) in enumerate(buscas):
        resultados.append(coletar_termo(cargo, termo))
        if i < len(buscas) - 1:
            time.sleep(config.PAUSA_ENTRE_BUSCAS)

    vagas = pd.concat(resultados, ignore_index=True)
    if vagas.empty:
        raise SystemExit("Nenhuma vaga coletada. Veja 'Problemas comuns' no README.")

    arquivo = PASTA_RAW / f"vagas_cargos_{date.today().isoformat()}.csv"
    vagas.to_csv(arquivo, index=False, encoding="utf-8-sig")

    print("\n📦 Vagas brutas por cargo da busca:")
    print(vagas.groupby("cargo_busca").size().to_string())
    datas = pd.to_datetime(vagas["date_posted"], errors="coerce")
    print(f"\n📅 Datas de publicação: {datas.min().date()} a {datas.max().date()}")
    print(f"💾 Salvo em: {arquivo}")
    return arquivo


if __name__ == "__main__":
    coletar()
