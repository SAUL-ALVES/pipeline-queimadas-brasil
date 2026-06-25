# Pipeline de Queimadas no Brasil

Projeto desenvolvido para a **Avaliação Prática Unificada — Ciência de Dados**.

- **Tema escolhido:** Opção C — Meio Ambiente / Queimadas
- **Dataset:** Forest Fires in Brazil — Kaggle
- **Arquivo esperado:** `data/raw/amazon.csv`
- **Período informado pelo dataset:** 1998 a 2017
- **Unidade de análise:** registros agregados por ano, mês e estado brasileiro

---

## 1. Objetivo do projeto

O objetivo deste projeto é construir um pipeline reprodutível de Ciência de Dados para ingestão, limpeza, tratamento estatístico, consolidação e visualização de dados sobre queimadas registradas no Brasil.

Além do processamento técnico, o projeto documenta limitações de amostragem, viés de seleção, classificação estatística das variáveis e uma reflexão sobre inferência causal.

---

## 2. Estrutura do projeto

```text
pipeline-queimadas-brasil/
├── data/
│   └── raw/
│       └── amazon.csv
├── outputs/
├── src/
│   ├── extract/
│   │   └── extractor.py
│   ├── transform/
│   │   └── cleaner.py
│   ├── visualize.py
│   └── main.py
├── requirements.txt
└── README.md
```

O arquivo final limpo é gerado automaticamente na raiz do projeto com o nome:

```text
dados_limpos_final.csv
```

O gráfico principal é gerado em:

```text
outputs/grafico_principal.png
```

---

## 3. Como executar

### 3.1. Preparar ambiente

```bash
python -m venv .venv
```

No Windows:

```bash
.venv\Scripts\activate
```

No Linux/Mac:

```bash
source .venv/bin/activate
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

### 3.2. Baixar o dataset

Baixe o arquivo `amazon.csv` do Kaggle e coloque em:

```text
data/raw/amazon.csv
```

### 3.3. Executar o pipeline

A partir da raiz do projeto:

```bash
python src/main.py
```

O pipeline executa quatro etapas:

1. ingestão dos dados brutos;
2. limpeza e tratamento estatístico;
3. geração do CSV final limpo;
4. geração automática do gráfico.

---

## 4. Camada de ingestão: amostragem e viés

### 4.1. População-alvo ideal

A população-alvo ideal seria o conjunto completo de todas as ocorrências reais de queimadas e incêndios florestais no território brasileiro, em todos os estados, biomas e períodos do ano, incluindo eventos grandes, médios e pequenos, independentemente de terem sido detectados, comunicados ou registrados oficialmente.

Em um cenário ideal, a base representaria todos os focos de incêndio ocorridos no Brasil, com data exata, localização precisa, intensidade, área afetada, causa provável e condições ambientais associadas.

### 4.2. Estrutura de acesso real do dataset

A estrutura de acesso real é o dataset disponibilizado no Kaggle, derivado de dados oficiais consolidados sobre incêndios florestais no Brasil. O arquivo usado no pipeline é uma tabela agregada por ano, estado, mês, número de queimadas e data de referência.

Portanto, o dataset não representa cada incêndio individualmente. Ele representa uma visão agregada e já filtrada dos registros disponíveis na fonte original. A unidade observada não é “um incêndio”, mas sim “a contagem de queimadas registradas para determinado estado, mês e ano”.

### 4.3. Risco de viés de seleção

Há risco de viés de seleção porque os dados disponíveis dependem da capacidade de detecção, registro e consolidação das ocorrências. Algumas regiões podem ter maior cobertura de monitoramento que outras. Além disso, queimadas pequenas, rápidas ou em áreas com menor observação podem ser subnotificadas.

Também pode haver mudanças metodológicas ao longo do tempo. Se a forma de detectar ou registrar queimadas mudou entre 1998 e 2017, parte da variação temporal pode refletir mudança de medição, e não necessariamente aumento ou redução real das queimadas.

Outro ponto importante é que o dataset não inclui diretamente variáveis ambientais, sociais ou econômicas, como chuva, umidade, desmatamento, fiscalização, expansão agropecuária ou densidade populacional rural. Isso limita a interpretação causal dos resultados.

---

## 5. Tratamento estatístico e EDA

### 5.1. Sanitização e padronização

O arquivo `src/transform/cleaner.py` realiza:

- normalização dos nomes das colunas;
- compatibilidade com colunas em inglês ou português;
- correção de problemas simples de encoding;
- padronização de estados e meses;
- conversão da coluna de número de queimadas para valor numérico;
- criação da coluna `mes_numero`;
- criação da coluna `data_referencia` com base em ano e mês.

### 5.2. Tratamento de nulos: viés vs variância

A estratégia adotada foi remover registros com nulos em variáveis essenciais: `ano`, `estado`, `mes_numero` e `numero_queimadas`.

Essa escolha foi feita porque essas colunas formam a chave mínima da análise. Sem ano, estado, mês ou número de queimadas, o registro perde sua utilidade estatística principal. Imputar essas variáveis poderia criar observações artificiais e gerar conclusões enganosas.

Para a data, quando houver falha, o pipeline usa `data_referencia`, calculada deterministicamente a partir de `ano` e `mes_numero`. Essa imputação tem baixo risco porque a data de referência serve apenas para organizar a série temporal mensal, e não para substituir uma medição causal independente.

Do ponto de vista teórico:

- **Viés:** a exclusão pode introduzir viés se os registros ausentes não forem aleatórios. Por exemplo, se determinados estados ou anos tiverem mais falhas, esses grupos podem ficar sub-representados.
- **Variância:** a exclusão reduz o tamanho da amostra e pode aumentar a sensibilidade dos resultados a novos dados. Porém, também evita que imputações arbitrárias aumentem ruído ou criem padrões inexistentes.

Neste projeto, a exclusão foi considerada mais segura do que imputar ano, estado, mês ou número de queimadas, pois essas variáveis são estruturais para a análise.

### 5.3. Tratamento de outliers por IQR

O pipeline aplica o método do Intervalo Interquartil na variável `numero_queimadas`.

A regra usada é:

```text
Q1 = percentil 25%
Q3 = percentil 75%
IQR = Q3 - Q1
Limite inferior = Q1 - 1,5 × IQR
Limite superior = Q3 + 1,5 × IQR
```

Valores abaixo do limite inferior ou acima do limite superior são marcados como outliers.

O pipeline não apaga automaticamente esses registros, porque queimadas extremas podem representar eventos reais e importantes. Em vez disso, ele cria duas colunas:

- `numero_queimadas_outlier_iqr`: indica se o registro é outlier;
- `numero_queimadas_tratado_iqr`: versão winsorizada, limitada aos limites estatísticos do IQR.

Assim, o projeto preserva a informação original e, ao mesmo tempo, oferece uma variável tratada para reduzir distorções em análises agregadas.

### 5.4. Consolidação lógica por merge

Embora o dataset principal tenha apenas uma tabela, o pipeline realiza uma consolidação lógica criando uma tabela auxiliar `estado -> regiao`.

O merge é feito pela chave normalizada do estado, usando `how='left'`. Isso evita perda silenciosa de amostras, pois nenhum registro do dataset principal é removido durante o cruzamento.

O código também valida se há estados sem correspondência na tabela auxiliar. Caso existam, eles são marcados como `Nao identificado`, preservando a linha para auditoria.

---

## 6. Dicionário de dados final

| Variável | Descrição | Tipo estatístico |
|---|---|---|
| `ano` | Ano do registro da queimada | Discreta |
| `mes` | Nome padronizado do mês | Categórica |
| `mes_numero` | Número do mês, de 1 a 12 | Discreta |
| `data_referencia` | Data mensal criada a partir de ano e mês | Discreta temporal |
| `estado` | Estado brasileiro do registro | Categórica |
| `regiao` | Região brasileira obtida por merge auxiliar | Categórica |
| `numero_queimadas` | Número original de queimadas registradas | Discreta |
| `numero_queimadas_outlier_iqr` | Indica se o registro foi classificado como outlier pelo IQR | Categórica |
| `numero_queimadas_tratado_iqr` | Número de queimadas após winsorização pelo IQR | Contínua operacional |

Observação: a variável `numero_queimadas` é uma contagem e, portanto, é naturalmente discreta. A variável tratada por IQR pode assumir valores de limite estatístico com casas decimais, por isso foi classificada como contínua operacional.

---

## 7. Análise de domínio: inferência causal e ceteris paribus

### Relação hipotética escolhida

Relação analisada: **mês do ano e número de queimadas registradas**.

Hipótese: determinados meses do ano apresentam maior número de queimadas, especialmente períodos associados a estiagem, baixa umidade e práticas agrícolas de limpeza de terreno.

### a) Por que correlação não comprova causalidade

Mesmo que o dataset mostre forte correlação entre determinados meses e o aumento do número de queimadas, isso não é suficiente para comprovar causalidade.

A correlação indica que duas variáveis variam juntas, mas não demonstra que uma causa diretamente a outra. O mês do ano, por si só, não “causa” a queimada. Ele pode estar funcionando como marcador temporal de outros fatores reais, como baixa umidade, menor volume de chuvas, maior temperatura, ventos, calendário agrícola ou aumento de atividades humanas em determinada época.

Além disso, os dados são observacionais. Não houve controle experimental das condições. Portanto, diferenças entre meses podem estar misturadas com diferenças entre estados, biomas, políticas públicas, fiscalização, ocupação do solo e qualidade do monitoramento.

Assim, uma correlação matemática forte pode sugerir uma hipótese, mas não prova nexo causal.

### b) Variáveis de confusão possíveis

**1. Condições climáticas**

Chuva, umidade relativa do ar, temperatura e vento são variáveis que podem influenciar diretamente a ocorrência e a propagação de queimadas. Se meses específicos têm menos chuva e menor umidade, o aumento das queimadas pode ser causado pelas condições climáticas, e não apenas pelo mês em si.

Nesse caso, o mês estaria correlacionado com o clima. Ignorar essa variável pode superestimar o efeito do mês sobre as queimadas.

**2. Atividade humana e uso do solo**

A expansão agropecuária, o desmatamento, a limpeza de áreas para plantio e a ocupação territorial também podem aumentar o número de queimadas. Estados ou períodos com maior pressão econômica sobre a terra podem registrar mais focos de incêndio.

Se essas atividades forem mais intensas em alguns meses ou regiões, elas podem confundir a relação entre mês e número de queimadas.

**3. Fiscalização e capacidade de monitoramento**

Mudanças em políticas públicas, fiscalização ambiental ou tecnologia de detecção podem alterar o número de registros observados. Um aumento nos registros pode representar mais queimadas reais, mas também pode representar melhor monitoramento.

Se esse fator for ignorado, o estudo pode interpretar como aumento ambiental aquilo que é parcialmente uma mudança na capacidade de observação.

### c) Cenário ideal sob o princípio do ceteris paribus

Para isolar adequadamente o efeito causal do período do ano sobre as queimadas, seria necessário comparar situações em que todas as demais condições relevantes permanecessem constantes.

Um desenho ideal sob o princípio do **ceteris paribus** controlaria, por exemplo:

- mesmo estado ou mesma região;
- mesmo bioma;
- mesma cobertura vegetal;
- mesmo nível de fiscalização;
- mesma metodologia de registro;
- mesmas condições socioeconômicas;
- níveis semelhantes de chuva, temperatura, umidade e vento;
- mesmo padrão de uso do solo.

Na prática, um estudo mais robusto poderia usar modelos com efeitos fixos por estado e por ano, além de incluir variáveis climáticas e socioeconômicas externas. Assim, a comparação entre meses seria feita mantendo constantes vários fatores que também influenciam as queimadas.

Como o dataset usado neste trabalho não traz essas variáveis de controle, o projeto deve ser interpretado como análise exploratória e descritiva, não como comprovação causal definitiva.

---

## 8. Visualização científica e integridade visual

O script `src/visualize.py` gera um gráfico de linhas com a evolução anual do total de queimadas registradas no Brasil.

Medidas de honestidade visual adotadas:

- título claro;
- eixo X identificado como ano;
- eixo Y identificado como total de queimadas registradas;
- unidade explícita de contagem;
- eixo Y iniciado em zero;
- escala proporcional;
- ausência de cortes de eixo que exagerem visualmente diferenças pequenas.

O gráfico usa a variável `numero_queimadas_tratado_iqr`, quando disponível, para reduzir o efeito visual de valores extremos sem apagar os registros originais do dataset final.

---

## 9. Limitações do projeto

Este pipeline é adequado para análise exploratória, visualização e preparação estatística inicial. Porém, ele possui limitações importantes:

- não prova causalidade;
- depende da qualidade da fonte original;
- trabalha com dados agregados, não eventos individuais;
- não inclui clima, desmatamento, fiscalização ou variáveis socioeconômicas;
- pode haver subnotificação ou mudanças de metodologia ao longo dos anos.

Portanto, as conclusões devem ser interpretadas como evidências descritivas sobre padrões de queimadas registradas, e não como afirmações causais definitivas.

---

## 10. Arquivos principais

| Arquivo | Função |
|---|---|
| `src/extract/extractor.py` | Lê os CSVs brutos e registra volumetria inicial |
| `src/transform/cleaner.py` | Padroniza dados, trata nulos, aplica IQR e faz merge com regiões |
| `src/visualize.py` | Gera gráfico científico com integridade visual |
| `src/main.py` | Orquestra todo o pipeline |
| `requirements.txt` | Lista dependências do projeto |
| `README.md` | Documentação técnica e fundamentação científica |
