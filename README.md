# Pipeline de Queimadas no Brasil 🔥

Pipeline de dados **reprodutível** para análise de focos de queimadas no Brasil,
desenvolvido para a **Avaliação Prática Unificada (Parte 1) — Ciência de Dados**.

- **Tema (Opção C):** Meio Ambiente (Queimadas)
- **Equipe:** Saul, Edílson, Luiz Vitor
- **Fonte de dados:** [Forest Fires in Brazil — Kaggle](https://www.kaggle.com/datasets/gustavomodelli/forest-fires-in-brazil)

---

## 📦 Estrutura do projeto

```
pipeline-queimadas-brasil/
├── src/
│   ├── extract/
│   │   └── extractor.py    # Ingestão e leitura dos CSVs brutos
│   ├── transform/
│   │   └── cleaner.py      # Tratamento estatístico (nulos e IQR) + merge
│   ├── visualize.py        # Gráfico com integridade visual
│   └── main.py             # Orquestrador central do pipeline
├── data/raw/               # CSV original do Kaggle (não versionado)
├── outputs/                # Gráficos gerados
├── requirements.txt
└── README.md
```

## ▶️ Como executar

```bash
# 1. Crie e ative um ambiente virtual (opcional, recomendado)
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/Mac

# 2. Instale as dependências
pip install -r requirements.txt

# 3. Baixe o dataset do Kaggle e coloque em data/raw/amazon.csv

# 4. Execute o pipeline a partir da raiz do projeto
python src/main.py
```

Ao final, o pipeline gera automaticamente:
- `dados_limpos_final.csv` (base consolidada na raiz)
- `outputs/grafico_principal.png` (visualização)

