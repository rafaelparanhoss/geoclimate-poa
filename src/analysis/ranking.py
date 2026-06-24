"""Create rankings of urban thermal vulnerability."""

import pandas as pd


def rank_spatial_units(
    data: pd.DataFrame,
    score_column: str = "thermal_vulnerability_index",
) -> pd.DataFrame:
    """Rank spatial units by vulnerability score in descending order."""
    ranked = data.copy()
    ranked["rank"] = ranked[score_column].rank(method="dense", ascending=False)
    return ranked.sort_values("rank")


def select_top_units(data: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Return the top n spatial units from a ranked table."""
    return data.head(n).copy()


def main() -> None:
    """Run the ranking workflow placeholder."""
    raise NotImplementedError("Ranking analysis will be implemented in a future step.")


if __name__ == "__main__":
    main()

