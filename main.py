"""
Roda o projeto: coleta -> limpeza -> validação -> análise.

    python main.py                 # tudo
    python main.py --pular-coleta  # usa os CSVs que já estão em data/raw/
"""

import argparse

from src.analise import analisar
from src.coleta import coletar
from src.limpeza import limpar
from src.validacao import gerar as gerar_amostras

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analista × Cientista × Engenheiro de Dados")
    parser.add_argument("--pular-coleta", action="store_true")
    args = parser.parse_args()

    if not args.pular_coleta:
        print("=== 1/4 COLETA ===")
        coletar()
    print("\n=== 2/4 LIMPEZA ===")
    limpar()
    print("\n=== 3/4 AMOSTRAS PARA VALIDAÇÃO ===")
    gerar_amostras()
    print("\n=== 4/4 ANÁLISE ===")
    analisar()
    print("\n🎉 Pronto! Veja outputs/")
