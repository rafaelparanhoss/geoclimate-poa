"""Check processed dashboard inputs before local or Streamlit Cloud deploy."""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

BAIRROS_GEOJSON = PROCESSED_DIR / "poa_bairros_utvi.geojson"
BAIRROS_CSV = PROCESSED_DIR / "poa_bairros_utvi.csv"
SETORES_GEOJSON = PROCESSED_DIR / "poa_setores_utvi.geojson"
SETORES_CSV = PROCESSED_DIR / "poa_setores_utvi.csv"

BAIRROS_EXPECTED_ROWS = 94
SETORES_EXPECTED_ROWS = 2744

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
]


def file_size_mb(path: Path) -> float:
    """Return file size in megabytes."""
    return path.stat().st_size / 1024 / 1024


def check_file_exists(path: Path, errors: list[str]) -> None:
    """Validate that a dashboard input file exists."""
    if not path.exists():
        errors.append(f"Arquivo ausente: {path}")


def missing_columns(data: pd.DataFrame, columns: list[str]) -> list[str]:
    """Return required columns missing from a DataFrame."""
    return [column for column in columns if column not in data.columns]


def check_unique_key(data: pd.DataFrame, key: str, expected_rows: int, label: str, errors: list[str]) -> None:
    """Validate unique key counts and row counts."""
    if key not in data.columns:
        return

    duplicated = int(data[key].duplicated().sum())
    unique_count = int(data[key].nunique(dropna=True))

    if duplicated:
        errors.append(f"{label}: {duplicated} chaves duplicadas em {key}.")
    if len(data) != expected_rows:
        errors.append(f"{label}: esperado {expected_rows} linhas, encontrado {len(data)}.")
    if unique_count != expected_rows:
        errors.append(f"{label}: esperado {expected_rows} valores unicos em {key}, encontrado {unique_count}.")


def check_bairros(errors: list[str]) -> None:
    """Validate processed neighborhood files used by the dashboard."""
    bairros_geo = gpd.read_file(BAIRROS_GEOJSON)
    bairros_csv = pd.read_csv(BAIRROS_CSV)

    for label, data in [("GeoJSON bairros", bairros_geo), ("CSV bairros", bairros_csv)]:
        missing = missing_columns(data, BAIRROS_REQUIRED_COLUMNS)
        if missing:
            errors.append(f"{label}: colunas ausentes: {', '.join(missing)}.")
        check_unique_key(data, "bairro_nome_title", BAIRROS_EXPECTED_ROWS, label, errors)

    if "utvi_exploratory" in bairros_geo.columns and bairros_geo["utvi_exploratory"].isna().any():
        errors.append("GeoJSON bairros: ha valores nulos em utvi_exploratory.")
    if "utvi_exploratory" in bairros_csv.columns and bairros_csv["utvi_exploratory"].isna().any():
        errors.append("CSV bairros: ha valores nulos em utvi_exploratory.")

    if bairros_geo.crs is None:
        errors.append("GeoJSON bairros: CRS ausente.")
    elif bairros_geo.crs.to_epsg() != 4326:
        errors.append(f"GeoJSON bairros: CRS esperado EPSG:4326, encontrado {bairros_geo.crs}.")

    if bairros_geo.geometry.isna().any():
        errors.append("GeoJSON bairros: ha geometrias nulas.")


def check_setores(errors: list[str]) -> None:
    """Validate processed census-sector files used by the dashboard."""
    setores_geo = gpd.read_file(SETORES_GEOJSON)
    setores_csv = pd.read_csv(SETORES_CSV, dtype={"CD_SETOR": "string"})

    for label, data in [("GeoJSON setores", setores_geo), ("CSV setores", setores_csv)]:
        missing = missing_columns(data, SETORES_REQUIRED_COLUMNS)
        if missing:
            errors.append(f"{label}: colunas ausentes: {', '.join(missing)}.")
        check_unique_key(data, "CD_SETOR", SETORES_EXPECTED_ROWS, label, errors)

        if "quality_flag_setor" not in data.columns:
            errors.append(f"{label}: coluna quality_flag_setor ausente.")
        elif data["quality_flag_setor"].isna().any():
            errors.append(f"{label}: ha flags de qualidade nulas.")

    if setores_geo.crs is None:
        errors.append("GeoJSON setores: CRS ausente.")
    elif setores_geo.crs.to_epsg() != 4326:
        errors.append(f"GeoJSON setores: CRS esperado EPSG:4326, encontrado {setores_geo.crs}.")

    if setores_geo.geometry.isna().any():
        errors.append("GeoJSON setores: ha geometrias nulas.")


def print_file_inventory(paths: list[Path]) -> None:
    """Print dashboard input inventory with file sizes."""
    print("Arquivos verificados:")
    for path in paths:
        if path.exists():
            relative = path.relative_to(PROJECT_ROOT)
            print(f"- {relative} ({file_size_mb(path):.2f} MB)")
        else:
            print(f"- {path.relative_to(PROJECT_ROOT)} (ausente)")


def main() -> None:
    """Run dashboard input checks."""
    paths = [BAIRROS_GEOJSON, BAIRROS_CSV, SETORES_GEOJSON, SETORES_CSV]
    errors: list[str] = []

    for path in paths:
        check_file_exists(path, errors)

    print_file_inventory(paths)

    if not errors:
        check_bairros(errors)
        check_setores(errors)

    if errors:
        print("\nFalhas encontradas:")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)

    print("\nOK: inputs do dashboard prontos para deploy.")


if __name__ == "__main__":
    main()
