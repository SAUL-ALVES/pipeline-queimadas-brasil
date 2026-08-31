"""
regression.py

Regressão Linear Múltipla para estimar o número de queimadas a partir de
variáveis temporais e geográficas do dataset limpo.

Atende à seção 4.3 da Avaliação Prática Unificada (Parte 2):

1. separação treino/teste reprodutível;
2. preparação de variáveis numéricas e categóricas;
3. ajuste de uma Regressão Linear Múltipla;
4. avaliação por R², MAE e RMSE;
5. relatório automático com os coeficientes de maior magnitude.

A variável tratada por IQR é usada como alvo quando disponível. Isso preserva
o procedimento adotado na Parte 1 e reduz a influência de observações extremas
sem apagar registros do dataset.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

SRC_DIR = Path(__file__).resolve().parent.parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from config import OUTPUT_CSV, RANDOM_SEED, REPORT_DIR

logger = logging.getLogger("pipeline.models.regression")

FEATURES_NUMERICAS = ("ano", "mes_numero")
FEATURES_CATEGORICAS = ("estado",)
ALVO_PREFERENCIAL = "numero_queimadas_tratado_iqr"
ALVO_FALLBACK = "numero_queimadas"
TEST_SIZE = 0.20
REGRESSION_REPORT = REPORT_DIR / "regressao_multipla.txt"


def _validar_colunas(df: pd.DataFrame, colunas: list[str]) -> None:
    ausentes = [coluna for coluna in colunas if coluna not in df.columns]
    if ausentes:
        raise KeyError(f"Colunas ausentes no dataset limpo: {', '.join(ausentes)}")


def _escolher_alvo(df: pd.DataFrame) -> str:
    if ALVO_PREFERENCIAL in df.columns:
        return ALVO_PREFERENCIAL
    if ALVO_FALLBACK in df.columns:
        return ALVO_FALLBACK
    raise KeyError(
        "Nenhuma coluna de queimadas disponível para regressão: "
        f"'{ALVO_PREFERENCIAL}' ou '{ALVO_FALLBACK}'."
    )


def construir_pipeline_regressao() -> Pipeline:
    """Cria o pré-processamento e a Regressão Linear Múltipla."""
    preprocessador = ColumnTransformer(
        transformers=[
            ("numericas", StandardScaler(), list(FEATURES_NUMERICAS)),
            (
                "categoricas",
                OneHotEncoder(
                    handle_unknown="ignore",
                    drop="first",
                    sparse_output=False,
                ),
                list(FEATURES_CATEGORICAS),
            ),
        ],
        remainder="drop",
    )

    return Pipeline(
        steps=[
            ("preprocessador", preprocessador),
            ("modelo", LinearRegression()),
        ]
    )


def _extrair_coeficientes(pipeline: Pipeline) -> pd.DataFrame:
    preprocessador = pipeline.named_steps["preprocessador"]
    modelo = pipeline.named_steps["modelo"]
    nomes = preprocessador.get_feature_names_out()

    coeficientes = pd.DataFrame(
        {
            "variavel": nomes,
            "coeficiente": modelo.coef_.astype(float),
        }
    )
    coeficientes["magnitude"] = coeficientes["coeficiente"].abs()
    return coeficientes.sort_values("magnitude", ascending=False).reset_index(drop=True)


def _formatar_relatorio(resultado: dict) -> str:
    metricas = resultado["metricas"]
    maiores = resultado["coeficientes"].head(12)

    linhas = [
        "=" * 68,
        "SEÇÃO 4.3 — REGRESSÃO LINEAR MÚLTIPLA",
        "=" * 68,
        f"Alvo..........................: {resultado['alvo']}",
        f"Preditores....................: {', '.join(resultado['features'])}",
        f"Treino / teste................: {resultado['n_treino']:,} / {resultado['n_teste']:,}",
        f"Semente aleatória.............: {resultado['seed']}",
        "",
        "Métricas no conjunto de teste",
        f"  R²..........................: {metricas['r2']:.4f}",
        f"  MAE.........................: {metricas['mae']:.4f}",
        f"  RMSE........................: {metricas['rmse']:.4f}",
        f"  Intercepto..................: {resultado['intercepto']:.4f}",
        "",
        "Coeficientes de maior magnitude (variáveis já transformadas)",
    ]

    for _, linha in maiores.iterrows():
        linhas.append(f"  {linha['variavel']:<42} {linha['coeficiente']:>11.4f}")

    linhas.extend(
        [
            "",
            "Interpretação:",
            "  O R² mede a parcela da variabilidade do alvo explicada pelo modelo.",
            "  MAE e RMSE medem erro de previsão; quanto menores, melhor.",
            "  O modelo é associativo/preditivo e não estabelece causalidade.",
            "=" * 68,
        ]
    )
    return "\n".join(linhas) + "\n"


def executar_regressao(
    df: pd.DataFrame,
    seed: int = RANDOM_SEED,
    test_size: float = TEST_SIZE,
    relatorio_path: Path | None = REGRESSION_REPORT,
) -> dict:
    """Treina e avalia a Regressão Linear Múltipla da seção 4.3."""
    alvo = _escolher_alvo(df)
    features = list(FEATURES_NUMERICAS + FEATURES_CATEGORICAS)
    _validar_colunas(df, features + [alvo])

    dados = df[features + [alvo]].dropna().copy()
    if dados.empty:
        raise ValueError("Não há observações completas para treinar a regressão.")

    X = dados[features]
    y = dados[alvo].astype(float)

    X_treino, X_teste, y_treino, y_teste = train_test_split(
        X,
        y,
        test_size=test_size,
        random_state=seed,
    )

    pipeline = construir_pipeline_regressao()
    pipeline.fit(X_treino, y_treino)
    previsoes = pipeline.predict(X_teste)

    metricas = {
        "r2": float(r2_score(y_teste, previsoes)),
        "mae": float(mean_absolute_error(y_teste, previsoes)),
        "rmse": float(np.sqrt(mean_squared_error(y_teste, previsoes))),
    }
    coeficientes = _extrair_coeficientes(pipeline)
    intercepto = float(pipeline.named_steps["modelo"].intercept_)

    resultado = {
        "alvo": alvo,
        "features": features,
        "seed": seed,
        "test_size": test_size,
        "n_total": int(len(dados)),
        "n_treino": int(len(X_treino)),
        "n_teste": int(len(X_teste)),
        "metricas": metricas,
        "coeficientes": coeficientes,
        "intercepto": intercepto,
        "modelo": pipeline,
        "y_teste": y_teste.to_numpy(dtype=float),
        "previsoes": np.asarray(previsoes, dtype=float),
    }

    texto = _formatar_relatorio(resultado)
    logger.info("\n%s", texto.rstrip())

    if relatorio_path is not None:
        relatorio_path.parent.mkdir(parents=True, exist_ok=True)
        relatorio_path.write_text(texto, encoding="utf-8")
        logger.info("Relatório de regressão salvo em: %s", relatorio_path)

    return resultado


def main() -> int:
    """Permite executar apenas a regressão a partir do CSV limpo."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%H:%M:%S",
    )

    if not OUTPUT_CSV.exists():
        logger.error("Dataset limpo não encontrado: %s", OUTPUT_CSV)
        return 1

    df = pd.read_csv(OUTPUT_CSV)
    executar_regressao(df)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
