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
✔ Distribuição bootstrap da média (Parte 2)
✔ Distribuição de permutação do teste A/B (Parte 2)
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

    def grafico_bootstrap(
        self,
        medias,
        media_obs,
        ic_bootstrap,
        ic_parametrico,
        destino,
    ):
        """
        Histograma das médias bootstrap com os limites dos dois ICs de 95%.

        Arquivo exigido pelo enunciado: distribuicao_bootstrap.png
        """
        destino = Path(destino)
        destino.parent.mkdir(parents=True, exist_ok=True)

        plt.figure(figsize=(12, 6))
        plt.hist(medias, bins=40, color="#4C78A8", edgecolor="white", alpha=0.9)

        plt.axvline(
            media_obs,
            color="black",
            linestyle="-",
            linewidth=2,
            label=f"Média amostral = {media_obs:.2f}",
        )
        plt.axvline(
            ic_bootstrap[0],
            color="#E45756",
            linestyle="--",
            linewidth=2,
            label=f"IC bootstrap 2,5% = {ic_bootstrap[0]:.2f}",
        )
        plt.axvline(
            ic_bootstrap[1],
            color="#E45756",
            linestyle="--",
            linewidth=2,
            label=f"IC bootstrap 97,5% = {ic_bootstrap[1]:.2f}",
        )
        plt.axvline(
            ic_parametrico[0],
            color="#54A24B",
            linestyle=":",
            linewidth=2.5,
            label=f"IC paramétrico inf. = {ic_parametrico[0]:.2f}",
        )
        plt.axvline(
            ic_parametrico[1],
            color="#54A24B",
            linestyle=":",
            linewidth=2.5,
            label=f"IC paramétrico sup. = {ic_parametrico[1]:.2f}",
        )

        plt.title("Distribuição Bootstrap da Média de Queimadas")
        plt.xlabel("Média bootstrap do número de queimadas")
        plt.ylabel("Frequência das réplicas")
        plt.legend(frameon=False)
        plt.grid(True, axis="y", alpha=0.3)
        plt.tight_layout()
        plt.savefig(destino, dpi=150)
        plt.close()

        logger.info("Gráfico bootstrap salvo em: %s", destino)

    # -------------------------------------------------------

    def grafico_permutacao(
        self,
        estatisticas_nulas,
        estatistica_observada,
        destino,
    ):
        """
        Histograma da estatística sob H0, com a diferença observada destacada.

        Arquivo exigido pelo enunciado: distribuicao_permutacao.png
        """
        destino = Path(destino)
        destino.parent.mkdir(parents=True, exist_ok=True)

        plt.figure(figsize=(12, 6))
        plt.hist(
            estatisticas_nulas,
            bins=40,
            color="#9D755D",
            edgecolor="white",
            alpha=0.9,
        )
        plt.axvline(
            estatistica_observada,
            color="#E45756",
            linestyle="-",
            linewidth=2.5,
            label=f"Diferença observada = {estatistica_observada:.2f}",
        )
        plt.axvline(
            -abs(estatistica_observada),
            color="#E45756",
            linestyle=":",
            linewidth=1.8,
            label="Limite simétrico (teste bicaudal)",
        )

        plt.title("Distribuição da Diferença de Médias sob H0 (Permutação)")
        plt.xlabel("X̄ seco − X̄ chuvoso (sob H0)")
        plt.ylabel("Frequência das permutações")
        plt.legend(frameon=False)
        plt.grid(True, axis="y", alpha=0.3)
        plt.tight_layout()
        plt.savefig(destino, dpi=150)
        plt.close()

        logger.info("Gráfico de permutação salvo em: %s", destino)

    # -------------------------------------------------------

    def gerar_todos(self):

        logger.info("Gerando gráficos...")

        self.grafico_anual()

        self.grafico_estados()

        self.grafico_regioes()

        self.grafico_meses()

        self.heatmap()

        logger.info("Todos os gráficos foram gerados com sucesso.")