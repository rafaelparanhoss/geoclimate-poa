# Dashboard Streamlit

O dashboard MVP do `geoclimate-poa` apresenta os resultados processados de
vulnerabilidade térmica urbana em Porto Alegre sem depender de banco de dados,
APIs externas ou dados brutos em tempo de execução.

## Execução local

```powershell
streamlit run app/streamlit_app.py
```

O app deve ser executado a partir da raiz do repositório.

## Arquivos consumidos pelo app

O dashboard carrega diretamente as camadas espaciais processadas:

- `data/processed/poa_bairros_utvi.geojson`
- `data/processed/poa_setores_utvi.geojson`

Também são mantidos como outputs leves de apoio e auditoria:

- `data/processed/poa_bairros_utvi.csv`
- `data/processed/poa_setores_utvi.csv`
- `outputs/tables/poa_bairros_ranking_utvi_top20.csv`
- `outputs/tables/poa_setores_ranking_utvi_top50.csv`

Os dados brutos em `data/raw/` e os dados intermediários em `data/interim/` não
são usados pelo dashboard.

## Abas

- **Visão geral:** título do projeto, métricas sintéticas, mapa coroplético por
  bairro e ranking top 10 por UTVI.
- **Bairros:** mapa por variável selecionada, tabela filtrável, dispersões entre
  NDVI, urbanização e LST, e barras top 15 por UTVI.
- **Setores censitários:** camada complementar com filtro por bairro, filtro por
  qualidade e ranking top 20 de setores válidos.
- **Indicadores:** gráficos comparativos simples para bairros e distribuição do
  UTVI por bairros e setores `ok`.
- **Metodologia:** resumo do período, fontes, fórmula do índice, flags de
  qualidade e limitações de interpretação.

## Unidade espacial

Bairros são a unidade principal do MVP porque oferecem uma escala mais estável
para comunicação pública e comparação intraurbana.

Setores censitários são camada complementar de maior detalhe. A interpretação
setorial exige cautela porque muitos setores são pequenos em relação à resolução
Landsat de 30 m. O ranking setorial principal considera apenas setores com
`quality_flag_setor = ok`.

## Índice exploratório

O UTVI combina variáveis normalizadas por min-max:

```text
UTVI = mean(LST_median_norm, LST_p75_norm, urban_norm, NDBI_norm, NDVI_inverse_norm)
```

O índice é exploratório. Ele não é um indicador oficial de risco climático,
vulnerabilidade social ou saúde pública.

## Checagem antes de publicar

```powershell
python src/check_dashboard_inputs.py
```

Essa rotina valida existência dos GeoJSONs e CSVs processados, colunas
essenciais, tamanho dos arquivos, UTVI dos bairros e flags de qualidade dos
setores.
