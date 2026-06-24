# Dashboard Streamlit

O dashboard MVP do `geoclimate-poa` apresenta os resultados processados de
vulnerabilidade térmica urbana em Porto Alegre sem depender de banco de dados ou
serviços externos.

## Como executar

```powershell
streamlit run app/streamlit_app.py
```

O app deve ser executado a partir da raiz do repositório.

## Dados carregados pelo app

O dashboard carrega diretamente as camadas espaciais processadas:

- `data/processed/poa_bairros_utvi.geojson`
- `data/processed/poa_setores_utvi.geojson`

Os rankings e tabelas processadas seguem disponíveis como outputs leves de
apoio e auditoria:

- `data/processed/poa_bairros_utvi.csv`
- `data/processed/poa_setores_utvi.csv`
- `outputs/tables/poa_bairros_ranking_utvi_top20.csv`
- `outputs/tables/poa_setores_ranking_utvi_top50.csv`

Os dados brutos em `data/raw/` não são usados pelo app.

## Abas

- **Visão geral:** métricas sintéticas, mapa por bairro e ranking top 10.
- **Bairros:** mapa coroplético, tabela filtrável e gráficos de relação entre
  vegetação, urbanização, LST e UTVI.
- **Setores censitários:** camada complementar com filtros por bairro e por
  flag de qualidade.
- **Indicadores:** gráficos comparativos simples para bairros e setores válidos.
- **Metodologia:** resumo do período, fontes, fórmula do índice e limitações.

## Limitações do MVP

O UTVI é exploratório e não deve ser interpretado como indicador oficial de
risco climático, vulnerabilidade social ou saúde pública. A camada setorial é
mais sensível à resolução Landsat de 30 m; por isso o ranking principal usa
apenas setores com `quality_flag_setor = ok`.
