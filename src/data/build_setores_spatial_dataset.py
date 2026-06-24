"""Build a lightweight spatial UTVI dataset by census sector."""

from pathlib import Path

import geopandas as gpd
import pandas as pd


EXPECTED_SETORES = 2744
DEFAULT_SIMPLIFY_TOLERANCE_METERS = 5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SETORES_SHP = PROJECT_ROOT / "data/raw/boundaries/setores_2022_poa.shp"
UTVI_TABLE = PROJECT_ROOT / "data/processed/poa_setores_utvi.csv"
OUTPUT_GEOJSON = PROJECT_ROOT / "data/processed/poa_setores_utvi.geojson"
OUTPUT_GEOPARQUET = PROJECT_ROOT / "data/processed/poa_setores_utvi.geoparquet"


def make_geometries_valid(data: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Fix invalid geometries when needed."""
    fixed = data.copy()
    invalid_count = int((~fixed.geometry.is_valid).sum())
    if invalid_count == 0:
        return fixed

    if hasattr(fixed.geometry, "make_valid"):
        fixed.geometry = fixed.geometry.make_valid()
    else:
        fixed.geometry = fixed.geometry.buffer(0)

    remaining_invalid = int((~fixed.geometry.is_valid).sum())
    if remaining_invalid:
        raise ValueError(
            "Invalid sector geometries remain after repair: "
            f"{remaining_invalid} of {len(fixed)}"
        )

    print(f"- geometrias invalidas de setores corrigidas: {invalid_count}")
    return fixed


def load_setores_geometry(path: str | Path = SETORES_SHP) -> gpd.GeoDataFrame:
    """Load the local census-sector shapefile."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Sector shapefile not found: {path}")

    setores = gpd.read_file(path)
    if "CD_SETOR" not in setores.columns:
        raise ValueError("Sector shapefile does not contain CD_SETOR.")

    setores["CD_SETOR"] = setores["CD_SETOR"].astype("string").str.strip()
    if len(setores) != EXPECTED_SETORES:
        raise ValueError(f"Expected {EXPECTED_SETORES} geometries, found {len(setores)}.")
    if setores["CD_SETOR"].duplicated().any():
        raise ValueError("Duplicated CD_SETOR values in sector shapefile.")
    if setores.geometry.isna().any():
        raise ValueError("Sector shapefile contains null geometries.")

    columns = [
        column
        for column in ["CD_SETOR", "SITUACAO", "CD_TIPO", "AREA_KM2", "geometry"]
        if column in setores.columns
    ]
    return make_geometries_valid(setores[columns].copy())


def load_setores_utvi(path: str | Path = UTVI_TABLE) -> pd.DataFrame:
    """Load processed sector UTVI attributes."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Processed sector UTVI table not found: {path}")

    data = pd.read_csv(path, dtype={"CD_SETOR": "string"})
    if len(data) != EXPECTED_SETORES:
        raise ValueError(f"Expected {EXPECTED_SETORES} UTVI rows, found {len(data)}.")
    if data["CD_SETOR"].duplicated().any():
        raise ValueError("Duplicated CD_SETOR values in processed UTVI table.")
    return data


def join_setores_geometry(
    setores: gpd.GeoDataFrame,
    utvi: pd.DataFrame,
) -> gpd.GeoDataFrame:
    """Join sector geometries to processed UTVI attributes."""
    duplicate_attributes = [
        column
        for column in setores.columns
        if column in utvi.columns and column not in ["CD_SETOR", "geometry"]
    ]
    setores_for_join = setores.drop(columns=duplicate_attributes)

    joined = setores_for_join.merge(
        utvi,
        on="CD_SETOR",
        how="outer",
        indicator=True,
        suffixes=("_geom", ""),
    )

    table_without_geometry = joined.loc[joined["_merge"] == "right_only", "CD_SETOR"].tolist()
    geometry_without_table = joined.loc[joined["_merge"] == "left_only", "CD_SETOR"].tolist()
    if table_without_geometry:
        raise ValueError(f"Sectors in table without geometry: {table_without_geometry}")
    if geometry_without_table:
        raise ValueError(f"Geometries without UTVI attributes: {geometry_without_table}")

    joined = joined.loc[joined["_merge"] == "both"].drop(columns=["_merge"])
    joined = gpd.GeoDataFrame(joined, geometry="geometry", crs=setores.crs)
    joined = make_geometries_valid(joined)

    if len(joined) != EXPECTED_SETORES:
        raise ValueError(f"Expected {EXPECTED_SETORES} joined sectors, found {len(joined)}.")
    if joined["CD_SETOR"].duplicated().any():
        raise ValueError("Duplicated CD_SETOR values after spatial join.")
    if joined.geometry.isna().any():
        raise ValueError("Joined sector dataset contains null geometries.")

    return joined


def enrich_with_geometry_attributes(data: pd.DataFrame) -> pd.DataFrame:
    """Add lightweight sector attributes from the local shapefile when missing."""
    enriched = data.copy()
    setores = load_setores_geometry()
    missing_attribute_columns = [
        column
        for column in ["SITUACAO", "CD_TIPO", "AREA_KM2"]
        if column in setores.columns and column not in enriched.columns
    ]

    if not missing_attribute_columns:
        return enriched

    attributes = pd.DataFrame(
        setores[["CD_SETOR"] + missing_attribute_columns]
    ).drop_duplicates("CD_SETOR")
    return enriched.merge(attributes, on="CD_SETOR", how="left")


def simplify_for_dashboard(
    data: gpd.GeoDataFrame,
    tolerance_meters: float = DEFAULT_SIMPLIFY_TOLERANCE_METERS,
) -> gpd.GeoDataFrame:
    """Simplify sector geometries in source CRS and reproject to EPSG:4326."""
    simplified = data.copy()
    simplified.geometry = simplified.geometry.simplify(
        tolerance=tolerance_meters,
        preserve_topology=True,
    )
    simplified = make_geometries_valid(simplified)
    return simplified.to_crs(epsg=4326)


def save_spatial_outputs(
    data: gpd.GeoDataFrame,
    geojson_path: str | Path = OUTPUT_GEOJSON,
    geoparquet_path: str | Path = OUTPUT_GEOPARQUET,
) -> None:
    """Save GeoJSON and GeoParquet outputs."""
    geojson_path = Path(geojson_path)
    geoparquet_path = Path(geoparquet_path)
    geojson_path.parent.mkdir(parents=True, exist_ok=True)
    geoparquet_path.parent.mkdir(parents=True, exist_ok=True)

    data.to_file(geojson_path, driver="GeoJSON")
    data.to_parquet(geoparquet_path, index=False)


def file_size_mb(path: str | Path) -> float:
    """Return file size in megabytes."""
    return Path(path).stat().st_size / (1024 * 1024)


def build_setores_spatial_dataset() -> gpd.GeoDataFrame:
    """Build and save the sector-level spatial UTVI dataset."""
    setores = load_setores_geometry()
    utvi = load_setores_utvi()
    joined = join_setores_geometry(setores, utvi)
    web_ready = simplify_for_dashboard(joined)

    save_spatial_outputs(web_ready)

    print("Resumo do dataset espacial setorial")
    print(f"- geometrias carregadas: {len(setores)}")
    print(f"- linhas apos join: {len(web_ready)}")
    print(f"- CRS de exportacao: {web_ready.crs}")
    print(f"- GeoJSON: {OUTPUT_GEOJSON} ({file_size_mb(OUTPUT_GEOJSON):.2f} MB)")
    print(f"- GeoParquet: {OUTPUT_GEOPARQUET} ({file_size_mb(OUTPUT_GEOPARQUET):.2f} MB)")

    return web_ready
