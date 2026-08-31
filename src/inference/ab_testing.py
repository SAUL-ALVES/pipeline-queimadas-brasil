"""
ab_testing.py

Teste A/B por permutação: período seco versus período chuvoso quanto ao
número médio de queimadas registradas.

Atende à seção 4.2 da Avaliação Prática Unificada (Parte 2):

1. declaração formal de H0 e H1;
2. α = 0,05;
3. estatística observada = X̄_A − X̄_B;
4. teste de permutação com pelo menos 2.000 embaralhamentos de rótulos;
5. p-valor empírico bicaudal.
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
    AB_TESTING_REPORT,
    ALPHA,
    COLUNA_INFERENCIA,
    MESES_PERIODO_CHUVOSO,
    MESES_PERIODO_SECO,
    N_PERMUTACOES,
    OUTPUT_CSV,
    PERMUTACAO_PLOT,
    RANDOM_SEED,
)

logger = logging.getLogger("pipeline.inference.ab")

H0 = (
    "H0: μ_seco = μ_chuvoso  "
    "(o número médio de queimadas registradas é igual nos dois períodos)"
)
H1 = (
    "H1: μ_seco ≠ μ_chuvoso  "
    "(o número médio de queimadas registradas difere entre os períodos)"
)


def segmentar_grupos(
    df: pd.DataFrame,
    coluna: str = COLUNA_INFERENCIA,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Grupo A: período seco (junho–outubro).
    Grupo B: período chuvoso (novembro–maio).

    Os grupos são mutuamente exclusivos porque cada registro possui um
    único mês, logo um único período climático.
    """
    if "mes_numero" not in df.columns:
        raise KeyError("Coluna 'mes_numero' ausente no dataset limpo.")
    if coluna not in df.columns:
        raise KeyError(f"Coluna '{coluna}' não encontrada no dataset limpo.")

    seco = df.loc[df["mes_numero"].isin(MESES_PERIODO_SECO), coluna].dropna()
    chuvoso = df.loc[df["mes_numero"].isin(MESES_PERIODO_CHUVOSO), coluna].dropna()

    if seco.empty or chuvoso.empty:
        raise ValueError("Um dos grupos do teste A/B ficou vazio após a segmentação.")

    return seco.to_numpy(dtype=float), chuvoso.to_numpy(dtype=float)


def estatistica_diferenca_medias(grupo_a: np.ndarray, grupo_b: np.ndarray) -> float:
    """Estatística de teste: X̄_A − X̄_B."""
    return float(grupo_a.mean() - grupo_b.mean())


def teste_permutacao(
    grupo_a: np.ndarray,
    grupo_b: np.ndarray,
    n_iteracoes: int = N_PERMUTACOES,
    seed: int = RANDOM_SEED,
) -> tuple[np.ndarray, float, int]:
    """
    Simula a distribuição da diferença de médias sob H0 embaralhando
    os rótulos de grupo. Sob a nula, os dois rótulos são intercambiáveis.

    O p-valor bicaudal é a proporção de permutações cuja estatística
    é tão ou mais extrema (em valor absoluto) do que a observada.
    """
    observada = estatistica_diferenca_medias(grupo_a, grupo_b)
    combinado = np.concatenate([grupo_a, grupo_b])
    n_a = grupo_a.size
    rng = np.random.default_rng(seed)

    estatisticas_nulas = np.empty(n_iteracoes, dtype=float)
    for i in range(n_iteracoes):
        rng.shuffle(combinado)
        permutado_a = combinado[:n_a]
        permutado_b = combinado[n_a:]
        estatisticas_nulas[i] = permutado_a.mean() - permutado_b.mean()

    extremos = np.abs(estatisticas_nulas) >= np.abs(observada)
    n_extremos = int(np.sum(extremos))
    p_valor = n_extremos / float(n_iteracoes)
    return estatisticas_nulas, p_valor, n_extremos


def _formatar_relatorio(resultado: dict) -> str:
    rejeita = resultado["rejeita_h0"]
    decisao = (
        "Rejeitar H0 ao nível de 5%."
        if rejeita
        else "Não rejeitar H0 ao nível de 5%."
    )

    return (
        "============================================================\n"
        "TESTE A/B — PERMUTAÇÃO (PERÍODO SECO vs. PERÍODO CHUVOSO)\n"
        "============================================================\n"
        f"Variável resposta...........: {resultado['coluna']}\n"
        f"Grupo A (período seco)......: meses {list(MESES_PERIODO_SECO)}\n"
        f"Grupo B (período chuvoso)...: meses {list(MESES_PERIODO_CHUVOSO)}\n"
        f"Iterações de permutação.....: {resultado['n_iteracoes']:,}\n"
        f"Semente aleatória...........: {resultado['seed']}\n"
        f"α (significância)...........: {resultado['alpha']:.2f}\n"
        "\n"
        "Hipóteses\n"
        f"  {H0}\n"
        f"  {H1}\n"
        "\n"
        "Amostras\n"
        f"  N_A (seco)................: {resultado['n_a']:,}\n"
        f"  N_B (chuvoso).............: {resultado['n_b']:,}\n"
        f"  Média A (seco)............: {resultado['media_a']:.4f}\n"
        f"  Média B (chuvoso).........: {resultado['media_b']:.4f}\n"
        f"  Estatística observada.....: {resultado['estatistica_observada']:.4f}\n"
        "      (X barra_A − X barra_B)\n"
        "\n"
        "Resultado do teste de permutação (bicaudal)\n"
        f"  p-valor empírico..........: {resultado['p_valor_texto']}\n"
        f"  Decisão...................: {decisao}\n"
        "============================================================\n"
    )


def executar_teste_ab(
    df: pd.DataFrame,
    coluna: str = COLUNA_INFERENCIA,
    n_iteracoes: int = N_PERMUTACOES,
    alpha: float = ALPHA,
    seed: int = RANDOM_SEED,
    relatorio_path: Path | None = AB_TESTING_REPORT,
) -> dict:
    """Executa o teste A/B por permutação e registra a decisão formal."""
    grupo_a, grupo_b = segmentar_grupos(df, coluna=coluna)

    logger.info(
        "Teste A/B por permutação: seco (N=%d) vs. chuvoso (N=%d), %d iterações",
        grupo_a.size,
        grupo_b.size,
        n_iteracoes,
    )

    observada = estatistica_diferenca_medias(grupo_a, grupo_b)
    estatisticas_nulas, p_valor, n_extremos = teste_permutacao(
        grupo_a,
        grupo_b,
        n_iteracoes=n_iteracoes,
        seed=seed,
    )

    if p_valor == 0.0:
        p_valor_texto = f"< {1.0 / n_iteracoes:.4f} (0/{n_iteracoes:,} permutações tão extremas)"
    else:
        p_valor_texto = f"{p_valor:.6f} ({n_extremos}/{n_iteracoes:,})"

    resultado = {
        "coluna": coluna,
        "hipotese_nula": H0,
        "hipotese_alternativa": H1,
        "alpha": alpha,
        "n_iteracoes": n_iteracoes,
        "seed": seed,
        "n_a": int(grupo_a.size),
        "n_b": int(grupo_b.size),
        "media_a": float(grupo_a.mean()),
        "media_b": float(grupo_b.mean()),
        "estatistica_observada": observada,
        "estatisticas_nulas": estatisticas_nulas,
        "p_valor": p_valor,
        "p_valor_texto": p_valor_texto,
        "n_extremos": n_extremos,
        "rejeita_h0": bool(p_valor < alpha),
        "grafico": PERMUTACAO_PLOT,
    }

    texto = _formatar_relatorio(resultado)
    logger.info("\n%s", texto.rstrip())

    if relatorio_path is not None:
        relatorio_path.parent.mkdir(parents=True, exist_ok=True)
        relatorio_path.write_text(texto, encoding="utf-8")
        logger.info("Relatório do teste A/B salvo em: %s", relatorio_path)

    return resultado


def main() -> int:
    """Permite executar só o teste A/B a partir do CSV limpo."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%H:%M:%S",
    )

    if not OUTPUT_CSV.exists():
        logger.error("Dataset limpo não encontrado: %s", OUTPUT_CSV)
        return 1

    df = pd.read_csv(OUTPUT_CSV)
    executar_teste_ab(df)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
