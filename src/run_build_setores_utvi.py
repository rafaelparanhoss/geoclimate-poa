"""Run the sector-level UTVI build pipeline."""

from pathlib import Path

from data.build_setores_spatial_dataset import (
    build_setores_spatial_dataset,
    enrich_with_geometry_attributes,
)
from data.load_setores_exports import (
    load_validate_clean,
    print_clean_summary,
    save_table,
)
from features.build_setores_index import (
    build_setores_ranking,
    build_setores_utvi,
    print_setores_ranking_summary,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_INPUT = (
    PROJECT_ROOT
    / "data/raw/gee_exports/poa_setores_zonal_stats_landsat_mapbiomas_2023_2024.csv"
)
INTERIM_CSV = PROJECT_ROOT / "data/interim/poa_setores_zonal_stats_clean.csv"
INTERIM_PARQUET = PROJECT_ROOT / "data/interim/poa_setores_zonal_stats_clean.parquet"
PROCESSED_CSV = PROJECT_ROOT / "data/processed/poa_setores_utvi.csv"
PROCESSED_PARQUET = PROJECT_ROOT / "data/processed/poa_setores_utvi.parquet"
TOP50_CSV = PROJECT_ROOT / "outputs/tables/poa_setores_ranking_utvi_top50.csv"

RANKING_COLUMNS = [
    "utvi_setor_rank",
    "CD_SETOR",
    "NM_BAIRRO",
    "NM_MUN",
    "utvi_setor_exploratory",
    "utvi_setor_class",
    "quality_flag_setor",
    "LST_C_median_mean",
    "LST_C_p75_mean",
    "pct_urbana_land",
    "NDVI_median_mean",
    "NDBI_median_mean",
    "pct_lst_valid_land",
    "area_land_ha",
    "n_pixels_land_aprox",
]


def main() -> None:
    """Execute the complete sector-level tabular and spatial pipeline."""
    print("Iniciando pipeline UTVI setorial exploratorio")
    print(f"Entrada: {RAW_INPUT}")

    clean_data, invalid_counts = load_validate_clean(RAW_INPUT)
    save_table(clean_data, INTERIM_CSV)
    save_table(clean_data, INTERIM_PARQUET)
    print_clean_summary(clean_data, invalid_counts)

    utvi_data = build_setores_utvi(clean_data)
    utvi_data = enrich_with_geometry_attributes(utvi_data)
    save_table(utvi_data, PROCESSED_CSV)
    save_table(utvi_data, PROCESSED_PARQUET)

    ranking = build_setores_ranking(utvi_data)
    top50 = ranking[RANKING_COLUMNS].head(50)
    save_table(top50, TOP50_CSV)
    print_setores_ranking_summary(utvi_data, top_n=20)

    build_setores_spatial_dataset()

    print("Arquivos gerados:")
    print(f"- {INTERIM_CSV}")
    print(f"- {INTERIM_PARQUET}")
    print(f"- {PROCESSED_CSV}")
    print(f"- {PROCESSED_PARQUET}")
    print(f"- {TOP50_CSV}")
    print("- data/processed/poa_setores_utvi.geojson")
    print("- data/processed/poa_setores_utvi.geoparquet")
    print("Pipeline setorial concluido.")


if __name__ == "__main__":
    main()
