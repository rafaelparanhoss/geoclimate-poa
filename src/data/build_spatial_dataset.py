"""Build a lightweight spatial UTVI dataset by bairro for the dashboard."""

from pathlib import Path
import unicodedata

import geopandas as gpd
import pandas as pd


EXPECTED_BAIRROS = 94
DEFAULT_SIMPLIFY_TOLERANCE_METERS = 15

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BAIRROS_SHP = PROJECT_ROOT / "data/raw/boundaries/Bairros_LC12112_16.shp"
UTVI_TABLE = PROJECT_ROOT / "data/processed/poa_bairros_utvi.csv"
OUTPUT_GEOJSON = PROJECT_ROOT / "data/processed/poa_bairros_utvi.geojson"
OUTPUT_GEOPARQUET = PROJECT_ROOT / "data/processed/poa_bairros_utvi.geoparquet"

NAME_FIELD_CANDIDATES = ["NOME", "NM_BAIRRO", "bairro_nome", "BAIRRO"]


def normalize_name(value: object) -> str:
    """Normalize a bairro name for robust joins."""
    text = "" if pd.isna(value) else str(value)
    text = " ".join(text.strip().upper().split())
    return "".join(
        char
        for char in unicodedata.normalize("NFKD", text)
        if not unicodedata.combining(char)
    )


def find_name_field(columns: list[str]) -> str:
    """Find the preferred bairro name field in a spatial layer."""
    for candidate in NAME_FIELD_CANDIDATES:
        if candidate in columns:
            return candidate
    raise ValueError(
        "Could not identify bairro name field. "
        f"Tried: {NAME_FIELD_CANDIDATES}. Available: {columns}"
    )


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
            "Invalid geometries remain after repair: "
            f"{remaining_invalid} of {len(fixed)}"
        )

    print(f"- geometrias invalidas corrigidas: {invalid_count}")
    return fixed


def load_bairros(path: str | Path = BAIRROS_SHP) -> gpd.GeoDataFrame:
    """Load the local bairro shapefile."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Bairro shapefile not found: {path}")

    bairros = gpd.read_file(path)
    if bairros.empty:
        raise ValueError(f"Bairro shapefile is empty: {path}")

    name_field = find_name_field(list(bairros.columns))
    bairros = bairros[[name_field, "geometry"]].copy()
    bairros = bairros.rename(columns={name_field: "bairro_nome_geom"})
    bairros["bairro_join_key"] = bairros["bairro_nome_geom"].map(normalize_name)
    bairros = bairros.loc[bairros["bairro_join_key"] != ""].copy()

    return make_geometries_valid(bairros)


def dissolve_bairros(bairros: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Dissolve bairro geometries by normalized bairro name."""
    dissolved = bairros.dissolve(
        by="bairro_join_key",
        as_index=False,
        aggfunc={
            "bairro_nome_geom": "first",
        },
    )
    dissolved["n_partes_geom"] = (
        bairros.groupby("bairro_join_key")
        .size()
        .reindex(dissolved["bairro_join_key"])
        .to_numpy()
    )
    dissolved = make_geometries_valid(dissolved)

    if len(dissolved) != EXPECTED_BAIRROS:
        raise ValueError(
            f"Expected {EXPECTED_BAIRROS} dissolved bairros, found {len(dissolved)}."
        )
    if dissolved["bairro_join_key"].duplicated().any():
        raise ValueError("Duplicated bairro keys after dissolve.")

    return dissolved


def load_utvi_table(path: str | Path = UTVI_TABLE) -> pd.DataFrame:
    """Load the processed UTVI table."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"UTVI table not found: {path}")

    utvi = pd.read_csv(path)
    required = {"bairro_nome", "utvi_exploratory", "utvi_rank"}
    missing = sorted(required - set(utvi.columns))
    if missing:
        raise ValueError(f"Missing required UTVI columns: {missing}")

    utvi["bairro_join_key"] = utvi["bairro_nome"].map(normalize_name)
    if len(utvi) != EXPECTED_BAIRROS:
        raise ValueError(f"Expected {EXPECTED_BAIRROS} UTVI rows, found {len(utvi)}.")
    if utvi["bairro_join_key"].duplicated().any():
        duplicated = utvi.loc[
            utvi["bairro_join_key"].duplicated(),
            "bairro_nome",
        ].tolist()
        raise ValueError(f"Duplicated bairro keys in UTVI table: {duplicated}")

    return utvi


def join_bairros_utvi(
    bairros: gpd.GeoDataFrame,
    utvi: pd.DataFrame,
) -> gpd.GeoDataFrame:
    """Join dissolved bairro geometries with UTVI attributes."""
    joined = bairros.merge(
        utvi,
        on="bairro_join_key",
        how="outer",
        indicator=True,
    )

    missing_geometry = joined.loc[joined["_merge"] == "right_only", "bairro_nome"].tolist()
    missing_utvi = joined.loc[joined["_merge"] == "left_only", "bairro_nome_geom"].tolist()
    if missing_geometry:
        raise ValueError(f"Bairros in UTVI table without geometry: {missing_geometry}")
    if missing_utvi:
        raise ValueError(f"Geometries without UTVI attributes: {missing_utvi}")

    joined = joined.loc[joined["_merge"] == "both"].drop(columns=["_merge"])
    joined = gpd.GeoDataFrame(joined, geometry="geometry", crs=bairros.crs)
    joined = make_geometries_valid(joined)

    if len(joined) != EXPECTED_BAIRROS:
        raise ValueError(f"Expected {EXPECTED_BAIRROS} joined rows, found {len(joined)}.")
    if joined.geometry.isna().any():
        raise ValueError("Joined dataset has rows without geometry.")
    if joined["utvi_exploratory"].isna().any():
        raise ValueError("Joined dataset has geometries without UTVI values.")

    return joined


def simplify_for_dashboard(
    data: gpd.GeoDataFrame,
    tolerance_meters: float = DEFAULT_SIMPLIFY_TOLERANCE_METERS,
) -> gpd.GeoDataFrame:
    """Simplify geometries in source CRS and reproject to EPSG:4326."""
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


def build_spatial_dataset() -> gpd.GeoDataFrame:
    """Build and save the lightweight bairro UTVI spatial dataset."""
    bairros = load_bairros()
    dissolved = dissolve_bairros(bairros)
    utvi = load_utvi_table()
    joined = join_bairros_utvi(dissolved, utvi)
    web_ready = simplify_for_dashboard(joined)

    save_spatial_outputs(web_ready)

    print("Resumo do dataset espacial de bairros")
    print(f"- bairros carregados: {len(bairros)}")
    print(f"- bairros apos dissolve: {len(dissolved)}")
    print(f"- bairros apos join: {len(web_ready)}")
    print(f"- CRS de exportacao: {web_ready.crs}")
    print("- colunas principais:")
    print(
        [
            "bairro_nome",
            "bairro_nome_title",
            "utvi_exploratory",
            "utvi_rank",
            "utvi_class",
            "quality_flag",
            "geometry",
        ]
    )
    print(f"- GeoJSON: {OUTPUT_GEOJSON} ({file_size_mb(OUTPUT_GEOJSON):.2f} MB)")
    print(f"- GeoParquet: {OUTPUT_GEOPARQUET} ({file_size_mb(OUTPUT_GEOPARQUET):.2f} MB)")

    return web_ready


def main() -> None:
    """Run the spatial dataset build workflow."""
    build_spatial_dataset()


if __name__ == "__main__":
    main()
