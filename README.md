# geoclimate-poa

Projeto geoespacial para análise de vulnerabilidade térmica urbana em Porto
Alegre, Rio Grande do Sul.

## Objetivo

Construir um MVP publicável em GitHub e Streamlit para identificar áreas de
Porto Alegre que combinam maior temperatura de superfície, menor vegetação,
maior urbanização e maior exposição populacional.

## Pergunta central

Quais áreas de Porto Alegre apresentam maior vulnerabilidade térmica urbana
quando combinamos temperatura de superfície, cobertura vegetal, urbanização e
exposição populacional?

## Stack

- Python
- GeoPandas
- Pandas
- DuckDB
- Parquet/GeoParquet
- Streamlit
- Plotly
- Folium
- streamlit-folium
- Google Earth Engine

## Como rodar o pipeline

Os scripts GEE em `gee/` geram os CSVs exportados para `data/raw/gee_exports/`.
Depois da exportação manual pelo Google Earth Engine, rode os scripts Python a
partir da raiz do repositório:

```powershell
python src/run_build_utvi.py
python src/run_build_spatial_dataset.py
python src/run_build_setores_utvi.py
```

## Como rodar o dashboard

```powershell
streamlit run app/streamlit_app.py
```

O dashboard usa apenas arquivos processados leves em `data/processed/` e
`outputs/tables/`.

## Principais outputs usados pelo app

- `data/processed/poa_bairros_utvi.geojson`
- `data/processed/poa_setores_utvi.geojson`

Outros outputs leves gerados pelo pipeline:

- `data/processed/poa_bairros_utvi.geoparquet`
- `data/processed/poa_bairros_utvi.csv`
- `data/processed/poa_setores_utvi.geoparquet`
- `data/processed/poa_setores_utvi.csv`
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
|-- .gitignore
|-- README.md
|-- requirements.txt
```

## Status

Em desenvolvimento.
