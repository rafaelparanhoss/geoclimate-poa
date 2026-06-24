"""Map utilities for the geoclimate-poa MVP."""

import geopandas as gpd
import folium


def create_base_map(
    center: tuple[float, float] = (-30.0346, -51.2177),
    zoom_start: int = 11,
) -> folium.Map:
    """Create a Folium base map centered on Porto Alegre."""
    return folium.Map(location=center, zoom_start=zoom_start, tiles="CartoDB positron")


def add_choropleth_placeholder(
    base_map: folium.Map,
    boundaries: gpd.GeoDataFrame,
) -> folium.Map:
    """Add a placeholder layer for future choropleth mapping."""
    folium.GeoJson(boundaries, name="Unidades espaciais").add_to(base_map)
    return base_map


def main() -> None:
    """Run the map generation workflow placeholder."""
    raise NotImplementedError("Map generation will be implemented in a future step.")


if __name__ == "__main__":
    main()

