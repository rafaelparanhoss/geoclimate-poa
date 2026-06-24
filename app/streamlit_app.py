"""Streamlit dashboard MVP for GeoClimate POA."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable

import geopandas as gpd
import pandas as pd
import streamlit as st

try:
    from streamlit_folium import st_folium
except ImportError:  # pragma: no cover - handled at runtime in the app
    st_folium = None


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.visualization.charts import (  # noqa: E402
    make_bar_ranking,
    make_histogram,
    make_scatter,
)
from src.visualization.maps import make_choropleth_map  # noqa: E402


BAIRROS_GEOJSON = PROJECT_ROOT / "data" / "processed" / "poa_bairros_utvi.geojson"
SETORES_GEOJSON = PROJECT_ROOT / "data" / "processed" / "poa_setores_utvi.geojson"

BAIRROS_PIPELINE_HINT = "Rode: python src/run_build_spatial_dataset.py"
SETORES_PIPELINE_HINT = "Rode: python src/run_build_setores_utvi.py"

BAIRROS_REQUIRED_COLUMNS = [
    "bairro_nome_title",
    "utvi_exploratory",
    "utvi_class",
    "quality_flag",
    "LST_C_median_mean",
    "LST_C_p75_mean",
    "NDVI_median_mean",
    "NDBI_median_mean",
    "pct_urbana_land",
    "pct_lst_valid_land",
    "geometry",
]

SETORES_REQUIRED_COLUMNS = [
    "CD_SETOR",
    "NM_BAIRRO",
    "bairro_nome_title",
    "utvi_setor_exploratory",
    "utvi_setor_class",
    "quality_flag_setor",
    "LST_C_median_mean",
    "NDVI_median_mean",
    "pct_urbana_land",
    "pct_lst_valid_land",
    "geometry",
]

BAIRROS_MAP_VARIABLES = {
    "utvi_exploratory": "UTVI",
    "LST_C_median_mean": "Temperatura de superfície mediana média (°C)",
    "LST_C_p75_mean": "Temperatura de superfície p75 média (°C)",
    "NDVI_median_mean": "Vegetação média (NDVI)",
    "NDBI_median_mean": "Urbanização espectral média (NDBI)",
    "pct_urbana_land": "Área urbana (%)",
    "pct_lst_valid_land": "LST válida (%)",
}

SETORES_MAP_VARIABLES = {
    "utvi_setor_exploratory": "UTVI",
    "LST_C_median_mean": "Temperatura de superfície mediana média (°C)",
    "NDVI_median_mean": "Vegetação média (NDVI)",
    "pct_urbana_land": "Área urbana (%)",
    "pct_lst_valid_land": "LST válida (%)",
}

LABELS = {
    **BAIRROS_MAP_VARIABLES,
    **SETORES_MAP_VARIABLES,
    "bairro_nome_title": "Bairro",
    "NM_BAIRRO": "Bairro",
    "CD_SETOR": "CD_SETOR",
    "utvi_class": "Classe UTVI",
    "utvi_setor_class": "Classe UTVI",
    "quality_flag": "Qualidade",
    "quality_flag_setor": "quality_flag_setor",
    "utvi_rank": "Ranking UTVI",
    "utvi_setor_rank": "Ranking UTVI",
}

BAIRROS_TOOLTIP_FIELDS = [
    "bairro_nome_title",
    "utvi_exploratory",
    "utvi_class",
    "LST_C_median_mean",
    "NDVI_median_mean",
    "pct_urbana_land",
    "quality_flag",
]

SETORES_TOOLTIP_FIELDS = [
    "CD_SETOR",
    "bairro_nome_title",
    "utvi_setor_exploratory",
    "utvi_setor_class",
    "LST_C_median_mean",
    "NDVI_median_mean",
    "pct_urbana_land",
    "quality_flag_setor",
]

BAIRROS_TABLE_COLUMNS = [
    "utvi_rank",
    "bairro_nome_title",
    "utvi_exploratory",
    "utvi_class",
    "LST_C_median_mean",
    "LST_C_p75_mean",
    "NDVI_median_mean",
    "NDBI_median_mean",
    "pct_urbana_land",
    "pct_lst_valid_land",
    "quality_flag",
]

SETORES_TABLE_COLUMNS = [
    "utvi_setor_rank",
    "CD_SETOR",
    "bairro_nome_title",
    "utvi_setor_exploratory",
    "utvi_setor_class",
    "LST_C_median_mean",
    "NDVI_median_mean",
    "pct_urbana_land",
    "pct_lst_valid_land",
    "quality_flag_setor",
]


def format_metric(value: object, decimals: int = 2, suffix: str = "") -> str:
    """Format numeric metrics with a fallback for missing values."""
    if value is None or pd.isna(value):
        return "n/d"
    if isinstance(value, str):
        return value
    return f"{float(value):,.{decimals}f}{suffix}".replace(",", "X").replace(".", ",").replace("X", ".")


def validate_columns(data: pd.DataFrame, required_columns: Iterable[str], dataset_name: str) -> None:
    """Raise a clear error when expected columns are missing."""
    missing = [column for column in required_columns if column not in data.columns]
    if missing:
        missing_text = ", ".join(missing)
        raise ValueError(f"{dataset_name} sem colunas obrigatórias: {missing_text}")


def require_file(path: Path, hint: str) -> None:
    """Validate that a processed file exists before loading it."""
    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {path}. {hint}")


@st.cache_data(show_spinner="Carregando bairros processados...")
def load_bairros_data() -> gpd.GeoDataFrame:
    """Load the processed neighborhood GeoJSON."""
    require_file(BAIRROS_GEOJSON, BAIRROS_PIPELINE_HINT)
    data = gpd.read_file(BAIRROS_GEOJSON)
    validate_columns(data, BAIRROS_REQUIRED_COLUMNS, "Camada de bairros")
    return data


@st.cache_data(show_spinner="Carregando setores processados...")
def load_setores_data() -> gpd.GeoDataFrame:
    """Load the processed census-sector GeoJSON."""
    require_file(SETORES_GEOJSON, SETORES_PIPELINE_HINT)
    data = gpd.read_file(SETORES_GEOJSON)
    validate_columns(data, SETORES_REQUIRED_COLUMNS, "Camada de setores")
    return data


def existing_columns(data: pd.DataFrame, columns: Iterable[str]) -> list[str]:
    """Return the subset of columns that exists in a DataFrame."""
    existing: list[str] = []
    for column in columns:
        if column in data.columns and column not in existing:
            existing.append(column)
    return existing


def filter_by_bairros(data: pd.DataFrame, selected_bairros: list[str]) -> pd.DataFrame:
    """Filter a DataFrame using the standardized neighborhood title column."""
    if not selected_bairros or "bairro_nome_title" not in data.columns:
        return data
    return data[data["bairro_nome_title"].isin(selected_bairros)].copy()


def round_for_display(data: pd.DataFrame) -> pd.DataFrame:
    """Round visible numeric columns without changing the stored data."""
    display = data.copy()
    for column in display.columns:
        if column in ["utvi_exploratory", "utvi_setor_exploratory"]:
            display[column] = pd.to_numeric(display[column], errors="coerce").round(3)
        elif column.startswith("LST_") or column.startswith("pct_"):
            display[column] = pd.to_numeric(display[column], errors="coerce").round(1)
        elif "NDVI" in column or "NDBI" in column or "MNDWI" in column:
            display[column] = pd.to_numeric(display[column], errors="coerce").round(3)
    return display


def friendly_table(data: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Select, round and rename table columns for the dashboard."""
    selected = data[existing_columns(data, columns)].copy()
    selected = selected.drop(columns=["geometry"], errors="ignore")
    selected = round_for_display(selected)
    return selected.rename(columns=LABELS)


def download_table(data: pd.DataFrame, filename: str, label: str) -> None:
    """Render a CSV download button for a filtered table."""
    export = data.drop(columns=["geometry"], errors="ignore").copy()
    csv = export.to_csv(index=False).encode("utf-8")
    st.download_button(
        label=label,
        data=csv,
        file_name=filename,
        mime="text/csv",
    )


def render_map(
    data: gpd.GeoDataFrame,
    variable: str,
    variable_label: str,
    tooltip_fields: list[str],
    map_key: str,
    height: int = 590,
) -> None:
    """Render a Folium choropleth in Streamlit."""
    if st_folium is None:
        st.error("streamlit-folium não está instalado. Rode: pip install streamlit-folium")
        return
    if data.empty:
        st.info("Nenhuma feição disponível para o filtro atual.")
        return

    folium_map = make_choropleth_map(
        data=data,
        variable=variable,
        variable_label=variable_label,
        tooltip_fields=existing_columns(data, tooltip_fields),
        tooltip_aliases=LABELS,
    )
    st_folium(
        folium_map,
        width=1400,
        height=height,
        returned_objects=[],
        key=map_key,
    )


def render_overview(bairros: gpd.GeoDataFrame, setores: gpd.GeoDataFrame | None) -> None:
    """Render the dashboard overview tab."""
    st.title("GeoClimate POA")
    st.subheader("Vulnerabilidade térmica urbana em Porto Alegre")
    st.markdown(
        """
        **Pergunta central:** quais áreas combinam maior temperatura de superfície,
        menor vegetação e maior urbanização?

        Este painel organiza os resultados por bairros e, como camada complementar,
        por setores censitários. O índice UTVI é exploratório e ajuda a comparar
        padrões espaciais de calor de superfície no verão de 2023/2024.
        """
    )

    top_utvi = bairros.sort_values("utvi_exploratory", ascending=False).iloc[0]
    top_lst = bairros.sort_values("LST_C_median_mean", ascending=False).iloc[0]
    valid_setores = (
        int(setores["quality_flag_setor"].eq("ok").sum())
        if setores is not None and "quality_flag_setor" in setores.columns
        else None
    )

    metric_cols = st.columns(5)
    metric_cols[0].metric(
        "Bairro com maior UTVI",
        str(top_utvi["bairro_nome_title"]),
        format_metric(top_utvi["utvi_exploratory"], decimals=3),
    )
    metric_cols[1].metric(
        "Maior temperatura média",
        str(top_lst["bairro_nome_title"]),
        format_metric(top_lst["LST_C_median_mean"], decimals=1, suffix=" °C"),
    )
    metric_cols[2].metric("Bairros", f"{len(bairros):,}".replace(",", "."))
    metric_cols[3].metric(
        "Setores válidos",
        "n/d" if valid_setores is None else f"{valid_setores:,}".replace(",", "."),
    )
    metric_cols[4].metric(
        "Média do UTVI",
        format_metric(bairros["utvi_exploratory"].mean(), decimals=3),
    )

    st.markdown("### Mapa de UTVI por bairro")
    render_map(
        bairros,
        variable="utvi_exploratory",
        variable_label="UTVI",
        tooltip_fields=BAIRROS_TOOLTIP_FIELDS,
        map_key="overview_bairros_utvi_map",
        height=620,
    )

    st.markdown("### Ranking top 10 bairros")
    top10 = bairros.sort_values("utvi_exploratory", ascending=False).head(10)
    st.plotly_chart(
        make_bar_ranking(
            top10,
            label_col="bairro_nome_title",
            value_col="utvi_exploratory",
            title="Bairros com maior UTVI",
            labels=LABELS,
            hover_data=["LST_C_median_mean", "NDVI_median_mean", "pct_urbana_land", "quality_flag"],
        ),
        width="stretch",
        key="overview_top10_bairros_chart",
    )


def render_bairros(bairros: gpd.GeoDataFrame, selected_bairros: list[str]) -> None:
    """Render the neighborhood exploration tab."""
    st.header("Explorar bairros")
    st.caption("Bairros são a unidade principal do MVP e a escala recomendada para leitura inicial.")

    data = filter_by_bairros(bairros, selected_bairros)

    variable = st.selectbox(
        "Variável do mapa",
        options=list(BAIRROS_MAP_VARIABLES),
        format_func=BAIRROS_MAP_VARIABLES.get,
        key="bairros_map_variable",
    )
    render_map(
        data,
        variable=variable,
        variable_label=BAIRROS_MAP_VARIABLES[variable],
        tooltip_fields=BAIRROS_TOOLTIP_FIELDS,
        map_key=f"bairros_{variable}_map",
    )

    st.markdown("### Ranking e tabela")
    query = st.text_input("Filtrar por nome do bairro", key="bairros_query")
    table_data = data.copy()
    if query:
        table_data = table_data[
            table_data["bairro_nome_title"].str.contains(query, case=False, na=False)
        ]
    table_data = table_data.sort_values("utvi_exploratory", ascending=False)
    st.dataframe(
        friendly_table(table_data, BAIRROS_TABLE_COLUMNS),
        width="stretch",
        hide_index=True,
    )
    download_table(
        table_data[existing_columns(table_data, BAIRROS_TABLE_COLUMNS)],
        "geoclimate_poa_bairros_filtrados.csv",
        "Baixar tabela de bairros em CSV",
    )

    st.plotly_chart(
        make_bar_ranking(
            data,
            label_col="bairro_nome_title",
            value_col="utvi_exploratory",
            title="Top 15 bairros por UTVI",
            labels=LABELS,
            top_n=15,
            hover_data=["LST_C_median_mean", "NDVI_median_mean", "pct_urbana_land", "quality_flag"],
        ),
        width="stretch",
        key="bairros_top15_chart",
    )


def render_setores(setores: gpd.GeoDataFrame | None, selected_bairros: list[str]) -> None:
    """Render the census-sector exploration tab."""
    st.header("Explorar setores")
    st.info(
        "Setores censitários oferecem maior detalhe espacial, mas podem ser mais sensíveis "
        "à resolução Landsat de 30 m. O ranking principal considera apenas setores com "
        "quality_flag_setor = ok."
    )

    if setores is None:
        st.warning(f"Camada setorial indisponível. {SETORES_PIPELINE_HINT}")
        return

    bairro_options = sorted(setores["bairro_nome_title"].dropna().unique().tolist())
    default_bairros = [bairro for bairro in selected_bairros if bairro in bairro_options]
    filter_cols = st.columns(3)

    with filter_cols[0]:
        sector_bairros = st.multiselect(
            "Bairro",
            options=bairro_options,
            default=default_bairros,
            key="setores_bairros",
        )
    with filter_cols[1]:
        flag_options = sorted(setores["quality_flag_setor"].dropna().unique().tolist())
        selected_flags = st.multiselect(
            "quality_flag_setor",
            options=flag_options,
            default=["ok"] if "ok" in flag_options else flag_options,
            key="setores_flags",
        )
    with filter_cols[2]:
        class_options = sorted(setores["utvi_setor_class"].dropna().unique().tolist())
        selected_classes = st.multiselect(
            "Classe UTVI",
            options=class_options,
            default=class_options,
            key="setores_classes",
        )

    data = filter_by_bairros(setores, sector_bairros)
    if selected_flags:
        data = data[data["quality_flag_setor"].isin(selected_flags)]
    if selected_classes:
        data = data[data["utvi_setor_class"].isin(selected_classes)]

    variable = st.selectbox(
        "Variável do mapa setorial",
        options=list(SETORES_MAP_VARIABLES),
        format_func=SETORES_MAP_VARIABLES.get,
        key="setores_map_variable",
    )
    render_map(
        data,
        variable=variable,
        variable_label=SETORES_MAP_VARIABLES[variable],
        tooltip_fields=SETORES_TOOLTIP_FIELDS,
        map_key=f"setores_{variable}_map",
    )

    st.markdown("### Ranking top 20 setores válidos")
    valid_ranking = (
        data[data["quality_flag_setor"].eq("ok")]
        .sort_values("utvi_setor_exploratory", ascending=False)
        .head(20)
    )
    st.dataframe(
        friendly_table(valid_ranking, SETORES_TABLE_COLUMNS),
        width="stretch",
        hide_index=True,
    )

    st.markdown("### Tabela setorial filtrada")
    table_data = data.sort_values("utvi_setor_exploratory", ascending=False, na_position="last")
    st.dataframe(
        friendly_table(table_data, SETORES_TABLE_COLUMNS),
        width="stretch",
        hide_index=True,
    )
    download_table(
        table_data[existing_columns(table_data, SETORES_TABLE_COLUMNS)],
        "geoclimate_poa_setores_filtrados.csv",
        "Baixar tabela de setores em CSV",
    )


def render_indicators(bairros: gpd.GeoDataFrame, setores: gpd.GeoDataFrame | None) -> None:
    """Render comparative indicator charts."""
    st.header("Indicadores")
    st.caption("Gráficos sintéticos para apoiar a leitura do mapa e dos rankings.")

    left, right = st.columns(2)
    with left:
        st.plotly_chart(
            make_scatter(
                bairros,
                x="LST_C_median_mean",
                y="NDVI_median_mean",
                hover_name="bairro_nome_title",
                color="utvi_class",
                labels=LABELS,
                hover_data=["utvi_exploratory", "pct_urbana_land", "quality_flag"],
                title="Temperatura de superfície × vegetação por bairro",
            ),
            width="stretch",
            key="indicadores_lst_ndvi_chart",
        )
    with right:
        st.plotly_chart(
            make_scatter(
                bairros,
                x="utvi_exploratory",
                y="pct_urbana_land",
                hover_name="bairro_nome_title",
                color="utvi_class",
                labels=LABELS,
                hover_data=["LST_C_median_mean", "NDVI_median_mean", "quality_flag"],
                title="UTVI × área urbana por bairro",
            ),
            width="stretch",
            key="indicadores_utvi_urbano_chart",
        )

    st.plotly_chart(
        make_bar_ranking(
            bairros,
            label_col="bairro_nome_title",
            value_col="utvi_exploratory",
            title="Top 15 bairros por UTVI",
            labels=LABELS,
            top_n=15,
            hover_data=["LST_C_median_mean", "NDVI_median_mean", "pct_urbana_land", "quality_flag"],
        ),
        width="stretch",
        key="indicadores_top15_bairros_chart",
    )

    if setores is not None:
        setores_ok = setores[setores["quality_flag_setor"].eq("ok")]
        st.plotly_chart(
            make_histogram(
                setores_ok,
                x="utvi_setor_exploratory",
                title="Distribuição de UTVI nos setores ok",
                labels=LABELS,
                nbins=35,
            ),
            width="stretch",
            key="indicadores_setores_ok_hist_chart",
        )
    else:
        st.warning("Histograma setorial indisponível porque a camada de setores não foi carregada.")


def render_methodology() -> None:
    """Render the methodology tab."""
    st.header("Metodologia")
    st.warning(
        "O UTVI é exploratório e não representa um indicador oficial de risco climático "
        "ou vulnerabilidade social."
    )

    with st.expander("Dados usados", expanded=True):
        st.markdown(
            """
            - Período analisado: `2023-12-01` a `2024-03-31`.
            - Landsat 8/9 Collection 2 Level 2.
            - Temperatura de superfície em °C (`LST_C`).
            - Índices espectrais `NDVI`, `NDBI` e `MNDWI`.
            - MapBiomas Collection 10, ano 2023.
            - Bairros oficiais como unidade principal.
            - Setores censitários como camada complementar.
            """
        )

    with st.expander("Fórmula do índice"):
        st.markdown(
            """
            ```text
            UTVI = mean(LST_median_norm, LST_p75_norm, urban_norm, NDBI_norm, NDVI_inverse_norm)
            ```

            Temperaturas mais altas, maior urbanização e maior NDBI aumentam o índice.
            Maior NDVI reduz o índice por meio do componente invertido.
            """
        )

    with st.expander("Interpretação das quality flags"):
        st.markdown(
            """
            - `quality_flag`: flag dos bairros, baseada principalmente na cobertura válida de LST.
            - `quality_flag_setor = ok`: setor apto ao ranking exploratório principal.
            - `caution_low_lst_valid`: baixa cobertura válida de LST.
            - `caution_small_sector`: setor pequeno ou com poucos pixels Landsat.
            - `invalid_no_lst`: setor sem LST válida; não entra no ranking principal.
            """
        )

    with st.expander("Limitações"):
        st.markdown(
            """
            - O UTVI não incorpora população, renda, idade, saúde ou outras dimensões sociais.
            - A resolução Landsat de 30 m pode gerar instabilidade em setores pequenos.
            - O dashboard compara padrões espaciais do período analisado; não substitui análise
              climática, epidemiológica ou socioeconômica dedicada.
            """
        )


def main() -> None:
    """Run the Streamlit dashboard."""
    st.set_page_config(
        page_title="GeoClimate POA",
        layout="wide",
    )

    try:
        bairros = load_bairros_data()
    except (FileNotFoundError, ValueError) as error:
        st.error(str(error))
        st.stop()

    try:
        setores = load_setores_data()
    except (FileNotFoundError, ValueError) as error:
        setores = None
        st.sidebar.warning(str(error))

    with st.sidebar:
        st.title("GeoClimate POA")
        st.caption("Filtros gerais")
        bairro_options = sorted(bairros["bairro_nome_title"].dropna().unique().tolist())
        selected_bairros = st.multiselect(
            "Bairros em destaque",
            options=bairro_options,
            help="Se nenhum bairro for selecionado, o app mostra todos.",
        )
        st.divider()
        st.write("Dados carregados")
        st.write(f"- Bairros: {len(bairros)}")
        st.write(
            f"- Setores: {len(setores) if setores is not None else 'indisponível'}"
        )

    tab_overview, tab_bairros, tab_setores, tab_indicators, tab_methodology = st.tabs(
        ["Visão geral", "Explorar bairros", "Explorar setores", "Indicadores", "Metodologia"]
    )

    with tab_overview:
        render_overview(bairros, setores)
    with tab_bairros:
        render_bairros(bairros, selected_bairros)
    with tab_setores:
        render_setores(setores, selected_bairros)
    with tab_indicators:
        render_indicators(bairros, setores)
    with tab_methodology:
        render_methodology()


if __name__ == "__main__":
    main()
