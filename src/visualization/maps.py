"""Map utilities for the GeoClimate POA Streamlit dashboard."""

from __future__ import annotations

import math
from collections.abc import Mapping

import branca.colormap as cm
import folium
import geopandas as gpd
import pandas as pd


PORTO_ALEGRE_CENTER = (-30.0346, -51.2177)


def _is_missing(value: object) -> bool:
    """Return True for missing scalar values used in GeoJSON properties."""
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    return False


def _palette_for_variable(variable: str) -> cm.LinearColormap:
    """Choose a simple color palette for a dashboard variable."""
    if "NDVI" in variable or "vegetacao" in variable:
        return cm.linear.YlGn_09
    if "pct_lst_valid" in variable:
        return cm.linear.Blues_09
    if "MNDWI" in variable or "agua" in variable:
        return cm.linear.YlGnBu_09
    if "NDBI" in variable or "urbana" in variable:
        return cm.linear.OrRd_09
    return cm.linear.YlOrRd_09


def _fit_bounds(base_map: folium.Map, data: gpd.GeoDataFrame) -> None:
    """Fit a Folium map to a GeoDataFrame extent."""
    if data.empty:
        return
    minx, miny, maxx, maxy = data.total_bounds
    if any(math.isnan(value) for value in [minx, miny, maxx, maxy]):
        return
    base_map.fit_bounds([[miny, minx], [maxy, maxx]], padding=(12, 12))


def _format_tooltip_value(field: str, value: object) -> object:
    """Format tooltip values without changing the analytical columns."""
    if _is_missing(value):
        return "n/d"
    if field in ["utvi_exploratory", "utvi_setor_exploratory"]:
        return f"{float(value):.3f}"
    if field.startswith("LST_"):
        return f"{float(value):.1f}"
    if field.startswith("pct_") or field.startswith("area_"):
        return f"{float(value):.1f}"
    if "NDVI" in field or "NDBI" in field or "MNDWI" in field:
        return f"{float(value):.3f}"
    return value


def _add_tooltip_display_columns(
    data: gpd.GeoDataFrame,
    fields: list[str],
) -> tuple[gpd.GeoDataFrame, list[str]]:
    """Create formatted tooltip columns for the requested fields."""
    display_data = data.copy()
    display_fields: list[str] = []

    for field in fields:
        display_field = f"tooltip_{field}"
        display_data[display_field] = display_data[field].map(
            lambda value, current_field=field: _format_tooltip_value(current_field, value)
        )
        display_fields.append(display_field)

    return display_data, display_fields


def make_choropleth_map(
    data: gpd.GeoDataFrame,
    variable: str,
    variable_label: str,
    tooltip_fields: list[str],
    tooltip_aliases: Mapping[str, str] | None = None,
    tiles: str = "CartoDB positron",
) -> folium.Map:
    """Create a Folium choropleth for a numeric GeoDataFrame column."""
    if variable not in data.columns:
        raise ValueError(f"Variável ausente na camada espacial: {variable}")

    map_data = data.copy()
    tooltip_fields = [field for field in tooltip_fields if field in map_data.columns]
    map_data, display_tooltip_fields = _add_tooltip_display_columns(map_data, tooltip_fields)

    if map_data.crs and map_data.crs.to_epsg() != 4326:
        map_data = map_data.to_crs(epsg=4326)

    map_data[variable] = pd.to_numeric(map_data[variable], errors="coerce")
    values = map_data[variable].dropna()

    base_map = folium.Map(
        location=PORTO_ALEGRE_CENTER,
        zoom_start=11,
        tiles=tiles,
        control_scale=True,
    )

    if values.empty:
        colormap = cm.LinearColormap(["#f0f0f0", "#969696"], vmin=0, vmax=1)
    else:
        vmin = float(values.quantile(0.02))
        vmax = float(values.quantile(0.98))
        if math.isclose(vmin, vmax):
            vmin = float(values.min())
            vmax = float(values.max())
        if math.isclose(vmin, vmax):
            vmax = vmin + 1
        colormap = _palette_for_variable(variable).scale(vmin, vmax)

    colormap.caption = variable_label

    def style_function(feature: dict) -> dict:
        value = feature["properties"].get(variable)
        fill_color = "#d9d9d9" if _is_missing(value) else colormap(float(value))
        return {
            "fillColor": fill_color,
            "color": "#4a4a4a",
            "weight": 0.6,
            "fillOpacity": 0.72,
        }

    def highlight_function(_: dict) -> dict:
        return {"weight": 2, "color": "#111111", "fillOpacity": 0.82}

    aliases = tooltip_aliases or {}
    tooltip = folium.GeoJsonTooltip(
        fields=display_tooltip_fields,
        aliases=[aliases.get(field.replace("tooltip_", ""), field) for field in display_tooltip_fields],
        localize=False,
        sticky=False,
        labels=True,
        style=(
            "background-color: white; color: #1f2937; "
            "font-family: Arial; font-size: 12px; padding: 8px;"
        ),
    )

    folium.GeoJson(
        map_data,
        name=variable_label,
        style_function=style_function,
        highlight_function=highlight_function,
        tooltip=tooltip,
    ).add_to(base_map)

    colormap.add_to(base_map)
    folium.LayerControl(collapsed=True).add_to(base_map)
    _fit_bounds(base_map, map_data)
    return base_map
