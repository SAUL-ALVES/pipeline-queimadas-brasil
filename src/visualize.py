"""
visualize.py - Visualizacao Cientifica (Integridade Visual).

Gera, de forma automatizada, UM grafico a partir da base ja tratada pelo
pipeline. Vale 20% da avaliacao. Escolha UMA das opcoes:

    - Evolucao temporal da metrica principal .... Grafico de LINHAS
    - Distribuicao proporcional de qualitativos . Grafico de BARRAS
    - Relacao entre duas variaveis numericas .... Grafico de DISPERSAO

Checklist OBRIGATORIO de integridade visual (honestidade estatistica):
    [ ] Titulo claro e descritivo
    [ ] Eixos identificados (label) com UNIDADE de medida explicita
    [ ] Escala proporcional e coerente; eixo numerico iniciando em ZERO
        onde for aplicavel (ex.: contagens, barras)
    [ ] Ausencia de distorcoes visuais (sem eixos truncados enganosos)
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
    """Gera e salva o grafico principal do projeto.

    TODO (equipe):
      - Escolher UM tipo de grafico (linhas / barras / dispersao).
      - Agregar os dados conforme necessario (ex.: total de queimadas por ano).
      - Aplicar TODO o checklist de integridade visual do docstring acima.
      - Salvar em `caminho_saida` (PNG) com fig.savefig(..., dpi=150,
        bbox_inches="tight").

    Esqueleto de exemplo (descomente e adapte ao seu recorte de dados):

        fig, ax = plt.subplots(figsize=(10, 6))
        # ... plotagem aqui ...
        ax.set_title("Titulo descritivo")
        ax.set_xlabel("Eixo X (unidade)")
        ax.set_ylabel("Eixo Y (unidade)")
        ax.set_ylim(bottom=0)  # eixo iniciando em zero onde aplicavel
        fig.savefig(caminho_saida, dpi=150, bbox_inches="tight")
        plt.close(fig)
    """
    logger.warning("gerar_grafico() ainda nao implementada (TODO).")
