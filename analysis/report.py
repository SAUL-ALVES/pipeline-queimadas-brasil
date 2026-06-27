"""
report.py

Gera automaticamente um relatório textual da execução do pipeline.
"""

from pathlib import Path
import logging
import pandas as pd

logger = logging.getLogger("pipeline.report")


class Report:

    def __init__(self, df: pd.DataFrame, output_file: Path):

        self.df = df.copy()
        self.output_file = Path(output_file)


    def gerar(self):

        estado_top = (
            self.df.groupby("estado")["numero_queimadas"]
            .sum()
            .idxmax()
        )

        regiao_top = (
            self.df.groupby("regiao")["numero_queimadas"]
            .sum()
            .idxmax()
        )

        ano_top = (
            self.df.groupby("ano")["numero_queimadas"]
            .sum()
            .idxmax()
        )

        mes_top = (
            self.df.groupby("mes")["numero_queimadas"]
            .sum()
            .idxmax()
        )

        total = len(self.df)

        linhas = [
            "=" * 60,
            "RELATÓRIO DO PIPELINE DE QUEIMADAS",
            "=" * 60,
            "",
            f"Total de registros.............: {total:,}",
            f"Estados analisados............: {self.df['estado'].nunique()}",
            f"Regiões analisadas............: {self.df['regiao'].nunique()}",
            f"Período.......................: {self.df['ano'].min()} - {self.df['ano'].max()}",
            "",
            f"Média de queimadas............: {self.df['numero_queimadas'].mean():.2f}",
            f"Mediana.......................: {self.df['numero_queimadas'].median():.2f}",
            f"Máximo........................: {self.df['numero_queimadas'].max():.2f}",
            f"Mínimo........................: {self.df['numero_queimadas'].min():.2f}",
            "",
            f"Estado com maior ocorrência...: {estado_top}",
            f"Região com maior ocorrência...: {regiao_top}",
            f"Ano mais crítico..............: {ano_top}",
            f"Mês mais crítico..............: {mes_top}",
            "",
            "=" * 60,
            "Relatório gerado automaticamente pelo pipeline.",
            "=" * 60,
        ]

        self.output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(self.output_file, "w", encoding="utf-8") as arquivo:
            arquivo.write("\n".join(linhas))

        logger.info("Relatório salvo em: %s", self.output_file)