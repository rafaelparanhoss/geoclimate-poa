"""Build the exploratory urban thermal vulnerability index."""

import pandas as pd


UTVI_INPUT_COLUMNS = [
    "LST_C_median_mean",
    "LST_C_p75_mean",
    "pct_urbana_land",
    "NDBI_median_mean",
    "NDVI_median_mean",
]

UTVI_COMPONENT_COLUMNS = [
    "lst_median_norm",
    "lst_p75_norm",
    "urban_norm",
    "ndbi_norm",
    "ndvi_inverse_norm",
]


def normalize_min_max(values: pd.Series) -> pd.Series:
    """Normalize a numeric series to the 0-1 range."""
    numeric_values = pd.to_numeric(values, errors="coerce")
    value_min = numeric_values.min()
    value_max = numeric_values.max()
    value_range = value_max - value_min

    if pd.isna(value_range) or value_range == 0:
        return pd.Series(0.0, index=values.index)

    return (numeric_values - value_min) / value_range


def classify_utvi(score: float) -> str:
    """Classify a UTVI score using fixed 0-1 ranges."""
    if pd.isna(score):
        return "sem classificacao"
    if score < 0.20:
        return "muito baixa"
    if score < 0.40:
        return "baixa"
    if score < 0.60:
        return "media"
    if score < 0.80:
        return "alta"
    return "muito alta"


def add_quality_flag(data: pd.DataFrame) -> pd.DataFrame:
    """Add a quality flag based on LST valid land coverage."""
    flagged = data.copy()
    flagged["quality_flag"] = "ok"
    flagged.loc[
        flagged["pct_lst_valid_land"] < 80,
        "quality_flag",
    ] = "caution_low_lst_valid"
    return flagged


def build_utvi(data: pd.DataFrame) -> pd.DataFrame:
    """Build the exploratory urban thermal vulnerability index."""
    missing_columns = [column for column in UTVI_INPUT_COLUMNS if column not in data.columns]
    if missing_columns:
        raise ValueError(f"Missing UTVI input columns: {missing_columns}")

    indexed = data.copy()

    indexed["lst_median_norm"] = normalize_min_max(indexed["LST_C_median_mean"])
    indexed["lst_p75_norm"] = normalize_min_max(indexed["LST_C_p75_mean"])
    indexed["urban_norm"] = normalize_min_max(indexed["pct_urbana_land"])
    indexed["ndbi_norm"] = normalize_min_max(indexed["NDBI_median_mean"])
    indexed["ndvi_norm"] = normalize_min_max(indexed["NDVI_median_mean"])
    indexed["ndvi_inverse_norm"] = 1 - indexed["ndvi_norm"]

    indexed["utvi_exploratory"] = indexed[UTVI_COMPONENT_COLUMNS].mean(axis=1)
    indexed["utvi_rank"] = (
        indexed["utvi_exploratory"]
        .rank(method="dense", ascending=False)
        .astype("int64")
    )
    indexed["utvi_class"] = indexed["utvi_exploratory"].apply(classify_utvi)

    indexed = add_quality_flag(indexed)

    return indexed.sort_values(["utvi_rank", "bairro_nome"]).reset_index(drop=True)
