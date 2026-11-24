"""
Etapa 2: limpeza e classificação.

1. Junta a coleta nova com os brutos do projeto 1 (só Analista vem do projeto 1)
2. Remove repetidas: mesmo link, ou mesmo título + empresa
3. Classifica o cargo pelo título (Analista, Cientista, Engenheiro, Híbrido, Outra área)
4. Exige descrição, classifica senioridade e modelo de trabalho
5. Aplica a janela de datas comum aos três cargos

Rode sozinho com:  python -m src.limpeza
Saídas: data/processed/vagas_limpas.csv, outputs/tabelas/funil.csv,
        outputs/tabelas/titulos_hibridos.csv, outputs/validacao/titulos_outra_area.csv
"""

import re
import unicodedata
from pathlib import Path

import pandas as pd

from src import config

PASTA_RAW = Path("data/raw")
ARQUIVO_SAIDA = Path("data/processed/vagas_limpas.csv")
PASTA_TABELAS = Path("outputs/tabelas")
PASTA_VALIDACAO = Path("outputs/validacao")


def normalizar(texto) -> str:
    """Minúsculas, sem acentos, sem marcação de markdown. 'Cientísta' -> 'cientista'."""
    if not isinstance(texto, str):
        return ""
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = texto.lower()
    texto = re.sub(r"[*_#`>\[\]\\]", " ", texto)
    return re.sub(r"\s+", " ", texto).strip()


def classificar_cargo(titulo_norm: str) -> tuple[str, str]:
    """Devolve (classe, detalhe). A ordem das regras é a prioridade."""
    if re.search(config.TITULO_ENGENHEIRO_NOME, titulo_norm):
        return "Engenheiro", ""
    if re.search(config.TITULO_CIENTISTA_NOME, titulo_norm):
        return "Cientista", ""
    for nome, padrao in config.TITULO_HIBRIDO.items():
        if re.search(padrao, titulo_norm):
            return "Híbrido (excluído)", nome
    if re.search(config.TITULO_ENGENHEIRO_AREA, titulo_norm):
        return "Engenheiro", ""
    if re.search(config.TITULO_CIENTISTA_AREA, titulo_norm):
        return "Cientista", ""
    if (re.search(config.TITULO_ANALISTA_INCLUIR, titulo_norm)
            and re.search(config.TITULO_ANALISTA_TEMA, titulo_norm)
            and not re.search(config.TITULO_OUTRA_AREA, titulo_norm)):
        return "Analista", ""
    return "Outra área", ""


def classificar_senioridade(titulo_norm: str) -> str:
    for nivel, padrao in config.SENIORIDADE:
        if re.search(padrao, titulo_norm):
            return nivel
    return config.SEM_SENIORIDADE


def _modelo_em(texto: str) -> str | None:
    for nome, padrao in config.MODELO_TRABALHO:
        if re.search(padrao, texto):
            return nome
    return None


def classificar_modelo(linha) -> str:
    """Título e local primeiro; depois o campo is_remote; depois o trecho da descrição
    que fala de modelo/regime de trabalho."""
    achado = _modelo_em(f"{linha['titulo_norm']} {normalizar(linha.get('location'))}")
    if achado:
        return achado
    if str(linha.get("is_remote")).lower() == "true":
        return "Remoto"
    desc = linha["descricao_norm"]
    for m in re.finditer(r"(modelo|regime|formato|local) (de )?(trabalho|atuacao|contratacao)", desc):
        achado = _modelo_em(desc[m.start(): m.end() + 60])
        if achado:
            return achado
    for nome, padrao in config.MODELO_DESCRICAO:
        if re.search(padrao, desc):
            return nome
    return "Não informado"


def carregar_brutos() -> pd.DataFrame:
    partes = []
    for arq in sorted(PASTA_RAW.glob("*.csv")):
        d = pd.read_csv(arq, encoding="utf-8-sig")
        d["origem"] = "projeto2"
        partes.append(d)
    if not partes:
        raise SystemExit("Nenhum CSV em data/raw/. Rode a coleta: python -m src.coleta")
    p1 = Path(config.PASTA_RAW_PROJETO1)
    for arq in sorted(p1.glob("*.csv")) if p1.exists() else []:
        d = pd.read_csv(arq, encoding="utf-8-sig")
        d["origem"] = "projeto1"
        d["cargo_busca"] = "Analista"
        d["data_coleta"] = arq.stem.split("_")[-1]
        partes.append(d)
    print(f"📂 {len(partes)} arquivo(s) lidos (projeto 1 incluído: {p1.exists()})")
    return pd.concat(partes, ignore_index=True)


def janela_comum(df: pd.DataFrame) -> pd.Timestamp | None:
    if config.JANELA_INICIO != "auto":
        return pd.Timestamp(config.JANELA_INICIO)
    datas = pd.to_datetime(df["date_posted"], errors="coerce")
    minimos = [datas[df["cargo"] == c].min() for c in config.CARGOS]
    minimos = [m for m in minimos if pd.notna(m)]
    return max(minimos) if minimos else None


def limpar() -> pd.DataFrame:
    df = carregar_brutos()
    funil = [("Vagas coletadas (com repetidas)", len(df))]

    # Projeto 2 primeiro: na deduplicação, a versão mais nova da vaga é a que fica
    df = df.sort_values("origem", ascending=False)
    df["titulo_norm"] = df["title"].map(normalizar)
    df["empresa_norm"] = df["company"].map(normalizar)
    df = df.drop_duplicates(subset=["job_url"])
    df = df.drop_duplicates(subset=["titulo_norm", "empresa_norm"])
    funil.append(("Sem repetidas", len(df)))

    classes = df["titulo_norm"].map(classificar_cargo)
    df["cargo"] = classes.str[0]
    df["hibrido_tipo"] = classes.str[1]

    # Do projeto 1, só Analista (Cientista/Engenheiro de lá vieram de buscas por "analista")
    vindas_p1_descartadas = int(((df["origem"] == "projeto1") & (df["cargo"] != "Analista")).sum())
    df = df[~((df["origem"] == "projeto1") & (df["cargo"] != "Analista"))]
    funil.append(("Do projeto 1, fora de Analista (descartadas)", vindas_p1_descartadas))

    PASTA_TABELAS.mkdir(parents=True, exist_ok=True)
    PASTA_VALIDACAO.mkdir(parents=True, exist_ok=True)
    hib = df[df["cargo"] == "Híbrido (excluído)"]
    (hib.groupby("hibrido_tipo").size().rename("vagas").reset_index()
        .to_csv(PASTA_TABELAS / "titulos_hibridos.csv", index=False, encoding="utf-8-sig"))
    (df[df["cargo"] == "Outra área"]["title"].value_counts().rename("vagas").reset_index()
        .to_csv(PASTA_VALIDACAO / "titulos_outra_area.csv", index=False, encoding="utf-8-sig"))

    funil.append(("Híbridos excluídos", len(hib)))
    funil.append(("Outra área", int((df["cargo"] == "Outra área").sum())))
    df = df[df["cargo"].isin(config.CARGOS)].copy()

    df["descricao_norm"] = df["description"].map(normalizar)
    df = df[df["descricao_norm"].str.len() >= 200]
    funil.append(("Dos 3 cargos, com descrição", len(df)))

    inicio = janela_comum(df)
    if inicio is not None:
        datas = pd.to_datetime(df["date_posted"], errors="coerce")
        df = df[datas.isna() | (datas >= inicio)]
    funil.append((f"Na janela comum (desde {inicio.date() if inicio is not None else '-'})", len(df)))
    for c in config.CARGOS:
        funil.append((f"  {c}", int((df["cargo"] == c).sum())))

    df["senioridade"] = df["titulo_norm"].map(classificar_senioridade)
    df["modelo_trabalho"] = df.apply(classificar_modelo, axis=1)
    df["janela_inicio"] = inicio.date().isoformat() if inicio is not None else ""

    ARQUIVO_SAIDA.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(ARQUIVO_SAIDA, index=False, encoding="utf-8-sig")
    pd.DataFrame(funil, columns=["etapa", "vagas"]).to_csv(
        PASTA_TABELAS / "funil.csv", index=False, encoding="utf-8-sig")

    print("\n🧹 Funil:")
    for nome, n in funil:
        print(f"   {nome:<45} {n:>6}")
    print(f"   (vagas do projeto 1 descartadas por não serem Analista: {vindas_p1_descartadas})")
    print("\n🧩 Híbridos excluídos:", hib["hibrido_tipo"].value_counts().to_dict())
    print("\n📊 Senioridade por cargo:")
    print(pd.crosstab(df["senioridade"], df["cargo"]).to_string())
    print(f"\n💾 {ARQUIVO_SAIDA}")
    return df


if __name__ == "__main__":
    limpar()
