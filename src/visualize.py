"""
visualize.py

Responsável por gerar automaticamente gráficos para análise
exploratória do dataset de queimadas.

Gráficos gerados:

✔ Evolução Anual
✔ Top 10 Estados
✔ Queimadas por Região
✔ Queimadas por Mês
✔ Heatmap Ano x Mês
"""

from pathlib import Path
import logging

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd

logger = logging.getLogger("pipeline.visualize")


class Visualizer:

    def __init__(self, df, output_dir):

        self.df = df.copy()

        self.output_dir = Path(output_dir)

        self.output_dir.mkdir(parents=True, exist_ok=True)

    # -------------------------------------------------------

    def grafico_anual(self):

        # Usa a coluna tratada por IQR quando disponivel (winsorizada),
        # para reduzir o efeito visual de valores extremos sem apagar
        # os registros originais. Conforme documentado na secao 8 do README.
        coluna = (
            "numero_queimadas_tratado_iqr"
            if "numero_queimadas_tratado_iqr" in self.df.columns
            else "numero_queimadas"
        )

        dados = (

            self.df

            .groupby("ano")[coluna]

            .sum()

            .sort_index()

        )

        plt.figure(figsize=(12,6))

        plt.plot(dados.index,dados.values,marker="o")

        plt.title("Evolução Anual das Queimadas")

        plt.xlabel("Ano")

        plt.ylabel("Número de Queimadas")

        # Integridade visual: eixo Y iniciado em zero para nao exagerar
        # diferencas pequenas (secao 8 do README).
        plt.ylim(bottom=0)

        plt.grid(True)

        plt.tight_layout()

        plt.savefig(self.output_dir/"01_queimadas_ano.png",dpi=150)

        plt.close()

    # -------------------------------------------------------

    def grafico_estados(self):

        dados=(

            self.df

            .groupby("estado")["numero_queimadas"]

            .sum()

            .sort_values(ascending=False)

            .head(10)

        )

        plt.figure(figsize=(12,6))

        dados.plot(kind="bar")

        plt.title("Top 10 Estados com mais Queimadas")

        plt.ylabel("Número de Queimadas")

        plt.tight_layout()

        plt.savefig(self.output_dir/"02_top_estados.png",dpi=150)

        plt.close()

    # -------------------------------------------------------

    def grafico_regioes(self):

        dados=(

            self.df

            .groupby("regiao")["numero_queimadas"]

            .sum()

        )

        plt.figure(figsize=(8,8))

        plt.pie(

            dados,

            labels=dados.index,

            autopct="%1.1f%%"

        )

        plt.title("Distribuição por Região")

        plt.savefig(self.output_dir/"03_regioes.png",dpi=150)

        plt.close()

    # -------------------------------------------------------

    def grafico_meses(self):

        dados=(

            self.df

            .groupby("mes")["numero_queimadas"]

            .sum()

        )

        plt.figure(figsize=(12,6))

        dados.plot(kind="bar")

        plt.title("Queimadas por Mês")

        plt.ylabel("Número de Queimadas")

        plt.tight_layout()

        plt.savefig(self.output_dir/"04_meses.png",dpi=150)

        plt.close()

    # -------------------------------------------------------

    def heatmap(self):

        tabela=(

            self.df.pivot_table(

                values="numero_queimadas",

                index="ano",

                columns="mes",

                aggfunc="sum"

            )

        )

        plt.figure(figsize=(12,8))

        plt.imshow(

            tabela,

            aspect="auto"

        )

        plt.colorbar(label="Número de Queimadas")

        plt.xticks(

            range(len(tabela.columns)),

            tabela.columns,

            rotation=45

        )

        plt.yticks(

            range(len(tabela.index)),

            tabela.index

        )

        plt.title("Heatmap Ano x Mês")

        plt.tight_layout()

        plt.savefig(self.output_dir/"05_heatmap.png",dpi=150)

        plt.close()

    # -------------------------------------------------------

    def gerar_todos(self):

        logger.info("Gerando gráficos...")

        self.grafico_anual()

        self.grafico_estados()

        self.grafico_regioes()

        self.grafico_meses()

        self.heatmap()

        logger.info("Todos os gráficos foram gerados com sucesso.")