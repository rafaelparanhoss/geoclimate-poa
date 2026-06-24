"""Load, validate, and clean census-sector GEE tabular exports."""

from pathlib import Path

import pandas as pd


EXPECTED_SETORES = 2744
INVALID_SENTINEL_THRESHOLD = -9990

KEY_COLUMNS = ["CD_SETOR", "NM_BAIRRO", "NM_MUN"]

REQUIRED_COLUMNS = [
    "CD_SETOR",
    "NM_BAIRRO",
    "NM_MUN",
    "area_setor_geom_ha",
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
    "n_pixels_land_aprox",
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
]

OPTIONAL_COLUMNS = [
    "SITUACAO",
    "lst_valid_mask_median",
]

UTVI_INPUT_COLUMNS = [
    "LST_C_median_mean",
    "LST_C_p75_mean",
    "pct_urbana_land",
    "NDBI_median_mean",
    "NDVI_median_mean",
]

NUMERIC_COLUMNS = [
    column
    for column in REQUIRED_COLUMNS + OPTIONAL_COLUMNS
    if column not in KEY_COLUMNS and column != "SITUACAO"
]


def load_setores_csv(input_path: str | Path) -> pd.DataFrame:
    """Load a sector-level CSV exported from Google Earth Engine."""
    input_path = Path(input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"Sector GEE export not found: {input_path}")
    return pd.read_csv(input_path, dtype={"CD_SETOR": "string"})


def validate_required_columns(data: pd.DataFrame) -> None:
    """Validate required columns in the sector-level GEE export."""
    missing_columns = [column for column in REQUIRED_COLUMNS if column not in data.columns]
    if missing_columns:
        raise ValueError(f"Missing required sector columns: {missing_columns}")


def validate_cd_setor(data: pd.DataFrame, expected_rows: int = EXPECTED_SETORES) -> None:
    """Validate the CD_SETOR key for sector-level processing."""
    if "CD_SETOR" not in data.columns:
        raise ValueError("Missing required key column: CD_SETOR")
    if data["CD_SETOR"].isna().any():
        raise ValueError("CD_SETOR contains null values.")
    if data["CD_SETOR"].duplicated().any():
        raise ValueError("CD_SETOR contains duplicate values.")
    if len(data) != expected_rows:
        raise ValueError(f"Expected {expected_rows} sectors, found {len(data)}.")


def count_invalid_sentinels(data: pd.DataFrame) -> pd.Series:
    """Count invalid sentinel values in numeric columns."""
    counts: dict[str, int] = {}
    for column in NUMERIC_COLUMNS:
        if column not in data.columns:
            continue
        values = pd.to_numeric(data[column], errors="coerce")
        invalid_count = int((values <= INVALID_SENTINEL_THRESHOLD).sum())
        if invalid_count:
            counts[column] = invalid_count
    return pd.Series(counts, dtype="int64")


def replace_invalid_sentinels(data: pd.DataFrame) -> pd.DataFrame:
    """Replace numeric invalid sentinels with NaN."""
    cleaned = data.copy()
    for column in NUMERIC_COLUMNS:
        if column not in cleaned.columns:
            continue
        values = pd.to_numeric(cleaned[column], errors="coerce")
        cleaned[column] = values.mask(values <= INVALID_SENTINEL_THRESHOLD)
    return cleaned


def add_quality_flags(data: pd.DataFrame) -> pd.DataFrame:
    """Add sector-level quality flags using priority rules."""
    flagged = data.copy()
    flagged["quality_flag_setor"] = "ok"

    small_sector = (
        (flagged["area_land_ha"] < 1)
        | (flagged["n_pixels_land_aprox"] < 10)
    )
    low_lst_valid = flagged["pct_lst_valid_land"] < 80
    invalid_no_lst = (
        flagged["LST_C_median_mean"].isna()
        | flagged["pct_lst_valid_land"].fillna(0).eq(0)
    )

    flagged.loc[small_sector, "quality_flag_setor"] = "caution_small_sector"
    flagged.loc[low_lst_valid, "quality_flag_setor"] = "caution_low_lst_valid"
    flagged.loc[invalid_no_lst, "quality_flag_setor"] = "invalid_no_lst"
    flagged["is_valid_for_ranking"] = flagged["quality_flag_setor"].eq("ok")

    return flagged


def clean_setores_export(data: pd.DataFrame) -> pd.DataFrame:
    """Clean and standardize a sector-level GEE export table."""
    validate_required_columns(data)

    cleaned = data.copy()
    cleaned["CD_SETOR"] = cleaned["CD_SETOR"].astype("string").str.strip()
    cleaned["NM_BAIRRO"] = (
        cleaned["NM_BAIRRO"]
        .astype("string")
        .str.strip()
        .str.replace(r"\s+", " ", regex=True)
    )
    cleaned["NM_MUN"] = (
        cleaned["NM_MUN"]
        .astype("string")
        .str.strip()
        .str.replace(r"\s+", " ", regex=True)
    )
    if "SITUACAO" in cleaned.columns:
        cleaned["SITUACAO"] = (
            cleaned["SITUACAO"]
            .astype("string")
            .str.strip()
            .str.replace(r"\s+", " ", regex=True)
        )

    cleaned["bairro_nome_title"] = cleaned["NM_BAIRRO"].str.title()

    for column in NUMERIC_COLUMNS:
        if column in cleaned.columns:
            cleaned[column] = pd.to_numeric(cleaned[column], errors="coerce")

    cleaned = replace_invalid_sentinels(cleaned)
    validate_cd_setor(cleaned)
    return add_quality_flags(cleaned).sort_values("CD_SETOR").reset_index(drop=True)


def index_null_counts(data: pd.DataFrame) -> pd.Series:
    """Return null counts for UTVI input variables."""
    return data[UTVI_INPUT_COLUMNS].isna().sum()


def save_table(data: pd.DataFrame, output_path: str | Path) -> None:
    """Save a table as CSV or Parquet based on file suffix."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_path.suffix.lower() == ".csv":
        data.to_csv(output_path, index=False)
    elif output_path.suffix.lower() == ".parquet":
        data.to_parquet(output_path, index=False)
    else:
        raise ValueError(f"Unsupported output format: {output_path.suffix}")


def print_clean_summary(
    data: pd.DataFrame,
    invalid_counts_before_cleaning: pd.Series,
) -> None:
    """Print a compact summary of the cleaned sector table."""
    print("Resumo da tabela setorial limpa")
    print(f"- setores: {len(data)}")
    print(f"- setores unicos: {data['CD_SETOR'].nunique()}")
    print(f"- bairros associados: {data['NM_BAIRRO'].nunique(dropna=True)}")
    print("- valores <= -9990 antes da limpeza:")
    if invalid_counts_before_cleaning.empty:
        print("  nenhum")
    else:
        print(invalid_counts_before_cleaning.to_string())

    invalid = data.loc[
        data["quality_flag_setor"].eq("invalid_no_lst"),
        ["CD_SETOR", "NM_BAIRRO", "LST_C_median_mean", "pct_lst_valid_land"],
    ]
    print("- setores com LST invalida:")
    print(invalid.to_string(index=False) if not invalid.empty else "  nenhum")

    low_validity = data.loc[data["pct_lst_valid_land"] < 80, "CD_SETOR"]
    small_land = data.loc[data["area_land_ha"] < 1, "CD_SETOR"]
    low_pixels = data.loc[data["n_pixels_land_aprox"] < 10, "CD_SETOR"]
    print(f"- setores com pct_lst_valid_land < 80: {len(low_validity)}")
    print(f"- setores com area_land_ha < 1: {len(small_land)}")
    print(f"- setores com n_pixels_land_aprox < 10: {len(low_pixels)}")
    print("- nulos nas variaveis do indice:")
    print(index_null_counts(data).to_string())


def load_validate_clean(input_path: str | Path) -> tuple[pd.DataFrame, pd.Series]:
    """Load, validate, and clean a sector-level GEE export table."""
    raw = load_setores_csv(input_path)
    validate_required_columns(raw)
    validate_cd_setor(raw)
    invalid_counts = count_invalid_sentinels(raw)
    cleaned = clean_setores_export(raw)
    return cleaned, invalid_counts
