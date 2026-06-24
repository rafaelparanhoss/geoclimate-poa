"""Create rankings of urban thermal vulnerability."""

from pathlib import Path

import pandas as pd


RANKING_COLUMNS = [
    "utvi_rank",
    "bairro_nome",
    "bairro_nome_title",
    "utvi_exploratory",
    "utvi_class",
    "quality_flag",
    "LST_C_median_mean",
    "LST_C_p75_mean",
    "pct_urbana_land",
    "NDVI_median_mean",
    "NDBI_median_mean",
    "pct_lst_valid_land",
]


def build_utvi_ranking(
    data: pd.DataFrame,
    score_column: str = "utvi_exploratory",
) -> pd.DataFrame:
    """Return a table ranked by UTVI in descending order."""
    if score_column not in data.columns:
        raise ValueError(f"Score column not found: {score_column}")

    ranked = data.copy()
    ranked["utvi_rank"] = (
        ranked[score_column]
        .rank(method="dense", ascending=False)
        .astype("int64")
    )

    available_columns = [column for column in RANKING_COLUMNS if column in ranked.columns]
    return (
        ranked.sort_values(["utvi_rank", "bairro_nome"])
        [available_columns]
        .reset_index(drop=True)
    )


def select_top_units(data: pd.DataFrame, n: int = 20) -> pd.DataFrame:
    """Return the top n rows from an already ranked table."""
    return data.head(n).copy()


def save_ranking(data: pd.DataFrame, output_path: str | Path) -> None:
    """Save a ranking table as CSV."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(output_path, index=False)


def print_ranking_summary(data: pd.DataFrame, top_n: int = 20) -> None:
    """Print UTVI, LST, and LST-validity ranking summaries."""
    print(f"- top {top_n} bairros por UTVI:")
    print(
        data[
            [
                "utvi_rank",
                "bairro_nome_title",
                "utvi_exploratory",
                "utvi_class",
                "quality_flag",
            ]
        ]
        .head(top_n)
        .to_string(index=False)
    )

    print("- top 10 bairros por LST_C_median_mean:")
    print(
        data.sort_values("LST_C_median_mean", ascending=False)
        [["bairro_nome_title", "LST_C_median_mean", "pct_lst_valid_land"]]
        .head(10)
        .to_string(index=False)
    )

    print("- bairros com baixa validade de LST (pct_lst_valid_land < 80):")
    low_validity = data.loc[
        data["pct_lst_valid_land"] < 80,
        ["bairro_nome_title", "pct_lst_valid_land", "quality_flag"],
    ].sort_values("pct_lst_valid_land")
    if low_validity.empty:
        print("  nenhum")
    else:
        print(low_validity.to_string(index=False))
