"""Inspect local boundary files without modifying source data."""

from pathlib import Path

import geopandas as gpd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BOUNDARIES_DIR = PROJECT_ROOT / "data/raw/boundaries"
VECTOR_EXTENSIONS = {".shp", ".gpkg", ".geojson"}
AREA_CRS = "EPSG:5880"


def list_vector_files(boundaries_dir: str | Path = BOUNDARIES_DIR) -> list[Path]:
    """List vector files available in the local boundaries directory."""
    boundaries_dir = Path(boundaries_dir)
    if not boundaries_dir.exists():
        raise FileNotFoundError(f"Boundaries directory not found: {boundaries_dir}")

    return sorted(
        path
        for path in boundaries_dir.iterdir()
        if path.is_file() and path.suffix.lower() in VECTOR_EXTENSIONS
    )


def infer_candidate_roles(path: Path, columns: list[str], feature_count: int) -> list[str]:
    """Infer likely dataset roles from filename, columns, and feature count."""
    stem = path.stem.lower()
    column_set = {column.upper() for column in columns}
    roles: list[str] = []

    if "setor" in stem or "CD_SETOR" in column_set:
        roles.append("possivel camada de setores censitarios")
    if "bairro" in stem or ("NOME" in column_set and "CD_SETOR" not in column_set):
        roles.append("possivel camada de bairros")
    if "NM_BAIRRO" in column_set and "CD_SETOR" in column_set:
        roles.append("contem bairro associado aos setores")
    if "limite" in stem or feature_count == 1:
        roles.append("possivel limite municipal")

    return roles or ["papel nao identificado automaticamente"]


def approximate_area_ha(data: gpd.GeoDataFrame) -> float | None:
    """Estimate total polygon area in hectares when possible."""
    if data.empty or data.crs is None:
        return None
    if not data.geometry.geom_type.isin(["Polygon", "MultiPolygon"]).any():
        return None

    area_data = data.to_crs(AREA_CRS)
    return float(area_data.geometry.area.sum() / 10000)


def inspect_vector_file(path: str | Path) -> None:
    """Print diagnostics for a single vector file."""
    path = Path(path)
    data = gpd.read_file(path)
    attribute_preview = data.drop(columns="geometry", errors="ignore").head(3)
    roles = infer_candidate_roles(path, list(data.columns), len(data))
    area_ha = approximate_area_ha(data)

    print("=" * 80)
    print(f"Caminho: {path}")
    print(f"Feicoes: {len(data)}")
    print(f"CRS: {data.crs}")
    print(f"Tipo(s) de geometria: {sorted(data.geometry.geom_type.dropna().unique())}")
    print(f"Colunas: {list(data.columns)}")
    print(f"Candidatos: {', '.join(roles)}")
    if area_ha is not None:
        print(f"Area total aproximada: {area_ha:,.2f} ha")
    else:
        print("Area total aproximada: nao calculada")
    print("Primeiras linhas de atributos:")
    print(attribute_preview.to_string(index=False))


def inspect_boundaries(boundaries_dir: str | Path = BOUNDARIES_DIR) -> list[Path]:
    """Inspect all vector files in the boundaries directory."""
    vector_files = list_vector_files(boundaries_dir)
    print(f"Diretorio: {Path(boundaries_dir)}")
    print(f"Arquivos vetoriais encontrados: {len(vector_files)}")

    for path in vector_files:
        inspect_vector_file(path)

    return vector_files


def main() -> None:
    """Run the local boundary inspection."""
    inspect_boundaries()


if __name__ == "__main__":
    main()
