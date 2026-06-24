"""Build thermal vulnerability indicators for the geoclimate-poa MVP."""

import pandas as pd


def normalize_series(values: pd.Series) -> pd.Series:
    """Normalize a numeric series to the 0-1 range."""
    value_range = values.max() - values.min()
    if value_range == 0:
        return pd.Series(0.0, index=values.index)
    return (values - values.min()) / value_range


def build_vulnerability_index(data: pd.DataFrame) -> pd.DataFrame:
    """Build a vulnerability index placeholder from prepared indicators."""
    indexed = data.copy()
    indexed["thermal_vulnerability_index"] = pd.NA
    return indexed


def main() -> None:
    """Run the feature engineering workflow placeholder."""
    raise NotImplementedError("Index construction will be implemented in a future step.")


if __name__ == "__main__":
    main()

