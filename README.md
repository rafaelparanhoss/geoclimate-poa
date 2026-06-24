# geoclimate-poa

Projeto geoespacial para análise exploratória de vulnerabilidade térmica urbana
em Porto Alegre, Rio Grande do Sul.

O MVP integra temperatura de superfície, vegetação, urbanização e unidades
territoriais oficiais para apoiar a identificação de áreas intraurbanas mais
expostas ao calor de superfície no verão de 2023/2024.

## Pergunta central

Quais áreas de Porto Alegre apresentam maior vulnerabilidade térmica urbana
quando combinamos temperatura de superfície, cobertura vegetal, urbanização e
exposição territorial?

## Stack

- Python
- Pandas
- GeoPandas
- Shapely
- PyProj
- Pyogrio
- PyArrow
- GeoJSON/GeoParquet
- Streamlit
- Plotly
- Folium
- streamlit-folium
- Google Earth Engine

## Dados utilizados

- Landsat 8/9 Collection 2 Level 2, período `2023-12-01` a `2024-03-31`.
- Temperatura de superfície (`LST_C`) em graus Celsius.
- Índices espectrais `NDVI`, `NDBI` e `MNDWI`.
- MapBiomas Collection 10, ano 2023.
- Limite municipal de Porto Alegre.
- Bairros oficiais de Porto Alegre, unidade principal do MVP.
- Setores censitários, camada complementar de maior detalhe.

Dados brutos e rasters pesados não devem ser versionados no GitHub. O dashboard
usa apenas outputs processados leves.

## Metodologia resumida

O índice exploratório `UTVI` combina variáveis normalizadas por min-max:

```text
UTVI = mean(LST_median_norm, LST_p75_norm, urban_norm, NDBI_norm, NDVI_inverse_norm)
```

Temperaturas mais altas, maior urbanização e maior `NDBI` aumentam o índice.
Maior `NDVI` reduz o índice por meio do componente invertido
`NDVI_inverse_norm`.

Bairros são a unidade principal de comunicação do MVP. Setores censitários são
uma camada complementar, mais sensível à resolução Landsat de 30 m e dependente
de flags de qualidade.

## Como rodar localmente

Crie e ative um ambiente virtual, depois instale as dependências:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Como rodar o pipeline

Os scripts em `gee/` geram os CSVs exportados manualmente pelo Google Earth
Engine para `data/raw/gee_exports/`. Depois da exportação, rode:

```powershell
python src/run_build_utvi.py
python src/run_build_spatial_dataset.py
python src/run_build_setores_utvi.py
```

## Checagem de prontidão do dashboard

Antes de publicar ou rodar em outro ambiente, valide os inputs processados:

```powershell
python src/check_dashboard_inputs.py
```

A checagem confirma existência dos GeoJSONs e CSVs processados, colunas
essenciais, tamanhos de arquivo, ausência de UTVI nulo nos bairros e flags de
qualidade setoriais.

## Como rodar o dashboard

```powershell
streamlit run app/streamlit_app.py
```

Entrada do app para Streamlit Community Cloud:

```text
app/streamlit_app.py
```

## Principais outputs usados pelo app

- `data/processed/poa_bairros_utvi.geojson`
- `data/processed/poa_setores_utvi.geojson`

Outputs leves de apoio e auditoria:

- `data/processed/poa_bairros_utvi.csv`
- `data/processed/poa_bairros_utvi.geoparquet`
- `data/processed/poa_setores_utvi.csv`
- `data/processed/poa_setores_utvi.geoparquet`
- `outputs/tables/poa_bairros_ranking_utvi_top20.csv`
- `outputs/tables/poa_setores_ranking_utvi_top50.csv`

## Estrutura do repositório

```text
geoclimate-poa/
|-- app/
|   |-- streamlit_app.py
|-- configs/
|   |-- config.yaml
|-- data/
|   |-- interim/
|   |-- processed/
|   |-- raw/
|-- docs/
|   |-- dashboard.md
|   |-- data_sources.md
|   |-- methodology.md
|-- gee/
|   |-- 01_landsat_lst_indices.js
|   |-- 02_zonal_stats_bairros.js
|   |-- 03_zonal_stats_setores.js
|-- outputs/
|   |-- figures/
|   |-- maps/
|   |-- tables/
|-- src/
|   |-- analysis/
|   |-- data/
|   |-- features/
|   |-- visualization/
|       |-- charts.py
|       |-- maps.py
|   |-- check_dashboard_inputs.py
|-- .gitignore
|-- README.md
|-- requirements.txt
```

## Limitações

- O UTVI é exploratório e não é indicador oficial de risco climático,
  vulnerabilidade social ou saúde pública.
- O MVP ainda não incorpora população, renda, idade, saúde ou outras dimensões
  socioeconômicas de vulnerabilidade.
- A camada setorial deve ser interpretada com cautela, especialmente em setores
  pequenos ou com baixa cobertura válida de LST.
- O dashboard não usa banco de dados; os arquivos processados são carregados
  diretamente de `data/processed/`.

## Status

Em desenvolvimento. MVP local preparado para publicação no GitHub e etapa
posterior de deploy no Streamlit Community Cloud.
