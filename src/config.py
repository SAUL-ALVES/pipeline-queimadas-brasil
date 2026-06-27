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