"""
main.py - Orquestrador central do pipeline de dados de queimadas no Brasil.

Disciplina: Ciencia de Dados | Avaliacao Pratica Unificada (Parte 1)
Tema (Opcao C): Meio Ambiente (Queimadas)
Equipe: Saul, Edilson, Luiz Vitor

Fluxo do pipeline (reprodutivel):
    1. INGESTAO   (extract/extractor.py)  -> le os CSVs brutos do Kaggle
    2. TRANSFORM  (transform/cleaner.py)  -> sanitiza, trata nulos, isola
                                              outliers via IQR e consolida (merge)
    3. EXPORTACAO                         -> grava dados_limpos_final.csv na raiz
    4. VISUALIZACAO (visualize.py)        -> gera grafico com integridade visual

Uso (a partir da RAIZ do projeto):
    python src/main.py
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

# Garante que a pasta `src/` esteja no path para os imports dos pacotes,
# independentemente de onde o script seja chamado.
SRC_DIR = Path(__file__).resolve().parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from extract.extractor import extrair_dados          # noqa: E402
from transform.cleaner import limpar_dados            # noqa: E402
from visualize import gerar_grafico                   # noqa: E402

# ---------------------------------------------------------------------------
# Caminhos base do projeto (resolvidos a partir deste arquivo)
# ---------------------------------------------------------------------------
ROOT_DIR = SRC_DIR.parent
DATA_RAW_DIR = ROOT_DIR / "data" / "raw"
OUTPUT_CSV = ROOT_DIR / "dados_limpos_final.csv"
OUTPUT_GRAFICO = ROOT_DIR / "outputs" / "grafico_principal.png"

# ---------------------------------------------------------------------------
# Configuracao de log simples (exigido na camada de ingestao)
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("pipeline")


def executar_pipeline() -> None:
    """Executa as etapas do pipeline em ordem, com log por etapa."""
    logger.info("=" * 60)
    logger.info("PIPELINE DE QUEIMADAS NO BRASIL - INICIO")
    logger.info("=" * 60)

    # 1. INGESTAO ----------------------------------------------------------
    logger.info("[1/4] Ingestao: lendo dados brutos de %s", DATA_RAW_DIR)
    df_bruto = extrair_dados(DATA_RAW_DIR)
    logger.info("[1/4] Volumetria bruta: %d linhas x %d colunas", *df_bruto.shape)

    # 2. TRANSFORMACAO -----------------------------------------------------
    logger.info("[2/4] Transformacao: sanitizacao, nulos, IQR e merge")
    df_limpo = limpar_dados(df_bruto)
    logger.info("[2/4] Volumetria final: %d linhas x %d colunas", *df_limpo.shape)

    # 3. EXPORTACAO --------------------------------------------------------
    logger.info("[3/4] Exportacao: gravando %s", OUTPUT_CSV.name)
    df_limpo.to_csv(OUTPUT_CSV, index=False, encoding="utf-8")

    # 4. VISUALIZACAO ------------------------------------------------------
    logger.info("[4/4] Visualizacao: gerando grafico principal")
    OUTPUT_GRAFICO.parent.mkdir(parents=True, exist_ok=True)
    gerar_grafico(df_limpo, OUTPUT_GRAFICO)

    logger.info("=" * 60)
    logger.info("PIPELINE CONCLUIDO COM SUCESSO")
    logger.info("Base consolidada : %s", OUTPUT_CSV)
    logger.info("Grafico gerado   : %s", OUTPUT_GRAFICO)
    logger.info("=" * 60)


def main() -> int:
    """Ponto de entrada. Retorna codigo de saida (0 = sucesso)."""
    try:
        executar_pipeline()
        return 0
    except FileNotFoundError as exc:
        logger.error("Arquivo nao encontrado: %s", exc)
        logger.error("Confira se o CSV bruto esta em data/raw/ (veja o README).")
        return 1
    except NotImplementedError as exc:
        logger.warning("Etapa ainda nao implementada: %s", exc)
        return 2
    except Exception as exc:  # noqa: BLE001 - log de qualquer falha inesperada
        logger.exception("Falha inesperada no pipeline: %s", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
