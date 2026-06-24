"""Placeholders for future census-sector GEE export processing."""

from pathlib import Path

import pandas as pd


SETORES_EXPORT_NAME = "poa_setores_zonal_stats_landsat_mapbiomas_2023_2024.csv"
EXPECTED_KEY_COLUMN = "CD_SETOR"


def load_setores_csv(input_path: str | Path) -> pd.DataFrame:
    """Load a sector-level CSV exported from Google Earth Engine."""
    input_path = Path(input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"Sector GEE export not found: {input_path}")
    return pd.read_csv(input_path)


def validate_cd_setor(data: pd.DataFrame) -> None:
    """Validate the CD_SETOR key for sector-level processing."""
    if EXPECTED_KEY_COLUMN not in data.columns:
        raise ValueError(f"Missing required key column: {EXPECTED_KEY_COLUMN}")
    if data[EXPECTED_KEY_COLUMN].isna().any():
        raise ValueError("CD_SETOR contains null values.")
    if data[EXPECTED_KEY_COLUMN].duplicated().any():
        raise ValueError("CD_SETOR contains duplicate values.")


def calculate_setores_utvi(data: pd.DataFrame) -> pd.DataFrame:
    """Calculate a future exploratory UTVI for census sectors."""
    raise NotImplementedError(
        "Sector-level UTVI will be implemented after the GEE CSV is exported "
        "and quality thresholds are reviewed."
    )


def add_quality_flags(data: pd.DataFrame) -> pd.DataFrame:
    """Add future sector-level quality flags."""
    raise NotImplementedError(
        "Sector-level quality flags will be implemented after inspecting "
        "LST validity and approximate pixel counts by sector."
    )


def save_processed_outputs(data: pd.DataFrame, output_dir: str | Path) -> None:
    """Save future processed sector-level outputs."""
    raise NotImplementedError(
        "Processed sector outputs will be defined after the first sector CSV "
        "export is validated."
    )
