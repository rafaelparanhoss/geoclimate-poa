# Fontes de dados

Este documento lista as fontes usadas na primeira etapa tabular do MVP.

## Exportacao GEE

Arquivo local de entrada:

```text
data/raw/gee_exports/poa_bairros_zonal_stats_landsat_mapbiomas_2023_2024.csv
```

O CSV foi exportado do Google Earth Engine e contem estatisticas zonais por bairro para Porto Alegre. A tabela validada possui 94 linhas, uma por bairro.

## Google Earth Engine

Assets e colecoes usadas:

- Limite municipal de Porto Alegre: `projects/rafaelparanhoss/assets/limite_municipal_poa_vigente`
- Bairros de Porto Alegre: `projects/rafaelparanhoss/assets/bairros`
- Landsat 8 Collection 2 Level 2: `LANDSAT/LC08/C02/T1_L2`
- Landsat 9 Collection 2 Level 2: `LANDSAT/LC09/C02/T1_L2`
- MapBiomas Collection 10: `projects/mapbiomas-public/assets/brazil/lulc/collection10/mapbiomas_brazil_collection10_coverage_v2`

## Periodo

Periodo Landsat usado nesta etapa:

```text
2023-12-01 a 2024-03-31
```

## Variaveis derivadas

O processamento GEE gerou indicadores de:

- Temperatura de superficie (`LST_C`).
- Vegetacao (`NDVI`).
- Urbanizacao espectral (`NDBI`).
- Agua e umidade superficial (`MNDWI`).
- Areas urbana, vegetada e agua a partir do MapBiomas 2023.
- Cobertura valida de LST por bairro.
