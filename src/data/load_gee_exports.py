"""Load, validate, and clean Google Earth Engine tabular exports."""

from pathlib import Path

import pandas as pd


EXPECTED_ROW_COUNT = 94

REQUIRED_COLUMNS = [
    "bairro_nome",
    "n_partes_originais",
    "area_bairro_geom_ha",
    "area_pixel_total_ha",
    "area_land_ha",
    "area_agua_ha",
    "area_urbana_ha",
    "area_vegetacao_ha",
    "area_lst_valid_ha",
    "pct_land",
    "pct_agua",
    "pct_urbana_land",
    "pct_vegetacao_land",
    "pct_lst_valid_land",
    "LST_C_median_mean",
    "LST_C_median_median",
    "LST_C_p75_mean",
    "LST_C_p75_median",
    "LST_C_p90_mean",
    "LST_C_p90_median",
    "NDVI_median_mean",
    "NDVI_median_median",
    "NDBI_median_mean",
    "NDBI_median_median",
    "MNDWI_median_mean",
    "MNDWI_median_median",
    "n_obs_validas_mean",
    "n_obs_validas_median",
    "lst_valid_mask_mean",
    "lst_valid_mask_median",
]

INDEX_COLUMNS = [
    "LST_C_median_mean",
    "LST_C_p75_mean",
    "pct_urbana_land",
    "NDBI_median_mean",
    "NDVI_median_mean",
]

NUMERIC_COLUMNS = [column for column in REQUIRED_COLUMNS if column != "bairro_nome"]


def load_gee_table(input_path: str | Path) -> pd.DataFrame:
    """Load a CSV table exported by Google Earth Engine."""
    input_path = Path(input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"GEE export not found: {input_path}")

    return pd.read_csv(input_path)


def validate_required_columns(data: pd.DataFrame) -> None:
    """Validate that all required columns are present."""
    missing_columns = [column for column in REQUIRED_COLUMNS if column not in data.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")


def validate_bairros(data: pd.DataFrame, expected_rows: int = EXPECTED_ROW_COUNT) -> None:
    """Validate expected bairro row count and uniqueness."""
    row_count = len(data)
    unique_bairros = data["bairro_nome"].nunique(dropna=False)
    duplicated = data.loc[data["bairro_nome"].duplicated(), "bairro_nome"].tolist()

    if row_count != expected_rows:
        raise ValueError(f"Expected {expected_rows} rows, found {row_count}.")
    if unique_bairros != expected_rows:
        raise ValueError(f"Expected {expected_rows} unique bairros, found {unique_bairros}.")
    if duplicated:
        raise ValueError(f"Duplicated bairro_nome values found: {duplicated}")


def validate_index_columns(data: pd.DataFrame) -> None:
    """Validate null values in columns used by the exploratory UTVI."""
    null_counts = data[INDEX_COLUMNS].isna().sum()
    null_counts = null_counts[null_counts > 0]

    if not null_counts.empty:
        raise ValueError(
            "Null values found in UTVI input columns: "
            f"{null_counts.to_dict()}"
        )


def validate_gee_export(data: pd.DataFrame) -> None:
    """Run all structural validations for the GEE export."""
    validate_required_columns(data)
    validate_bairros(data)
    validate_index_columns(data)


def clean_gee_export(data: pd.DataFrame) -> pd.DataFrame:
    """Clean and standardize a validated GEE export table."""
    validate_required_columns(data)

    cleaned = data.copy()
    cleaned["bairro_nome"] = (
        cleaned["bairro_nome"]
        .astype("string")
        .str.strip()
        .str.replace(r"\s+", " ", regex=True)
        .str.upper()
    )
    cleaned["bairro_nome_title"] = cleaned["bairro_nome"].str.title()

    for column in NUMERIC_COLUMNS:
        cleaned[column] = pd.to_numeric(cleaned[column], errors="coerce")

    validate_bairros(cleaned)
    validate_index_columns(cleaned)

    return cleaned.sort_values("bairro_nome").reset_index(drop=True)


def save_table(data: pd.DataFrame, output_path: str | Path) -> None:
    """Save a table as CSV or Parquet based on the output suffix."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_path.suffix.lower() == ".csv":
        data.to_csv(output_path, index=False)
    elif output_path.suffix.lower() == ".parquet":
        data.to_parquet(output_path, index=False)
    else:
        raise ValueError(f"Unsupported output format: {output_path.suffix}")


def print_clean_summary(data: pd.DataFrame) -> None:
    """Print a compact validation summary for the cleaned table."""
    print("Resumo da tabela limpa")
    print(f"- linhas: {len(data)}")
    print(f"- bairros unicos: {data['bairro_nome'].nunique()}")
    print("- top 10 por LST_C_median_mean:")
    print(
        data.sort_values("LST_C_median_mean", ascending=False)
        [["bairro_nome_title", "LST_C_median_mean", "pct_lst_valid_land"]]
        .head(10)
        .to_string(index=False)
    )
    print("- bairros com pct_lst_valid_land < 80:")
    low_validity = data.loc[
        data["pct_lst_valid_land"] < 80,
        ["bairro_nome_title", "pct_lst_valid_land"],
    ].sort_values("pct_lst_valid_land")
    if low_validity.empty:
        print("  nenhum")
    else:
        print(low_validity.to_string(index=False))


def load_validate_clean(input_path: str | Path) -> pd.DataFrame:
    """Load, validate, and clean a GEE export table."""
    raw = load_gee_table(input_path)
    validate_gee_export(raw)
    return clean_gee_export(raw)
