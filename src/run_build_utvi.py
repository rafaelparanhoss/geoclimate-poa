"""Run the tabular UTVI build pipeline."""

from pathlib import Path

from analysis.ranking import (
    build_utvi_ranking,
    print_ranking_summary,
    save_ranking,
    select_top_units,
)
from data.load_gee_exports import load_validate_clean, print_clean_summary, save_table
from features.build_index import build_utvi


PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_INPUT = PROJECT_ROOT / "data/raw/gee_exports/poa_bairros_zonal_stats_landsat_mapbiomas_2023_2024.csv"
INTERIM_CSV = PROJECT_ROOT / "data/interim/poa_bairros_zonal_stats_clean.csv"
INTERIM_PARQUET = PROJECT_ROOT / "data/interim/poa_bairros_zonal_stats_clean.parquet"
PROCESSED_CSV = PROJECT_ROOT / "data/processed/poa_bairros_utvi.csv"
PROCESSED_PARQUET = PROJECT_ROOT / "data/processed/poa_bairros_utvi.parquet"
TOP20_CSV = PROJECT_ROOT / "outputs/tables/poa_bairros_ranking_utvi_top20.csv"


def main() -> None:
    """Execute the complete tabular UTVI pipeline."""
    print("Iniciando pipeline UTVI exploratorio")
    print(f"Entrada: {RAW_INPUT}")

    clean_data = load_validate_clean(RAW_INPUT)
    save_table(clean_data, INTERIM_CSV)
    save_table(clean_data, INTERIM_PARQUET)

    print_clean_summary(clean_data)

    utvi_data = build_utvi(clean_data)
    save_table(utvi_data, PROCESSED_CSV)
    save_table(utvi_data, PROCESSED_PARQUET)

    ranking = build_utvi_ranking(utvi_data)
    top20 = select_top_units(ranking, n=20)
    save_ranking(top20, TOP20_CSV)

    print_ranking_summary(ranking, top_n=20)

    print("Arquivos gerados:")
    print(f"- {INTERIM_CSV}")
    print(f"- {INTERIM_PARQUET}")
    print(f"- {PROCESSED_CSV}")
    print(f"- {PROCESSED_PARQUET}")
    print(f"- {TOP20_CSV}")
    print("Pipeline concluido.")


if __name__ == "__main__":
    main()
