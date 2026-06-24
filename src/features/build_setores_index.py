"""Build the exploratory UTVI for census sectors."""

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


def normalize_with_reference(values: pd.Series, reference_values: pd.Series) -> pd.Series:
    """Normalize values using min and max from a reference subset."""
    values = pd.to_numeric(values, errors="coerce")
    reference_values = pd.to_numeric(reference_values, errors="coerce").dropna()

    value_min = reference_values.min()
    value_max = reference_values.max()
    value_range = value_max - value_min

    if pd.isna(value_range) or value_range == 0:
        return pd.Series(0.0, index=values.index)

    return ((values - value_min) / value_range).clip(lower=0, upper=1)


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


def build_setores_utvi(data: pd.DataFrame) -> pd.DataFrame:
    """Build sector-level exploratory UTVI using ok sectors as reference."""
    missing_columns = [column for column in UTVI_INPUT_COLUMNS if column not in data.columns]
    if missing_columns:
        raise ValueError(f"Missing sector UTVI input columns: {missing_columns}")
    if "quality_flag_setor" not in data.columns:
        raise ValueError("Missing quality_flag_setor column.")

    indexed = data.copy()
    reference = indexed.loc[indexed["quality_flag_setor"].eq("ok")]
    if reference.empty:
        raise ValueError("No ok sectors available to define UTVI normalization.")

    indexed["lst_median_norm"] = normalize_with_reference(
        indexed["LST_C_median_mean"],
        reference["LST_C_median_mean"],
    )
    indexed["lst_p75_norm"] = normalize_with_reference(
        indexed["LST_C_p75_mean"],
        reference["LST_C_p75_mean"],
    )
    indexed["urban_norm"] = normalize_with_reference(
        indexed["pct_urbana_land"],
        reference["pct_urbana_land"],
    )
    indexed["ndbi_norm"] = normalize_with_reference(
        indexed["NDBI_median_mean"],
        reference["NDBI_median_mean"],
    )
    indexed["ndvi_norm"] = normalize_with_reference(
        indexed["NDVI_median_mean"],
        reference["NDVI_median_mean"],
    )
    indexed["ndvi_inverse_norm"] = 1 - indexed["ndvi_norm"]

    indexed["utvi_setor_exploratory"] = indexed[UTVI_COMPONENT_COLUMNS].mean(axis=1)
    indexed.loc[
        indexed["quality_flag_setor"].eq("invalid_no_lst"),
        "utvi_setor_exploratory",
    ] = pd.NA

    indexed["utvi_setor_rank"] = pd.NA
    valid_ranking = indexed["quality_flag_setor"].eq("ok")
    indexed.loc[valid_ranking, "utvi_setor_rank"] = (
        indexed.loc[valid_ranking, "utvi_setor_exploratory"]
        .rank(method="dense", ascending=False)
        .astype("Int64")
    )
    indexed["utvi_setor_rank"] = indexed["utvi_setor_rank"].astype("Int64")
    indexed["utvi_setor_class"] = indexed["utvi_setor_exploratory"].apply(classify_utvi)

    return indexed.sort_values(["CD_SETOR"]).reset_index(drop=True)


def build_setores_ranking(data: pd.DataFrame) -> pd.DataFrame:
    """Build the main ranking with ok sectors only."""
    ranked = data.loc[data["is_valid_for_ranking"]].copy()
    ranked = ranked.sort_values(
        ["utvi_setor_exploratory", "CD_SETOR"],
        ascending=[False, True],
    )
    return ranked.reset_index(drop=True)


def print_setores_ranking_summary(data: pd.DataFrame, top_n: int = 20) -> None:
    """Print ranking, LST, invalid-sector, and quality summaries."""
    ranking = build_setores_ranking(data)
    print(f"- top {top_n} setores por UTVI:")
    print(
        ranking[
            [
                "utvi_setor_rank",
                "CD_SETOR",
                "NM_BAIRRO",
                "utvi_setor_exploratory",
                "utvi_setor_class",
                "quality_flag_setor",
            ]
        ]
        .head(top_n)
        .to_string(index=False)
    )

    print(f"- top {top_n} setores por LST_C_median_mean:")
    print(
        data.dropna(subset=["LST_C_median_mean"])
        .sort_values("LST_C_median_mean", ascending=False)
        [
            [
                "CD_SETOR",
                "NM_BAIRRO",
                "LST_C_median_mean",
                "pct_lst_valid_land",
                "quality_flag_setor",
            ]
        ]
        .head(top_n)
        .to_string(index=False)
    )

    invalid = data.loc[
        data["quality_flag_setor"].eq("invalid_no_lst"),
        ["CD_SETOR", "NM_BAIRRO", "LST_C_median_mean", "pct_lst_valid_land"],
    ]
    print("- setores invalidos:")
    print(invalid.to_string(index=False) if not invalid.empty else "  nenhum")

    print("- resumo de quality_flag_setor:")
    print(data["quality_flag_setor"].value_counts(dropna=False).to_string())
