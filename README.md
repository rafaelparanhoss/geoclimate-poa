# geoclimate-poa

Projeto geoespacial para análise de vulnerabilidade térmica urbana em Porto Alegre, Rio Grande do Sul.

## Objetivo

Construir um MVP publicável em GitHub e Streamlit para identificar áreas de Porto Alegre que combinam maior temperatura de superfície, menor vegetação, maior urbanização e maior exposição populacional.

## Pergunta central

Quais áreas de Porto Alegre apresentam maior vulnerabilidade térmica urbana quando combinamos temperatura de superfície, cobertura vegetal, urbanização e exposição populacional?

## Stack inicial

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

## Estrutura do repositório

```text
geoclimate-poa/
+-- app/
|   +-- streamlit_app.py
+-- configs/
|   +-- config.yaml
+-- data/
|   +-- interim/
|   |   +-- README.md
|   +-- processed/
|   |   +-- README.md
|   +-- raw/
|       +-- README.md
+-- docs/
|   +-- dashboard.md
|   +-- data_sources.md
|   +-- methodology.md
+-- gee/
|   +-- 01_landsat_lst_indices.js
|   +-- 02_zonal_stats_bairros.js
+-- outputs/
|   +-- figures/
|   +-- maps/
|   +-- tables/
+-- src/
|   +-- analysis/
|   |   +-- ranking.py
|   +-- data/
|   |   +-- load_gee_exports.py
|   |   +-- prepare_boundaries.py
|   +-- features/
|   |   +-- build_index.py
|   +-- visualization/
|       +-- maps.py
+-- .gitignore
+-- README.md
+-- requirements.txt
```

## Status

Em desenvolvimento.
