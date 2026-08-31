"""
machine_learning.py

Classificação supervisionada da seção 4.3 usando:

- Regressão Logística como baseline;
- K-Nearest Neighbors (KNN);
- GridSearchCV com validação cruzada estratificada para otimizar o KNN.

O alvo binário é definido sem usar nenhuma variável futura como preditora:
1 = número de queimadas acima da mediana da amostra;
0 = número de queimadas igual ou abaixo da mediana.

Os preditores são apenas ano, mês, estado e região. A própria contagem de
queimadas (ou sua versão tratada) nunca entra em X, evitando data leakage.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import GridSearchCV, StratifiedKFold, train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

SRC_DIR = Path(__file__).resolve().parent.parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from config import OUTPUT_CSV, RANDOM_SEED, REPORT_DIR

logger = logging.getLogger("pipeline.models.machine_learning")

FEATURES_NUMERICAS = ("ano", "mes_numero")
FEATURES_CATEGORICAS = ("estado",)
COLUNA_BASE_ALVO = "numero_queimadas"
TEST_SIZE = 0.20
CV_FOLDS = 5
CLASSIFICATION_REPORT = REPORT_DIR / "classificacao_ml.txt"

GRADE_KNN = {
    "modelo__n_neighbors": [3, 5, 7, 9, 11, 15, 21],
    "modelo__weights": ["uniform", "distance"],
    "modelo__p": [1, 2],
}


def _validar_colunas(df: pd.DataFrame, colunas: list[str]) -> None:
    ausentes = [coluna for coluna in colunas if coluna not in df.columns]
    if ausentes:
        raise KeyError(f"Colunas ausentes no dataset limpo: {', '.join(ausentes)}")


def _construir_preprocessador() -> ColumnTransformer:
    return ColumnTransformer(
        transformers=[
            ("numericas", StandardScaler(), list(FEATURES_NUMERICAS)),
            (
                "categoricas",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                list(FEATURES_CATEGORICAS),
            ),
        ],
        remainder="drop",
    )


def construir_pipeline_logistica(seed: int = RANDOM_SEED) -> Pipeline:
    return Pipeline(
        steps=[
            ("preprocessador", _construir_preprocessador()),
            (
                "modelo",
                LogisticRegression(
                    max_iter=2000,
                    random_state=seed,
                ),
            ),
        ]
    )


def construir_pipeline_knn() -> Pipeline:
    return Pipeline(
        steps=[
            ("preprocessador", _construir_preprocessador()),
            ("modelo", KNeighborsClassifier()),
        ]
    )


def criar_alvo_classificacao(df: pd.DataFrame) -> tuple[pd.Series, float]:
    """Cria 1 para ocorrência acima da mediana e 0 caso contrário."""
    if COLUNA_BASE_ALVO not in df.columns:
        raise KeyError(f"Coluna '{COLUNA_BASE_ALVO}' não encontrada no dataset limpo.")

    valores = pd.to_numeric(df[COLUNA_BASE_ALVO], errors="coerce")
    limiar = float(valores.median())
    alvo = (valores > limiar).astype(int)
    return alvo, limiar


def _calcular_metricas(modelo: Pipeline, X: pd.DataFrame, y: pd.Series) -> dict:
    predicoes = modelo.predict(X)
    probabilidades = modelo.predict_proba(X)[:, 1]
    matriz = confusion_matrix(y, predicoes, labels=[0, 1])

    return {
        "accuracy": float(accuracy_score(y, predicoes)),
        "precision": float(precision_score(y, predicoes, zero_division=0)),
        "recall": float(recall_score(y, predicoes, zero_division=0)),
        "f1": float(f1_score(y, predicoes, zero_division=0)),
        "roc_auc": float(roc_auc_score(y, probabilidades)),
        "confusion_matrix": matriz.astype(int),
    }


def _formatar_metricas(nome: str, metricas: dict) -> list[str]:
    matriz = metricas["confusion_matrix"]
    return [
        nome,
        f"  Accuracy....................: {metricas['accuracy']:.4f}",
        f"  Precision...................: {metricas['precision']:.4f}",
        f"  Recall......................: {metricas['recall']:.4f}",
        f"  F1-score....................: {metricas['f1']:.4f}",
        f"  ROC-AUC.....................: {metricas['roc_auc']:.4f}",
        "  Matriz de confusão [0, 1]..:",
        f"    [[TN={matriz[0, 0]:4d}, FP={matriz[0, 1]:4d}],",
        f"     [FN={matriz[1, 0]:4d}, TP={matriz[1, 1]:4d}]]",
    ]


def _formatar_relatorio(resultado: dict) -> str:
    linhas = [
        "=" * 72,
        "SEÇÃO 4.3 — CLASSIFICAÇÃO: LOGÍSTICA + KNN + GRIDSEARCHCV",
        "=" * 72,
        f"Alvo..........................: {resultado['descricao_alvo']}",
        f"Limiar (mediana)..............: {resultado['limiar']:.4f}",
        f"Preditores....................: {', '.join(resultado['features'])}",
        f"Treino / teste................: {resultado['n_treino']:,} / {resultado['n_teste']:,}",
        f"Classe 0 / Classe 1...........: {resultado['classe_0']:,} / {resultado['classe_1']:,}",
        f"Semente aleatória.............: {resultado['seed']}",
        f"Validação cruzada do Grid.....: {resultado['cv_folds']} folds estratificados",
        f"Métrica otimizada no Grid.....: F1-score",
        "",
    ]

    linhas.extend(_formatar_metricas("Regressão Logística (baseline)", resultado["logistica"]))
    linhas.append("")
    linhas.append("KNN otimizado por GridSearchCV")
    linhas.append(f"  Melhor F1 médio (CV)........: {resultado['knn_cv_best_score']:.4f}")
    linhas.append(f"  Melhores hiperparâmetros....: {resultado['knn_best_params']}")
    linhas.extend(_formatar_metricas("  Desempenho no teste", resultado["knn"]))

    melhor = resultado["melhor_modelo"]
    linhas.extend(
        [
            "",
            f"Modelo com maior F1 no teste..: {melhor}",
            "",
            "Observação metodológica:",
            "  O conjunto de teste é separado antes da otimização. O GridSearchCV",
            "  usa somente os dados de treino, reduzindo risco de ajuste ao teste.",
            "  A contagem de queimadas não é usada como feature, evitando leakage.",
            "  Os resultados são preditivos/associativos, não causais.",
            "=" * 72,
        ]
    )
    return "\n".join(linhas) + "\n"


def executar_classificacao(
    df: pd.DataFrame,
    seed: int = RANDOM_SEED,
    test_size: float = TEST_SIZE,
    cv_folds: int = CV_FOLDS,
    relatorio_path: Path | None = CLASSIFICATION_REPORT,
) -> dict:
    """Treina Logística e KNN otimizado por GridSearchCV e compara resultados."""
    features = list(FEATURES_NUMERICAS + FEATURES_CATEGORICAS)
    _validar_colunas(df, features + [COLUNA_BASE_ALVO])

    dados = df[features + [COLUNA_BASE_ALVO]].dropna().copy()
    if dados.empty:
        raise ValueError("Não há observações completas para a classificação.")

    y, limiar = criar_alvo_classificacao(dados)
    X = dados[features]

    if y.nunique() != 2:
        raise ValueError("O alvo de classificação não possui exatamente duas classes.")

    X_treino, X_teste, y_treino, y_teste = train_test_split(
        X,
        y,
        test_size=test_size,
        random_state=seed,
        stratify=y,
    )

    logistica = construir_pipeline_logistica(seed=seed)
    logistica.fit(X_treino, y_treino)
    metricas_logistica = _calcular_metricas(logistica, X_teste, y_teste)

    cv = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=seed)
    busca_knn = GridSearchCV(
        estimator=construir_pipeline_knn(),
        param_grid=GRADE_KNN,
        scoring="f1",
        cv=cv,
        n_jobs=-1,
        refit=True,
        return_train_score=False,
    )
    busca_knn.fit(X_treino, y_treino)

    melhor_knn = busca_knn.best_estimator_
    metricas_knn = _calcular_metricas(melhor_knn, X_teste, y_teste)

    melhor_modelo = (
        "KNN otimizado"
        if metricas_knn["f1"] >= metricas_logistica["f1"]
        else "Regressão Logística"
    )

    resultado = {
        "descricao_alvo": (
            f"1 se {COLUNA_BASE_ALVO} > mediana; 0 caso contrário"
        ),
        "limiar": limiar,
        "features": features,
        "seed": seed,
        "test_size": test_size,
        "cv_folds": cv_folds,
        "n_total": int(len(dados)),
        "n_treino": int(len(X_treino)),
        "n_teste": int(len(X_teste)),
        "classe_0": int((y == 0).sum()),
        "classe_1": int((y == 1).sum()),
        "logistica": metricas_logistica,
        "knn": metricas_knn,
        "knn_best_params": busca_knn.best_params_,
        "knn_cv_best_score": float(busca_knn.best_score_),
        "melhor_modelo": melhor_modelo,
        "modelo_logistica": logistica,
        "modelo_knn": melhor_knn,
        "grid_search": busca_knn,
    }

    texto = _formatar_relatorio(resultado)
    logger.info("\n%s", texto.rstrip())

    if relatorio_path is not None:
        relatorio_path.parent.mkdir(parents=True, exist_ok=True)
        relatorio_path.write_text(texto, encoding="utf-8")
        logger.info("Relatório de classificação salvo em: %s", relatorio_path)

    return resultado


def main() -> int:
    """Permite executar apenas a classificação a partir do CSV limpo."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%H:%M:%S",
    )

    if not OUTPUT_CSV.exists():
        logger.error("Dataset limpo não encontrado: %s", OUTPUT_CSV)
        return 1

    df = pd.read_csv(OUTPUT_CSV)
    executar_classificacao(df)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
