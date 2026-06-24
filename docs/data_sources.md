# Fontes de dados

Este documento lista as fontes usadas na primeira etapa tabular do MVP.

## Exportacao GEE

Arquivo local de entrada por bairro:

```text
data/raw/gee_exports/poa_bairros_zonal_stats_landsat_mapbiomas_2023_2024.csv
```

O CSV foi exportado do Google Earth Engine e contem estatisticas zonais por bairro para Porto Alegre. A tabela validada possui 94 linhas, uma por bairro.

Arquivo local de entrada por setor censitario:

```text
data/raw/gee_exports/poa_setores_zonal_stats_landsat_mapbiomas_2023_2024.csv
```

O CSV setorial foi exportado do Google Earth Engine e contem estatisticas zonais
para 2744 setores censitarios. O campo-chave e `CD_SETOR`, e o campo de bairro
associado e `NM_BAIRRO`.

## Google Earth Engine

Assets e colecoes usadas:

- Limite municipal de Porto Alegre: `projects/rafaelparanhoss/assets/limite_municipal_poa_vigente`
- Bairros de Porto Alegre: `projects/rafaelparanhoss/assets/bairros`
- Setores censitarios de Porto Alegre: `projects/rafaelparanhoss/assets/setores`
- Landsat 8 Collection 2 Level 2: `LANDSAT/LC08/C02/T1_L2`
- Landsat 9 Collection 2 Level 2: `LANDSAT/LC09/C02/T1_L2`
- MapBiomas Collection 10: `projects/mapbiomas-public/assets/brazil/lulc/collection10/mapbiomas_brazil_collection10_coverage_v2`

## Dados vetoriais locais

Camadas locais usadas nos processamentos espaciais:

- Bairros: `data/raw/boundaries/Bairros_LC12112_16.shp`
- Setores censitarios: `data/raw/boundaries/setores_2022_poa.shp`

No shapefile de setores, os campos principais sao:

- `CD_SETOR`: identificador unico do setor censitario.
- `NM_BAIRRO`: bairro associado ao setor.
- `NM_MUN`: municipio.

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
