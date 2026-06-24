"""Check readiness for the future sector-level UTVI pipeline."""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SETORES_EXPORT = (
    PROJECT_ROOT
    / "data/raw/gee_exports/poa_setores_zonal_stats_landsat_mapbiomas_2023_2024.csv"
)


def main() -> None:
    """Report whether the sector-level GEE export is available."""
    if not SETORES_EXPORT.exists():
        print("CSV setorial do GEE ainda nao encontrado.")
        print(f"Esperado em: {SETORES_EXPORT}")
        print("Exporte primeiro o CSV no Google Earth Engine usando:")
        print("gee/03_zonal_stats_setores.js")
        return

    print("CSV setorial encontrado.")
    print(f"Caminho: {SETORES_EXPORT}")
    print("O processamento setorial Python ainda e placeholder nesta etapa.")


if __name__ == "__main__":
    main()
