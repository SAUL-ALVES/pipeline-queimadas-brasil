"""
bootstrap.py

Estimação da média populacional de queimadas por reamostragem Bootstrap
e comparação com o intervalo de confiança paramétrico (aproximação normal).

Atende à seção 4.1 da Avaliação Prática Unificada (Parte 2):

1. média amostral e desvio padrão amostral;
2. pelo menos 2.000 réplicas bootstrap com reposição;
3. IC 95% não-paramétrico (percentis 2,5% e 97,5%);
4. IC 95% paramétrico: X̄ ± z95% · s / √N, com z95% ≈ 1,96.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

SRC_DIR = Path(__file__).resolve().parent.parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from config import (
    ALPHA,
    BOOTSTRAP_PLOT,
    BOOTSTRAP_REPORT,
    COLUNA_INFERENCIA,
    N_BOOTSTRAP,
    OUTPUT_CSV,
    RANDOM_SEED,
    Z_95,
)

logger = logging.getLogger("pipeline.inference.bootstrap")


def _assimetria_amostral(x: np.ndarray, media: float, desvio: float) -> float:
    """Terceiro momento padronizado (assimetria de Pearson)."""
    if desvio == 0:
        return 0.0
    return float(np.mean(((x - media) / desvio) ** 3))


def estimar_parametros(x: np.ndarray) -> dict:
    """Calcula média, desvio padrão amostral (ddof=1) e assimetria."""
    n = int(x.size)
    media = float(np.mean(x))
    desvio = float(np.std(x, ddof=1))
    return {
        "n": n,
        "media": media,
        "desvio": desvio,
        "mediana": float(np.median(x)),
        "assimetria": _assimetria_amostral(x, media, desvio),
        "minimo": float(np.min(x)),
        "maximo": float(np.max(x)),
    }


def reamostrar_bootstrap(
    x: np.ndarray,
    n_replicas: int = N_BOOTSTRAP,
    seed: int = RANDOM_SEED,
) -> np.ndarray:
    """
    Reamostragem com reposição para obter a distribuição empírica da média.

    Cada réplica sorteia N observações (mesmo tamanho da amostra original)
    e calcula a média. O laço deixa o algoritmo explícito, como pedido
    no enunciado (processo de reamostragem, não apenas uma função pronta).
    """
    n = x.size
    rng = np.random.default_rng(seed)
    medias = np.empty(n_replicas, dtype=float)

    for i in range(n_replicas):
        replica = rng.choice(x, size=n, replace=True)
        medias[i] = replica.mean()

    return medias


def intervalo_confianca_bootstrap(medias: np.ndarray, alpha: float = ALPHA) -> tuple[float, float]:
    """IC não-paramétrico pelos percentis da distribuição bootstrap."""
    limite_inferior = float(np.percentile(medias, 100.0 * (alpha / 2.0)))
    limite_superior = float(np.percentile(medias, 100.0 * (1.0 - alpha / 2.0)))
    return limite_inferior, limite_superior


def intervalo_confianca_parametrico(
    media: float,
    desvio: float,
    n: int,
    z: float = Z_95,
) -> tuple[float, float]:
    """
    IC 95% pela aproximação normal:

        IC = X̄ ± z95% · s / √N
    """
    erro_padrao = desvio / np.sqrt(n)
    margem = z * erro_padrao
    return float(media - margem), float(media + margem)


def _formatar_relatorio(resultado: dict) -> str:
    ic_boot = resultado["ic_bootstrap"]
    ic_param = resultado["ic_parametrico"]
    params = resultado["parametros"]

    return (
        "============================================================\n"
        "INFERÊNCIA — BOOTSTRAP E INTERVALOS DE CONFIANÇA (95%)\n"
        "============================================================\n"
        f"Variável....................: {resultado['coluna']}\n"
        f"Tamanho amostral (N)........: {params['n']:,}\n"
        f"Réplicas bootstrap..........: {resultado['n_replicas']:,}\n"
        f"Semente aleatória...........: {resultado['seed']}\n"
        "\n"
        "Parâmetros amostrais observados\n"
        f"  Média (X barra)...........: {params['media']:.4f}\n"
        f"  Desvio padrão (s).........: {params['desvio']:.4f}\n"
        f"  Mediana...................: {params['mediana']:.4f}\n"
        f"  Assimetria................: {params['assimetria']:.4f}\n"
        f"  Mínimo / Máximo...........: {params['minimo']:.4f} / {params['maximo']:.4f}\n"
        "\n"
        "Intervalo de confiança 95% — Bootstrap (percentis 2,5% e 97,5%)\n"
        f"  Limite inferior...........: {ic_boot[0]:.4f}\n"
        f"  Limite superior...........: {ic_boot[1]:.4f}\n"
        f"  Amplitude.................: {ic_boot[1] - ic_boot[0]:.4f}\n"
        "\n"
        "Intervalo de confiança 95% — Paramétrico (X barra ± 1,96 · s/√N)\n"
        f"  Erro padrão (s/√N)........: {resultado['erro_padrao']:.4f}\n"
        f"  Limite inferior...........: {ic_param[0]:.4f}\n"
        f"  Limite superior...........: {ic_param[1]:.4f}\n"
        f"  Amplitude.................: {ic_param[1] - ic_param[0]:.4f}\n"
        "============================================================\n"
    )


def executar_bootstrap(
    df: pd.DataFrame,
    coluna: str = COLUNA_INFERENCIA,
    n_replicas: int = N_BOOTSTRAP,
    seed: int = RANDOM_SEED,
    relatorio_path: Path | None = BOOTSTRAP_REPORT,
) -> dict:
    """Estima a média por bootstrap e constrói os dois ICs de 95%."""
    if coluna not in df.columns:
        raise KeyError(f"Coluna '{coluna}' não encontrada no dataset limpo.")

    x = df[coluna].dropna().to_numpy(dtype=float)
    if x.size == 0:
        raise ValueError(f"A coluna '{coluna}' não possui valores numéricos válidos.")

    logger.info(
        "Bootstrap da média de '%s' (N=%d, réplicas=%d)",
        coluna,
        x.size,
        n_replicas,
    )

    parametros = estimar_parametros(x)
    medias = reamostrar_bootstrap(x, n_replicas=n_replicas, seed=seed)
    ic_bootstrap = intervalo_confianca_bootstrap(medias)
    ic_parametrico = intervalo_confianca_parametrico(
        parametros["media"],
        parametros["desvio"],
        parametros["n"],
    )

    resultado = {
        "coluna": coluna,
        "n_replicas": n_replicas,
        "seed": seed,
        "parametros": parametros,
        "medias_bootstrap": medias,
        "ic_bootstrap": ic_bootstrap,
        "ic_parametrico": ic_parametrico,
        "erro_padrao": parametros["desvio"] / np.sqrt(parametros["n"]),
        "grafico": BOOTSTRAP_PLOT,
    }

    texto = _formatar_relatorio(resultado)
    logger.info("\n%s", texto.rstrip())

    if relatorio_path is not None:
        relatorio_path.parent.mkdir(parents=True, exist_ok=True)
        relatorio_path.write_text(texto, encoding="utf-8")
        logger.info("Relatório bootstrap salvo em: %s", relatorio_path)

    return resultado


def main() -> int:
    """Permite executar só a etapa de bootstrap a partir do CSV limpo."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%H:%M:%S",
    )

    if not OUTPUT_CSV.exists():
        logger.error("Dataset limpo não encontrado: %s", OUTPUT_CSV)
        return 1

    df = pd.read_csv(OUTPUT_CSV)
    executar_bootstrap(df)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
