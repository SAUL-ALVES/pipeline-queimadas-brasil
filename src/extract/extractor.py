"""
extractor.py - Camada de Ingestao (Amostragem e Vies).

Responsavel por capturar e ler os dados BRUTOS (.csv) do Kaggle, isolando
falhas de caminho de arquivo e registrando a volumetria inicial (log).

NAO faz limpeza/transformacao aqui - apenas leitura fiel do dado original.
A sanitizacao e responsabilidade de transform/cleaner.py.
"""
from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger("pipeline.extract")


ENCODINGS_TENTATIVOS = ("utf-8", "latin-1", "ISO-8859-1")


def _ler_csv(caminho: Path) -> pd.DataFrame:
    """Le um unico CSV testando uma lista de encodings ate ter sucesso."""
    ultimo_erro: Exception | None = None
    for enc in ENCODINGS_TENTATIVOS:
        try:
            df = pd.read_csv(caminho, encoding=enc)
            logger.info("Lido '%s' (encoding=%s): %d x %d",
                        caminho.name, enc, df.shape[0], df.shape[1])
            return df
        except UnicodeDecodeError as exc:
            ultimo_erro = exc
            logger.debug("Encoding %s falhou em %s; tentando proximo", enc, caminho.name)
    # Se nenhum encoding funcionou, propaga o ultimo erro
    raise UnicodeDecodeError(  # type: ignore[misc]
        "utf-8", b"", 0, 1,
        f"Nao foi possivel decodificar {caminho.name}: {ultimo_erro}",
    )


def extrair_dados(diretorio_raw: Path) -> pd.DataFrame:
    """Le todos os CSVs do diretorio de dados brutos e retorna um DataFrame.

    Parametros
    ----------
    diretorio_raw : Path
        Pasta onde estao os arquivos .csv originais (data/raw/).

    Retorna
    -------
    pd.DataFrame
        Dados brutos concatenados, sem nenhuma transformacao.

    Levanta
    -------
    FileNotFoundError
        Se a pasta nao existir ou nao houver nenhum .csv dentro dela.
    """
    diretorio_raw = Path(diretorio_raw)

    if not diretorio_raw.exists():
        raise FileNotFoundError(f"Diretorio de dados brutos inexistente: {diretorio_raw}")

    arquivos_csv = sorted(diretorio_raw.glob("*.csv"))
    if not arquivos_csv:
        raise FileNotFoundError(
            f"Nenhum .csv encontrado em {diretorio_raw}. "
            "Baixe o dataset do Kaggle (veja data/raw/COLOQUE_O_CSV_AQUI.md)."
        )

    logger.info("Encontrado(s) %d arquivo(s) CSV para ingestao", len(arquivos_csv))

    dataframes = [_ler_csv(arq) for arq in arquivos_csv]
    df_bruto = pd.concat(dataframes, ignore_index=True) if len(dataframes) > 1 else dataframes[0]

    logger.info("Volumetria bruta consolidada: %d linhas x %d colunas", *df_bruto.shape)
    return df_bruto
