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
    "utvi_exploratory": "UTVI exploratório",
    "LST_C_median_mean": "LST mediana média (°C)",
    "LST_C_p75_mean": "LST p75 média (°C)",
    "NDVI_median_mean": "NDVI mediano médio",
    "NDBI_median_mean": "NDBI mediano médio",
    "pct_urbana_land": "% urbano em área terrestre",
    "pct_lst_valid_land": "% LST válida em terra",
}

SETORES_MAP_VARIABLES = {
    "utvi_setor_exploratory": "UTVI setorial exploratório",
    "LST_C_median_mean": "LST mediana média (°C)",
    "NDVI_median_mean": "NDVI mediano médio",
    "pct_urbana_land": "% urbano em área terrestre",
    "pct_lst_valid_land": "% LST válida em terra",
}

LABELS = {
    **BAIRROS_MAP_VARIABLES,
    **SETORES_MAP_VARIABLES,
    "bairro_nome_title": "Bairro",
    "NM_BAIRRO": "Bairro",
    "CD_SETOR": "Setor censitário",
    "utvi_class": "Classe UTVI",
    "utvi_setor_class": "Classe UTVI",
    "quality_flag": "Qualidade",
    "quality_flag_setor": "Qualidade",
}


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


def render_map(
    data: gpd.GeoDataFrame,
    variable: str,
    variable_label: str,
    tooltip_fields: list[str],
    map_key: str,
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
        height=560,
        returned_objects=[],
        key=map_key,
    )


def render_overview(bairros: gpd.GeoDataFrame, setores: gpd.GeoDataFrame | None) -> None:
    """Render the dashboard overview tab."""
    st.title("GeoClimate POA")
    st.subheader("Vulnerabilidade térmica urbana em Porto Alegre")
    st.write(
        "Dashboard exploratório para analisar áreas que combinam maior temperatura "
        "de superfície, menor vegetação, maior urbanização e maior intensidade "
        "espectral de área construída. O índice integra LST, NDVI, NDBI e "
        "percentual urbano em área terrestre."
    )

    top_utvi = bairros.sort_values("utvi_exploratory", ascending=False).iloc[0]
    top_lst = bairros.sort_values("LST_C_median_mean", ascending=False).iloc[0]
    valid_setores = (
        int(setores["quality_flag_setor"].eq("ok").sum())
        if setores is not None and "quality_flag_setor" in setores.columns
        else None
    )

    metric_cols = st.columns(5)
    metric_cols[0].metric("Bairros", f"{len(bairros):,}".replace(",", "."))
    metric_cols[1].metric(
        "Maior UTVI",
        str(top_utvi["bairro_nome_title"]),
        format_metric(top_utvi["utvi_exploratory"]),
    )
    metric_cols[2].metric(
        "Maior LST mediana",
        format_metric(top_lst["LST_C_median_mean"], suffix=" °C"),
        str(top_lst["bairro_nome_title"]),
    )
    metric_cols[3].metric(
        "Média municipal UTVI",
        format_metric(bairros["utvi_exploratory"].mean()),
    )
    metric_cols[4].metric(
        "Setores válidos",
        "n/d" if valid_setores is None else f"{valid_setores:,}".replace(",", "."),
    )

    st.markdown("### Mapa por bairro")
    render_map(
        bairros,
        variable="utvi_exploratory",
        variable_label=BAIRROS_MAP_VARIABLES["utvi_exploratory"],
        tooltip_fields=[
            "bairro_nome_title",
            "utvi_exploratory",
            "utvi_class",
            "LST_C_median_mean",
            "NDVI_median_mean",
            "pct_urbana_land",
            "quality_flag",
        ],
        map_key="overview_bairros_utvi_map",
    )

    st.markdown("### Top 10 bairros por UTVI")
    top10 = bairros.sort_values("utvi_exploratory", ascending=False).head(10)
    st.plotly_chart(
        make_bar_ranking(
            top10,
            label_col="bairro_nome_title",
            value_col="utvi_exploratory",
            title="Ranking de bairros",
            labels=LABELS,
            hover_data=["LST_C_median_mean", "NDVI_median_mean", "pct_urbana_land", "quality_flag"],
        ),
        width="stretch",
    )


def render_bairros(bairros: gpd.GeoDataFrame, selected_bairros: list[str]) -> None:
    """Render the neighborhood analysis tab."""
    st.header("Bairros")
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
        tooltip_fields=[
            "bairro_nome_title",
            variable,
            "utvi_exploratory",
            "utvi_class",
            "LST_C_median_mean",
            "NDVI_median_mean",
            "pct_urbana_land",
            "quality_flag",
        ],
        map_key=f"bairros_{variable}_map",
    )

    st.markdown("### Tabela de bairros")
    query = st.text_input("Filtrar tabela por nome do bairro", key="bairros_query")
    table_data = data.copy()
    if query:
        table_data = table_data[
            table_data["bairro_nome_title"].str.contains(query, case=False, na=False)
        ]
    bairro_table_columns = [
        "utvi_rank",
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
    ]
    st.dataframe(
        table_data[existing_columns(table_data, bairro_table_columns)].sort_values(
            "utvi_exploratory", ascending=False
        ),
        width="stretch",
        hide_index=True,
    )

    left, right = st.columns(2)
    with left:
        st.plotly_chart(
            make_scatter(
                data,
                x="NDVI_median_mean",
                y="LST_C_median_mean",
                hover_name="bairro_nome_title",
                color="utvi_class",
                labels=LABELS,
                hover_data=["utvi_exploratory", "pct_urbana_land", "quality_flag"],
                title="NDVI × LST por bairro",
            ),
            width="stretch",
        )
    with right:
        st.plotly_chart(
            make_scatter(
                data,
                x="pct_urbana_land",
                y="LST_C_median_mean",
                hover_name="bairro_nome_title",
                color="utvi_class",
                labels=LABELS,
                hover_data=["utvi_exploratory", "NDVI_median_mean", "quality_flag"],
                title="% urbano × LST por bairro",
            ),
            width="stretch",
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
    )


def render_setores(setores: gpd.GeoDataFrame | None, selected_bairros: list[str]) -> None:
    """Render the census-sector analysis tab."""
    st.header("Setores censitários")
    st.info(
        "A camada setorial é complementar e mais sensível à escala Landsat de 30 m. "
        "O ranking principal usa apenas setores com quality_flag_setor = ok."
    )

    if setores is None:
        st.warning(f"Camada setorial indisponível. {SETORES_PIPELINE_HINT}")
        return

    bairro_options = sorted(setores["bairro_nome_title"].dropna().unique().tolist())
    default_bairros = [bairro for bairro in selected_bairros if bairro in bairro_options]
    sector_bairros = st.multiselect(
        "Filtrar setores por bairro",
        options=bairro_options,
        default=default_bairros,
        key="setores_bairros",
    )

    flag_option = st.radio(
        "Qualidade dos setores",
        options=[
            "Todos os setores",
            "Apenas setores ok",
            "Setores com cautela",
            "Setores inválidos",
        ],
        horizontal=True,
        key="setores_flag",
    )

    data = filter_by_bairros(setores, sector_bairros)
    if flag_option == "Apenas setores ok":
        data = data[data["quality_flag_setor"].eq("ok")]
    elif flag_option == "Setores com cautela":
        data = data[data["quality_flag_setor"].isin(["caution_low_lst_valid", "caution_small_sector"])]
    elif flag_option == "Setores inválidos":
        data = data[data["quality_flag_setor"].eq("invalid_no_lst")]

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
        tooltip_fields=[
            "CD_SETOR",
            "bairro_nome_title",
            variable,
            "utvi_setor_exploratory",
            "utvi_setor_class",
            "LST_C_median_mean",
            "NDVI_median_mean",
            "pct_urbana_land",
            "pct_lst_valid_land",
            "quality_flag_setor",
        ],
        map_key=f"setores_{variable}_map",
    )

    st.markdown("### Top 20 setores válidos por UTVI")
    valid_ranking = (
        data[data["quality_flag_setor"].eq("ok")]
        .sort_values("utvi_setor_exploratory", ascending=False)
        .head(20)
    )
    st.dataframe(
        valid_ranking[
            existing_columns(
                valid_ranking,
                [
                    "utvi_setor_rank",
                    "CD_SETOR",
                    "bairro_nome_title",
                    "utvi_setor_exploratory",
                    "utvi_setor_class",
                    "quality_flag_setor",
                    "LST_C_median_mean",
                    "NDVI_median_mean",
                    "pct_urbana_land",
                    "pct_lst_valid_land",
                ],
            )
        ],
        width="stretch",
        hide_index=True,
    )

    st.markdown("### Tabela setorial")
    sector_table_columns = [
        "CD_SETOR",
        "bairro_nome_title",
        "utvi_setor_exploratory",
        "utvi_setor_class",
        "quality_flag_setor",
        "LST_C_median_mean",
        "NDVI_median_mean",
        "pct_urbana_land",
        "pct_lst_valid_land",
    ]
    st.dataframe(
        data[existing_columns(data, sector_table_columns)].sort_values(
            "utvi_setor_exploratory", ascending=False, na_position="last"
        ),
        width="stretch",
        hide_index=True,
    )


def render_indicators(bairros: gpd.GeoDataFrame, setores: gpd.GeoDataFrame | None) -> None:
    """Render comparative indicator charts."""
    st.header("Indicadores")

    left, right = st.columns(2)
    with left:
        st.plotly_chart(
            make_scatter(
                bairros,
                x="utvi_exploratory",
                y="NDVI_median_mean",
                hover_name="bairro_nome_title",
                color="utvi_class",
                labels=LABELS,
                hover_data=["LST_C_median_mean", "pct_urbana_land", "quality_flag"],
                title="UTVI × NDVI por bairro",
            ),
            width="stretch",
        )
        st.plotly_chart(
            make_scatter(
                bairros,
                x="LST_C_median_mean",
                y="NDVI_median_mean",
                hover_name="bairro_nome_title",
                color="utvi_class",
                labels=LABELS,
                hover_data=["utvi_exploratory", "pct_urbana_land", "quality_flag"],
                title="LST × NDVI por bairro",
            ),
            width="stretch",
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
                title="UTVI × % urbano por bairro",
            ),
            width="stretch",
        )
        st.plotly_chart(
            make_histogram(
                bairros,
                x="utvi_exploratory",
                title="Distribuição do UTVI por bairros",
                labels=LABELS,
            ),
            width="stretch",
        )

    if setores is not None:
        setores_ok = setores[setores["quality_flag_setor"].eq("ok")]
        st.plotly_chart(
            make_histogram(
                setores_ok,
                x="utvi_setor_exploratory",
                title="Distribuição do UTVI por setores ok",
                labels=LABELS,
                nbins=35,
            ),
            width="stretch",
        )
    else:
        st.warning("Histograma setorial indisponível porque a camada de setores não foi carregada.")


def render_methodology() -> None:
    """Render the methodology tab."""
    st.header("Metodologia")
    st.markdown(
        """
        **Período analisado:** `2023-12-01` a `2024-03-31`.

        **Dados e indicadores:** o processamento usa Landsat 8/9 Collection 2 Level 2,
        temperatura de superfície em °C (`LST_C`), índices espectrais `NDVI`, `NDBI`
        e `MNDWI`, e MapBiomas Collection 10 para o ano de 2023.

        **Unidade principal do MVP:** bairros oficiais de Porto Alegre. A camada de
        setores censitários é complementar e permite observar variações internas aos
        bairros, mas exige cautela por causa da resolução Landsat de 30 m.

        **Fórmula do índice exploratório:**

        ```text
        UTVI = mean(LST_median_norm, LST_p75_norm, urban_norm, NDBI_norm, NDVI_inverse_norm)
        ```

        O UTVI é uma métrica exploratória para diagnóstico e priorização inicial.
        Ele não é um indicador oficial de risco climático, vulnerabilidade social ou
        saúde pública.

        **Flags de qualidade:**

        - `quality_flag`: flag dos bairros, baseada principalmente na cobertura válida de LST.
        - `quality_flag_setor`: flag dos setores, com categorias `ok`,
          `caution_low_lst_valid`, `caution_small_sector` e `invalid_no_lst`.
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
        ["Visão geral", "Bairros", "Setores censitários", "Indicadores", "Metodologia"]
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
