"""Prepare administrative boundaries for the geoclimate-poa MVP."""

from pathlib import Path

import geopandas as gpd


def load_boundaries(input_path: str | Path) -> gpd.GeoDataFrame:
    """Load spatial boundaries from a local geospatial file."""
    return gpd.read_file(input_path)


def standardize_boundaries(boundaries: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Return a standardized boundaries GeoDataFrame placeholder."""
    return boundaries.copy()


def save_boundaries(boundaries: gpd.GeoDataFrame, output_path: str | Path) -> None:
    """Save prepared boundaries to a GeoParquet file."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    boundaries.to_parquet(output_path)


def main() -> None:
    """Run the boundaries preparation workflow placeholder."""
    raise NotImplementedError("Boundary preparation will be implemented in a future step.")


if __name__ == "__main__":
    main()

