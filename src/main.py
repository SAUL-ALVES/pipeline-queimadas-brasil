"""
main.py

Orquestrador principal do pipeline de Ciência de Dados.

Fluxo:

1 - Extração
2 - Limpeza
3 - EDA
4 - Relatório
5 - Exportação
6 - Visualizações
7 - Inferência estatística (bootstrap e teste A/B)
8 - Aprendizado Não Supervisionado (K-Means e PCA)

Pendente para os colegas (Parte 2):
- 4.3 regressão múltipla e classificação (src/models/)
- 4.5 discussão causal complementar no README (Adicionado)

Execução:

python src/main.py
"""

from __future__ import annotations

import logging
import sys
import time
from pathlib import Path

import pandas as pd

SRC_DIR = Path(__file__).resolve().parent
ROOT_DIR = SRC_DIR.parent

for path in (str(ROOT_DIR), str(SRC_DIR)):
    if path not in sys.path:
        sys.path.insert(0, path)

# ================================
# Config
# ================================

from config import (
    RAW_DIR,
    OUTPUT_CSV,
    GRAPH_DIR,
    REPORT_DIR,
    REPORT_FILE,
    STATISTICS_FILE,
    BOOTSTRAP_PLOT,
    PERMUTACAO_PLOT,
)

# ================================
# Pipeline
# ================================

from extract.extractor import extrair_dados
from transform.cleaner import limpar_dados

# ================================
# Análises
# ================================

from analysis.eda import EDA
from analysis.report import Report

# Se existir validator.py descomente
#
# from analysis.validator import Validator

# ================================
# Modelos (Parte 2)
# ================================

from models.unsupervised import run_unsupervised_analysis

# ================================
# Visualizações e Inferência
# ================================

from visualize import Visualizer
from inference.bootstrap import executar_bootstrap
from inference.ab_testing import executar_teste_ab

# ================================
# Logs
# ================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
)

logger = logging.getLogger("pipeline")


# =========================================================


def executar_pipeline():

    inicio = time.perf_counter()

    logger.info("=" * 70)
    logger.info("PIPELINE DE DADOS - QUEIMADAS NO BRASIL")
    logger.info("=" * 70)

    # ------------------------------------------------------
    # EXTRAÇÃO
    # ------------------------------------------------------

    logger.info("[1/8] Extraindo dados...")

    df_bruto = extrair_dados(RAW_DIR)

    logger.info(
        "Dataset bruto: %d linhas x %d colunas",
        *df_bruto.shape,
    )

    # ------------------------------------------------------
    # LIMPEZA
    # ------------------------------------------------------

    logger.info("[2/8] Limpando dados...")

    df = limpar_dados(df_bruto)

    logger.info(
        "Dataset tratado: %d linhas x %d colunas",
        *df.shape,
    )

    # ------------------------------------------------------
    # VALIDAÇÃO (opcional)
    # ------------------------------------------------------

    """
    validator = Validator(df)

    validator.validar()
    """

    # ------------------------------------------------------
    # EDA
    # ------------------------------------------------------

    logger.info("[3/8] Executando EDA...")

    eda = EDA(df, REPORT_DIR)

    if hasattr(eda, "imprimir"):
        eda.imprimir()

    if hasattr(eda, "imprimir_resumo"):
        eda.imprimir_resumo()

    if hasattr(eda, "estatisticas"):
        eda.estatisticas()

    # ------------------------------------------------------
    # EXPORTAÇÃO
    # ------------------------------------------------------

    logger.info("[4/8] Exportando CSV tratado...")

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    df.to_csv(
        OUTPUT_CSV,
        index=False,
        encoding="utf-8",
    )

    logger.info("Arquivo salvo em: %s", OUTPUT_CSV)

    # ------------------------------------------------------
    # RELATÓRIO
    # ------------------------------------------------------

    logger.info("[5/8] Gerando relatório...")

    report = Report(
        df,
        REPORT_FILE,
    )

    report.gerar()

    logger.info("Relatório salvo em: %s", REPORT_FILE)

    # ------------------------------------------------------
    # GRÁFICOS
    # ------------------------------------------------------

    logger.info("[6/8] Gerando gráficos...")

    visual = Visualizer(
        df,
        GRAPH_DIR,
    )

    visual.gerar_todos()

    logger.info("Gráficos gerados em: %s", GRAPH_DIR)

    # ------------------------------------------------------
    # INFERÊNCIA ESTATÍSTICA (Parte 2 — recorte 1/3 do trio)
    # ------------------------------------------------------

    logger.info("[7/8] Inferência estatística (bootstrap e teste A/B)...")

    df_limpo = pd.read_csv(OUTPUT_CSV)

    resultado_boot = executar_bootstrap(df_limpo)
    visual.grafico_bootstrap(
        resultado_boot["medias_bootstrap"],
        resultado_boot["parametros"]["media"],
        resultado_boot["ic_bootstrap"],
        resultado_boot["ic_parametrico"],
        BOOTSTRAP_PLOT,
    )

    resultado_ab = executar_teste_ab(df_limpo)
    visual.grafico_permutacao(
        resultado_ab["estatisticas_nulas"],
        resultado_ab["estatistica_observada"],
        PERMUTACAO_PLOT,
    )

    logger.info("Gráfico bootstrap : %s", BOOTSTRAP_PLOT)
    logger.info("Gráfico permutação: %s", PERMUTACAO_PLOT)

    # ------------------------------------------------------
    # APRENDIZADO NÃO SUPERVISIONADO (K-Means e PCA)
    # ------------------------------------------------------

    logger.info("[8/8] Executando Análise Não Supervisionada...")

    # Seleciona automaticamente variáveis numéricas e remove potenciais variáveis de controle/ID
    features_cluster = df_limpo.select_dtypes(include=['float64', 'int64']).columns.tolist()
    colunas_ignorar = ['numero_queimadas_outlier_iqr', 'ano']
    features_cluster = [f for f in features_cluster if f not in colunas_ignorar]

    try:
        clusters = run_unsupervised_analysis(df_limpo, features_cluster, GRAPH_DIR)
        logger.info("Gráficos de cluster gerados com sucesso em: %s", GRAPH_DIR)
    except Exception as e:
        logger.error("Erro ao executar análise não supervisionada: %s", e)

    # ------------------------------------------------------

    tempo = time.perf_counter() - inicio

    logger.info("=" * 70)
    logger.info("PIPELINE EXECUTADO COM SUCESSO")
    logger.info("=" * 70)

    logger.info("Tempo total : %.2f segundos", tempo)
    logger.info("Linhas      : %d", len(df))
    logger.info("Colunas     : %d", len(df.columns))
    logger.info("Estados     : %d", df["estado"].nunique())
    logger.info("Regiões     : %d", df["regiao"].nunique())

    if "numero_queimadas_outlier_iqr" in df.columns:

        logger.info(
            "Outliers IQR: %d",
            int(df["numero_queimadas_outlier_iqr"].sum()),
        )

    logger.info("=" * 70)


# =========================================================


def main():

    try:

        executar_pipeline()

        return 0

    except FileNotFoundError as erro:

        logger.error("Arquivo não encontrado.")

        logger.error(str(erro))

        return 1

    except KeyboardInterrupt:

        logger.warning("Execução interrompida.")

        return 2

    except Exception:

        logger.exception("Erro inesperado.")

        return 1


# =========================================================

if __name__ == "__main__":

    raise SystemExit(main())