# Metodologia

Este documento resume a metodologia inicial do MVP do projeto `geoclimate-poa`.

## Unidade espacial

A unidade espacial desta etapa e o bairro de Porto Alegre. O arquivo de bairros foi processado no Google Earth Engine e dissolvido pelo campo `NOME`, resultando em 94 bairros unicos.

## Indicadores de entrada

Os indicadores tabulares por bairro foram gerados no Google Earth Engine a partir de:

- Landsat 8/9 Collection 2 Level 2, periodo `2023-12-01` a `2024-03-31`.
- Temperatura de superficie em Celsius (`LST_C`).
- Indices espectrais `NDVI`, `NDBI` e `MNDWI`.
- MapBiomas Collection 10, ano 2023, para estimar areas urbana, vegetada e agua.

## UTVI exploratorio

Nesta etapa foi criado um indice exploratorio chamado `utvi_exploratory`.

O indice usa normalizacao min-max de 0 a 1 e combina cinco componentes:

- `LST_C_median_mean`: maior temperatura aumenta vulnerabilidade.
- `LST_C_p75_mean`: maior temperatura no percentil 75 aumenta vulnerabilidade.
- `pct_urbana_land`: maior proporcao urbana em area terrestre aumenta vulnerabilidade.
- `NDBI_median_mean`: maior NDBI aumenta vulnerabilidade.
- `NDVI_median_mean`: maior NDVI reduz vulnerabilidade, por isso e usado de forma invertida.

Formula:

```text
utvi_exploratory = mean(
  lst_median_norm,
  lst_p75_norm,
  urban_norm,
  ndbi_norm,
  ndvi_inverse_norm
)
```

As classes do indice usam cortes fixos:

- 0.00 a 0.20: muito baixa
- 0.20 a 0.40: baixa
- 0.40 a 0.60: media
- 0.60 a 0.80: alta
- 0.80 a 1.00: muito alta

## Qualidade

A coluna `quality_flag` sinaliza a cobertura valida de LST em area terrestre:

- `ok`: `pct_lst_valid_land >= 80`
- `caution_low_lst_valid`: `pct_lst_valid_land < 80`

Esse alerta nao entra no calculo do indice nesta etapa.

## Setores censitarios como camada complementar

Os bairros seguem como unidade principal do MVP, pois oferecem uma escala mais
estavel para comunicacao publica e comparacao intraurbana.

Os setores censitarios serao tratados como camada complementar de maior detalhe.
Essa escala pode revelar variacoes internas aos bairros, mas tambem exige mais
cuidado metodologico: muitos setores sao pequenos em relacao a resolucao
Landsat de 30 m, o que pode gerar estatisticas instaveis quando ha poucos
pixels validos por setor.

A interpretacao setorial dependera de flags de qualidade, especialmente
cobertura valida de LST, area terrestre analisavel e numero aproximado de pixels
Landsat por setor. Nesta etapa, ainda nao ha processamento socioeconomico
censitario.

## Observacao

O UTVI e uma metrica exploratoria para priorizacao inicial e diagnostico. Ele ainda nao incorpora exposicao populacional, sensibilidade socioeconomica ou validacao estatistica externa.
