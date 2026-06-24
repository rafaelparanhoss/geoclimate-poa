"""Plotly chart utilities for the GeoClimate POA dashboard."""

from __future__ import annotations

from collections.abc import Mapping

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def _existing_columns(data: pd.DataFrame, columns: list[str] | None) -> list[str]:
    """Return existing columns from a requested list."""
    if not columns:
        return []
    return [column for column in columns if column in data.columns]


def _apply_layout(fig: go.Figure, title: str | None = None) -> go.Figure:
    """Apply a compact dashboard layout to a Plotly figure."""
    fig.update_layout(
        title=title,
        template="plotly_white",
        margin={"l": 10, "r": 10, "t": 48 if title else 20, "b": 10},
        legend_title_text="",
    )
    return fig


def make_scatter(
    data: pd.DataFrame,
    x: str,
    y: str,
    labels: Mapping[str, str],
    hover_name: str | None = None,
    color: str | None = None,
    hover_data: list[str] | None = None,
    title: str | None = None,
) -> go.Figure:
    """Create a scatter chart with standard styling."""
    plot_data = data.dropna(subset=[x, y]).copy()
    fig = px.scatter(
        plot_data,
        x=x,
        y=y,
        color=color if color in plot_data.columns else None,
        hover_name=hover_name if hover_name in plot_data.columns else None,
        hover_data=_existing_columns(plot_data, hover_data),
        labels=dict(labels),
    )
    fig.update_traces(
        marker={"size": 9, "opacity": 0.78, "line": {"width": 0.5, "color": "white"}}
    )
    return _apply_layout(fig, title)


def make_bar_ranking(
    data: pd.DataFrame,
    label_col: str,
    value_col: str,
    labels: Mapping[str, str],
    title: str | None = None,
    top_n: int = 10,
    hover_data: list[str] | None = None,
) -> go.Figure:
    """Create a horizontal ranking bar chart."""
    plot_data = (
        data.dropna(subset=[label_col, value_col])
        .sort_values(value_col, ascending=False)
        .head(top_n)
        .sort_values(value_col, ascending=True)
    )
    fig = px.bar(
        plot_data,
        x=value_col,
        y=label_col,
        orientation="h",
        color=value_col,
        color_continuous_scale="YlOrRd",
        hover_data=_existing_columns(plot_data, hover_data),
        labels=dict(labels),
    )
    fig.update_layout(coloraxis_showscale=False)
    return _apply_layout(fig, title)


def make_histogram(
    data: pd.DataFrame,
    x: str,
    labels: Mapping[str, str],
    title: str | None = None,
    nbins: int = 25,
) -> go.Figure:
    """Create a histogram for one indicator."""
    plot_data = data.dropna(subset=[x]).copy()
    fig = px.histogram(
        plot_data,
        x=x,
        nbins=nbins,
        color_discrete_sequence=["#d94801"],
        labels=dict(labels),
    )
    return _apply_layout(fig, title)
