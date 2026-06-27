"""
validator.py

Valida automaticamente o DataFrame antes da análise.
"""

import logging

logger = logging.getLogger("pipeline.validator")


def validar_dataset(df):

    logger.info("Iniciando validação do dataset...")

    obrigatorias = [
        "ano",
        "estado",
        "mes",
        "regiao",
        "numero_queimadas",
    ]

    faltando = []

    for coluna in obrigatorias:

        if coluna not in df.columns:

            faltando.append(coluna)

    if faltando:

        raise ValueError(
            f"Colunas obrigatórias ausentes: {faltando}"
        )

    if (df["numero_queimadas"] < 0).any():

        raise ValueError(
            "Existem valores negativos."
        )

    if (df["mes_numero"] < 1).any() or (df["mes_numero"] > 12).any():

        raise ValueError(
            "Existem meses inválidos."
        )

    logger.info("Validação concluída com sucesso.")

    return True