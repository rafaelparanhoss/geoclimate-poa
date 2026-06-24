"""Prepare the future spatial bairro dataset for the Streamlit dashboard.

Planned workflow:
1. Load the local official bairro geometry from ``data/raw/boundaries``.
2. Dissolve bairro geometries by name so the spatial layer has 94 features.
3. Load ``data/processed/poa_bairros_utvi.csv``.
4. Standardize bairro names on both sides of the join.
5. Join geometry and UTVI attributes by bairro name.
6. Validate 94 geometries, 94 joined rows, and no duplicate bairro names.
7. Simplify geometry for dashboard performance.
8. Save lightweight spatial outputs:
   - ``data/processed/poa_bairros_utvi.geojson``
   - ``data/processed/poa_bairros_utvi.geoparquet``

This script is intentionally a placeholder for now. The tabular UTVI outputs
are ready, but the spatial export should be implemented after confirming the
authoritative local bairro geometry, CRS, join key, and simplification tolerance.
"""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BOUNDARIES_DIR = PROJECT_ROOT / "data/raw/boundaries"
UTVI_TABLE = PROJECT_ROOT / "data/processed/poa_bairros_utvi.csv"
OUTPUT_GEOJSON = PROJECT_ROOT / "data/processed/poa_bairros_utvi.geojson"
OUTPUT_GEOPARQUET = PROJECT_ROOT / "data/processed/poa_bairros_utvi.geoparquet"


def main() -> None:
    """Describe the next spatial build step without running it yet."""
    print("Spatial dataset build is not implemented yet.")
    print(f"Expected boundary inputs directory: {BOUNDARIES_DIR}")
    print(f"Expected UTVI table: {UTVI_TABLE}")
    print(f"Future GeoJSON output: {OUTPUT_GEOJSON}")
    print(f"Future GeoParquet output: {OUTPUT_GEOPARQUET}")


if __name__ == "__main__":
    main()
