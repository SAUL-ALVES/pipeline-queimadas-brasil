"""
visualize.py - Visualizacao Cientifica (Integridade Visual).

Gera automaticamente um grafico de linhas com a evolucao anual do numero de
queimadas. O grafico usa a coluna tratada por IQR quando ela existir, mantendo
o eixo Y iniciado em zero por se tratar de uma contagem/agregacao.
"""
from __future__ import annotations

import logging
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # backend sem janela: salva o grafico em arquivo
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

logger = logging.getLogger("pipeline.visualize")


def gerar_grafico(df: pd.DataFrame, caminho_saida: Path) -> None:
    """Gera e salva grafico de evolucao temporal das queimadas por ano.

    Criterios de integridade visual aplicados:
      - titulo e eixos claros;
      - unidade explicita no eixo Y;
      - eixo Y iniciado em zero;
      - escala proporcional, sem truncamento enganoso.
    """
    if "ano" not in df.columns:
        raise ValueError("A coluna 'ano' e obrigatoria para gerar o grafico temporal.")

    coluna_metrica = (
        "numero_queimadas_tratado_iqr"
        if "numero_queimadas_tratado_iqr" in df.columns
        else "numero_queimadas"
    )
    if coluna_metrica not in df.columns:
        raise ValueError("Nao ha coluna numerica de queimadas para visualizacao.")

    serie_anual = (
        df.groupby("ano", as_index=False)[coluna_metrica]
        .sum()
        .sort_values("ano")
        .rename(columns={coluna_metrica: "total_queimadas"})
    )

    if serie_anual.empty:
        raise ValueError("Nao ha dados suficientes para gerar o grafico.")

    caminho_saida = Path(caminho_saida)
    caminho_saida.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(11, 6))
    ax.plot(serie_anual["ano"], serie_anual["total_queimadas"], marker="o")

    ax.set_title("Evolucao anual de queimadas registradas no Brasil")
    ax.set_xlabel("Ano")
    ax.set_ylabel("Total de queimadas registradas (contagem)")
    ax.set_ylim(bottom=0)
    ax.grid(True, axis="y", alpha=0.3)

    anos = serie_anual["ano"].astype(int).tolist()
    ax.set_xticks(anos)
    ax.tick_params(axis="x", rotation=45)

    fig.tight_layout()
    fig.savefig(caminho_saida, dpi=150, bbox_inches="tight")
    plt.close(fig)

    logger.info("Grafico salvo em: %s", caminho_saida)
