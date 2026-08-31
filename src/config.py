"""
config.py

Centraliza todas as configurações e caminhos do projeto.
"""

from pathlib import Path

# =====================================================
# Diretórios
# =====================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"

OUTPUT_DIR = BASE_DIR / "outputs"

GRAPH_DIR = OUTPUT_DIR / "graficos"
REPORT_DIR = OUTPUT_DIR / "relatorios"
DATA_OUTPUT_DIR = OUTPUT_DIR / "dados"

# =====================================================
# Criação automática das pastas
# =====================================================

for pasta in [GRAPH_DIR, REPORT_DIR, DATA_OUTPUT_DIR]:
    pasta.mkdir(parents=True, exist_ok=True)

# =====================================================
# Arquivos
# =====================================================

OUTPUT_CSV = DATA_OUTPUT_DIR / "dados_limpos_final.csv"

STATISTICS_FILE = REPORT_DIR / "estatisticas.csv"

REPORT_FILE = REPORT_DIR / "relatorio.txt"

# =====================================================
# Configurações
# =====================================================

ENCODING = "utf-8"

LOG_LEVEL = "INFO"

IQR_FACTOR = 1.5

# =====================================================
# Inferência estatística (Parte 2 — seções 4.1 e 4.2)
# =====================================================

COLUNA_INFERENCIA = "numero_queimadas"

N_BOOTSTRAP = 2000
N_PERMUTACOES = 2000
ALPHA = 0.05
Z_95 = 1.96
RANDOM_SEED = 42

# Período seco: junho a outubro (temporada clássica de queimadas no Brasil).
# Período chuvoso: novembro a maio.
MESES_PERIODO_SECO = (6, 7, 8, 9, 10)
MESES_PERIODO_CHUVOSO = (11, 12, 1, 2, 3, 4, 5)

BOOTSTRAP_PLOT = BASE_DIR / "distribuicao_bootstrap.png"
PERMUTACAO_PLOT = BASE_DIR / "distribuicao_permutacao.png"

BOOTSTRAP_REPORT = REPORT_DIR / "inferencia_bootstrap.txt"
AB_TESTING_REPORT = REPORT_DIR / "teste_ab.txt"