"""
cleaner.py - Analise Exploratoria e Tratamento Estatistico (EDA).

Este modulo centraliza a limpeza do dataset de queimadas do Kaggle.
Ele foi escrito para aceitar tanto os nomes originais em ingles do arquivo
amazon.csv (year, state, month, number, date) quanto nomes traduzidos pela
interface (ano, estado, mes, numero, data).

Etapas executadas:
    1. normalizacao de colunas, encoding e categorias;
    2. tratamento de nulos;
    3. isolamento de outliers pelo metodo IQR;
    4. merge logico com tabela auxiliar de regioes brasileiras.
"""
from __future__ import annotations

import logging
import re
import unicodedata
from typing import Iterable

import numpy as np
import pandas as pd

logger = logging.getLogger("pipeline.transform")

# ---------------------------------------------------------------------------
# Mapeamentos auxiliares
# ---------------------------------------------------------------------------
MESES_MAP = {
    "janeiro": 1,
    "jan": 1,
    "fevereiro": 2,
    "fev": 2,
    "marco": 3,
    "maro": 3,
    "marao": 3,
    "mar": 3,
    "abril": 4,
    "abr": 4,
    "maio": 5,
    "mai": 5,
    "junho": 6,
    "jun": 6,
    "julho": 7,
    "jul": 7,
    "agosto": 8,
    "ago": 8,
    "setembro": 9,
    "set": 9,
    "outubro": 10,
    "out": 10,
    "novembro": 11,
    "nov": 11,
    "dezembro": 12,
    "dez": 12,
    # Caso algum CSV venha em ingles.
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}

MESES_NOME = {
    1: "Janeiro",
    2: "Fevereiro",
    3: "Marco",
    4: "Abril",
    5: "Maio",
    6: "Junho",
    7: "Julho",
    8: "Agosto",
    9: "Setembro",
    10: "Outubro",
    11: "Novembro",
    12: "Dezembro",
}

REGIOES_POR_ESTADO = {
    # Norte
    "acre": "Norte",
    "amapa": "Norte",
    "amazonas": "Norte",
    "para": "Norte",
    "rondonia": "Norte",
    "roraima": "Norte",
    "tocantins": "Norte",
    # Nordeste
    "alagoas": "Nordeste",
    "bahia": "Nordeste",
    "ceara": "Nordeste",
    "maranhao": "Nordeste",
    "paraiba": "Nordeste",
    "pernambuco": "Nordeste",
    "piaui": "Nordeste",
    "piau": "Nordeste",  # forma truncada que aparece no amazon.csv do Kaggle
    "rio grande do norte": "Nordeste",
    "sergipe": "Nordeste",
    # Centro-Oeste
    "distrito federal": "Centro-Oeste",
    "goias": "Centro-Oeste",
    "mato grosso": "Centro-Oeste",
    "mato grosso do sul": "Centro-Oeste",
    # Sudeste
    "espirito santo": "Sudeste",
    "minas gerais": "Sudeste",
    "rio": "Sudeste",  # como aparece no dataset do Kaggle para Rio de Janeiro
    "rio de janeiro": "Sudeste",
    "sao paulo": "Sudeste",
    # Sul
    "parana": "Sul",
    "rio grande do sul": "Sul",
    "santa catarina": "Sul",
}

RENOMEAR_COLUNAS = {
    "year": "ano",
    "ano": "ano",
    "state": "estado",
    "estado": "estado",
    "month": "mes",
    "mes": "mes",
    "mês": "mes",
    "number": "numero_queimadas",
    "numero": "numero_queimadas",
    "número": "numero_queimadas",
    "data": "data",
    "date": "data",
}

COLUNAS_ESSENCIAIS = ["ano", "estado", "mes", "numero_queimadas"]


def _normalizar_ascii(valor: object) -> str:
    """Remove acentos, corrige caracteres estranhos comuns e padroniza texto."""
    if pd.isna(valor):
        return ""

    texto = str(valor).strip()
    # Correcoes simples de mojibake/caracter de substituicao.
    texto = (
        texto.replace("�", "c")
        .replace("Ã§", "c")
        .replace("Ã£", "a")
        .replace("Ã¡", "a")
        .replace("Ã©", "e")
        .replace("Ã³", "o")
        .replace("Ã´", "o")
        .replace("Ã­", "i")
        .replace("Ãº", "u")
    )
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip().lower()


def _normalizar_colunas(colunas: Iterable[object]) -> list[str]:
    novas_colunas: list[str] = []
    for coluna in colunas:
        nome = _normalizar_ascii(coluna)
        nome = re.sub(r"[^a-z0-9_]+", "_", nome).strip("_")
        novas_colunas.append(RENOMEAR_COLUNAS.get(nome, nome))
    return novas_colunas


def _title_sem_acentos(valor: object) -> str | float:
    """Padroniza categorias em formato Titulo, preservando nulos."""
    if pd.isna(valor):
        return np.nan
    texto = _normalizar_ascii(valor)
    if not texto:
        return np.nan
    return texto.title()


def _converter_numero(serie: pd.Series) -> pd.Series:
    """Converte strings numericas com virgula ou ponto decimal para float."""
    texto = serie.astype(str).str.strip()
    tem_virgula = texto.str.contains(",", regex=False, na=False)

    # Quando ha virgula, assume formato brasileiro: 1.234,56 -> 1234.56.
    texto_br = texto.str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
    texto_final = texto.where(~tem_virgula, texto_br)

    return pd.to_numeric(texto_final, errors="coerce")


def tratar_encoding_e_categorias(df: pd.DataFrame) -> pd.DataFrame:
    """Corrige nomes de colunas, codificacao e strings categoricas."""
    df = df.copy()
    df.columns = _normalizar_colunas(df.columns)

    colunas_ausentes = [col for col in COLUNAS_ESSENCIAIS if col not in df.columns]
    if colunas_ausentes:
        raise ValueError(
            "CSV fora do esquema esperado. Colunas obrigatorias ausentes: "
            f"{colunas_ausentes}. Colunas encontradas: {list(df.columns)}"
        )

    df["ano"] = pd.to_numeric(df["ano"], errors="coerce").astype("Int64")
    df["numero_queimadas"] = _converter_numero(df["numero_queimadas"])

    df["estado"] = df["estado"].apply(_title_sem_acentos)
    df["estado_chave"] = df["estado"].apply(_normalizar_ascii)

    df["mes_chave"] = df["mes"].apply(_normalizar_ascii)
    df["mes_numero"] = df["mes_chave"].map(MESES_MAP).astype("Int64")
    df["mes"] = df["mes_numero"].map(MESES_NOME)

    if "data" in df.columns:
        df["data_original"] = pd.to_datetime(df["data"], errors="coerce")
    else:
        df["data_original"] = pd.NaT

    df["data_referencia"] = pd.to_datetime(
        {
            "year": df["ano"].astype("float"),
            "month": df["mes_numero"].astype("float"),
            "day": 1,
        },
        errors="coerce",
    )

    logger.info("Colunas padronizadas: %s", list(df.columns))
    return df


def tratar_nulos(df: pd.DataFrame) -> pd.DataFrame:
    """Trata valores ausentes sem inventar categorias essenciais.

    Estrategia adotada:
      - Remove linhas sem ano, estado, mes ou numero de queimadas, pois essas
        variaveis formam a chave analitica minima do estudo.
      - Para data_original ausente/inconsistente, usa data_referencia criada de
        forma deterministica a partir de ano + mes_numero.
    """
    df = df.copy()
    nulos_antes = df.isna().sum()
    logger.info("Nulos antes do tratamento: %s", nulos_antes[nulos_antes > 0].to_dict())

    linhas_antes = len(df)
    df = df.dropna(subset=["ano", "estado", "mes_numero", "numero_queimadas"])
    removidas = linhas_antes - len(df)

    if "data_original" in df.columns:
        df["data_original"] = df["data_original"].fillna(df["data_referencia"])

    df["ano"] = df["ano"].astype(int)
    df["mes_numero"] = df["mes_numero"].astype(int)

    logger.info("Linhas removidas por nulos essenciais: %d", removidas)
    nulos_depois = df.isna().sum()
    logger.info("Nulos depois do tratamento: %s", nulos_depois[nulos_depois > 0].to_dict())
    return df


def isolar_outliers_iqr(df: pd.DataFrame, colunas: list[str] | None = None) -> pd.DataFrame:
    """Isola outliers das colunas numericas relevantes via IQR.

    Em vez de apagar registros extremos, o pipeline cria uma coluna booleana
    indicando outlier e uma versao winsorizada para analises em que seja preciso
    reduzir distorcao estatistica. Isso preserva os eventos raros para auditoria.
    """
    df = df.copy()
    if colunas is None:
        colunas = ["numero_queimadas"]

    for coluna in colunas:
        if coluna not in df.columns:
            logger.warning("Coluna %s nao encontrada para IQR; ignorando.", coluna)
            continue

        valores = pd.to_numeric(df[coluna], errors="coerce")
        q1 = valores.quantile(0.25)
        q3 = valores.quantile(0.75)
        iqr = q3 - q1

        if pd.isna(iqr) or iqr == 0:
            logger.warning("IQR invalido/zero para %s; nenhum outlier marcado.", coluna)
            df[f"{coluna}_outlier_iqr"] = False
            df[f"{coluna}_tratado_iqr"] = valores
            continue

        limite_inferior = q1 - 1.5 * iqr
        limite_superior = q3 + 1.5 * iqr
        mascara_outlier = (valores < limite_inferior) | (valores > limite_superior)

        df[f"{coluna}_outlier_iqr"] = mascara_outlier
        df[f"{coluna}_tratado_iqr"] = valores.clip(limite_inferior, limite_superior)

        logger.info(
            "IQR de %s: Q1=%.2f, Q3=%.2f, IQR=%.2f, limites=[%.2f, %.2f], outliers=%d",
            coluna,
            q1,
            q3,
            iqr,
            limite_inferior,
            limite_superior,
            int(mascara_outlier.sum()),
        )

    return df


def consolidar_merge(df: pd.DataFrame) -> pd.DataFrame:
    """Faz merge com tabela auxiliar estado -> regiao, sem perda silenciosa."""
    df = df.copy()
    tabela_regioes = pd.DataFrame(
        [{"estado_chave": chave, "regiao": regiao} for chave, regiao in REGIOES_POR_ESTADO.items()]
    )

    linhas_antes = len(df)
    df = df.merge(tabela_regioes, on="estado_chave", how="left", validate="many_to_one")

    if len(df) != linhas_antes:
        raise RuntimeError("O merge alterou a quantidade de linhas, indicando duplicidade de chaves.")

    sem_regiao = sorted(df.loc[df["regiao"].isna(), "estado"].dropna().unique().tolist())
    if sem_regiao:
        logger.warning(
            "Estados sem correspondencia na tabela de regioes: %s. Marcando como 'Nao identificado'.",
            sem_regiao,
        )
        df["regiao"] = df["regiao"].fillna("Nao identificado")

    colunas_finais = [
        "ano",
        "mes",
        "mes_numero",
        "data_referencia",
        "estado",
        "regiao",
        "numero_queimadas",
        "numero_queimadas_outlier_iqr",
        "numero_queimadas_tratado_iqr",
    ]
    colunas_existentes = [col for col in colunas_finais if col in df.columns]
    return df[colunas_existentes].sort_values(["ano", "mes_numero", "estado"]).reset_index(drop=True)


def limpar_dados(df_bruto: pd.DataFrame) -> pd.DataFrame:
    """Orquestra a limpeza e transformacao completa do DataFrame bruto."""
    logger.info("Iniciando limpeza. Entrada: %d x %d", *df_bruto.shape)

    df = df_bruto.copy()
    df = tratar_encoding_e_categorias(df)
    df = tratar_nulos(df)
    df = isolar_outliers_iqr(df)
    df = consolidar_merge(df)

    logger.info("Limpeza finalizada. Saida: %d x %d", *df.shape)
    return df
