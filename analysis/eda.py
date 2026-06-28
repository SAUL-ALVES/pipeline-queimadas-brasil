"""
eda.py

Módulo responsável pela Análise Exploratória dos Dados (EDA).

Gera:
- Resumo do dataset
- Estatísticas descritivas
- Top Estados
- Top Regiões
- Top Meses
- Top Anos
- Arquivo estatisticas.csv
"""

from pathlib import Path
import logging
import pandas as pd

logger = logging.getLogger("pipeline.eda")


class EDA:

    def __init__(self, df: pd.DataFrame, output_dir: Path):

        self.df = df.copy()
        self.output_dir = Path(output_dir)

    # ------------------------------------------------------------

    def resumo(self):

        return {

            "Total de registros": len(self.df),

            "Total de colunas": len(self.df.columns),

            "Estados": self.df["estado"].nunique(),

            "Regiões": self.df["regiao"].nunique(),

            "Anos": self.df["ano"].nunique(),

            "Meses": self.df["mes"].nunique(),

            "Ano Inicial": self.df["ano"].min(),

            "Ano Final": self.df["ano"].max()

        }

    # ------------------------------------------------------------

    def estatisticas(self):

        logger.info("Gerando estatísticas descritivas...")

        estatisticas = self.df.describe(include="all")

        arquivo = self.output_dir / "estatisticas.csv"

        estatisticas.to_csv(
            arquivo,
            encoding="utf-8-sig"
        )

        logger.info("Estatísticas salvas em %s", arquivo)

        return estatisticas

    # ------------------------------------------------------------

    def top_estados(self):

        return (

            self.df

            .groupby("estado")["numero_queimadas"]

            .sum()

            .sort_values(ascending=False)

            .head(10)

        )

    # ------------------------------------------------------------

    def top_regioes(self):

        return (

            self.df

            .groupby("regiao")["numero_queimadas"]

            .sum()

            .sort_values(ascending=False)

        )

    # ------------------------------------------------------------

    def top_anos(self):

        return (

            self.df

            .groupby("ano")["numero_queimadas"]

            .sum()

            .sort_values(ascending=False)

        )

    # ------------------------------------------------------------

    def top_meses(self):

        return (

            self.df

            .groupby("mes")["numero_queimadas"]

            .sum()

            .sort_values(ascending=False)

        )

    # ------------------------------------------------------------

    def imprimir(self):

        logger.info("=" * 60)

        logger.info("RESUMO DO DATASET")

        logger.info("=" * 60)

        resumo = self.resumo()

        for chave, valor in resumo.items():

            logger.info("%s : %s", chave, valor)

        logger.info("=" * 60)

        logger.info("TOP 10 ESTADOS")

        logger.info("\n%s", self.top_estados())

        logger.info("=" * 60)

        logger.info("TOP REGIÕES")

        logger.info("\n%s", self.top_regioes())

        logger.info("=" * 60)

        logger.info("TOP ANOS")

        logger.info("\n%s", self.top_anos())

        logger.info("=" * 60)

        logger.info("TOP MESES")

        logger.info("\n%s", self.top_meses())

        logger.info("=" * 60)