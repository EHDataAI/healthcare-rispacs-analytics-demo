from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from rispacs_demo.dimensions_v3 import procedure_display_categories
from rispacs_demo.visualization import workflow_stage_summary

SURFACE = "#151D26"
SURFACE_2 = "#1B2530"
TEXT = "#F3F6F8"
MUTED = "#A7B3BE"
BORDER = "#2B3743"
GRID = "#26323D"

MODALITY_COLORS = {
    "CT": "#74A7D8",
    "MR": "#6FD2B0",
    "US": "#C7A76A",
    "CR": "#A88FD8",
    "DX": "#8FA2B4",
    "UNKNOWN": "#556575",
}

FALLBACK_COLORS = [
    "#74A7D8",
    "#6FD2B0",
    "#C7A76A",
    "#A88FD8",
    "#8FA2B4",
]

PROCEDURE_CATEGORY_COLORS = {
    "CT": MODALITY_COLORS["CT"],
    "MR": MODALITY_COLORS["MR"],
    "ULTRASOUND": MODALITY_COLORS["US"],
    "RADIOGRAPHY": MODALITY_COLORS["DX"],
    "UNKNOWN": MODALITY_COLORS["UNKNOWN"],
    "UNKNOWN PROCEDURE": MODALITY_COLORS["UNKNOWN"],
}


def _base_layout(
    figure: go.Figure,
    title: str,
    height: int = 300,
) -> go.Figure:
    figure.update_layout(
        title={
            "text": title,
            "x": 0.02,
            "xanchor": "left",
        },
        height=height,
        margin={
            "l": 22,
            "r": 18,
            "t": 52,
            "b": 34,
        },
        paper_bgcolor=SURFACE,
        plot_bgcolor=SURFACE,
        font={
            "family": ("Inter, Segoe UI, Arial, sans-serif"),
            "color": TEXT,
            "size": 11,
        },
        title_font={
            "color": TEXT,
            "size": 14,
        },
        legend={
            "font": {
                "color": MUTED,
            },
            "bgcolor": "rgba(0,0,0,0)",
            "borderwidth": 0,
        },
        hoverlabel={
            "bgcolor": SURFACE_2,
            "bordercolor": BORDER,
            "font": {
                "color": TEXT,
            },
        },
    )

    return figure


def _empty_figure(
    title: str,
    message: str,
    height: int = 300,
) -> go.Figure:
    figure = go.Figure()

    figure.add_annotation(
        text=message,
        x=0.5,
        y=0.5,
        xref="paper",
        yref="paper",
        showarrow=False,
        font={
            "color": MUTED,
            "size": 12,
        },
    )

    figure.update_xaxes(visible=False)

    figure.update_yaxes(visible=False)

    return _base_layout(
        figure,
        title=title,
        height=height,
    )


def room_workload_rank_chart(
    df: pd.DataFrame,
    top_n: int = 8,
) -> go.Figure:
    title = "Room workload ranking"

    if df.empty or "room" not in df.columns:
        return _empty_figure(
            title,
            "No room data available.",
        )

    room = df["room"].dropna().astype(str)

    if room.empty:
        return _empty_figure(
            title,
            "No room data available.",
        )

    known_total = len(room)

    counts = room.value_counts().head(top_n).sort_values()

    share = counts / known_total * 100

    figure = go.Figure(
        go.Bar(
            x=counts.values,
            y=counts.index,
            orientation="h",
            marker={
                "color": "#74A7D8",
                "line": {
                    "color": "#9FC5E8",
                    "width": 0.6,
                },
            },
            customdata=share.values,
            text=[f"{value:,}" for value in counts.values],
            textposition="outside",
            textfont={
                "color": TEXT,
                "size": 10,
            },
            cliponaxis=False,
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Studies: %{x:,}<br>"
                "Share of known rooms: "
                "%{customdata:.1f}%"
                "<extra></extra>"
            ),
        )
    )

    figure.update_xaxes(
        title="Studies",
        showgrid=True,
        gridcolor=GRID,
        zeroline=False,
        linecolor=BORDER,
        tickfont={
            "color": MUTED,
        },
        title_font={
            "color": MUTED,
        },
    )

    figure.update_yaxes(
        title=None,
        showgrid=False,
        tickfont={
            "color": TEXT,
        },
    )

    return _base_layout(
        figure,
        title=title,
        height=max(
            290,
            42 * len(counts) + 95,
        ),
    )


def modality_mix_chart(
    df: pd.DataFrame,
) -> go.Figure:
    title = "Modality mix"

    if df.empty or "modality" not in df.columns:
        return _empty_figure(
            title,
            "No modality data available.",
        )

    modality = df["modality"].dropna().astype(str).str.upper()

    if modality.empty:
        return _empty_figure(
            title,
            "No modality data available.",
        )

    counts = modality.value_counts()

    preferred_order = [
        "CT",
        "MR",
        "US",
        "CR",
        "DX",
        "UNKNOWN",
    ]

    labels = [value for value in preferred_order if value in counts.index]

    labels.extend(sorted(value for value in counts.index if value not in labels))

    values = [int(counts.loc[label]) for label in labels]

    colors = [
        MODALITY_COLORS.get(
            label,
            FALLBACK_COLORS[index % len(FALLBACK_COLORS)],
        )
        for index, label in enumerate(labels)
    ]

    figure = go.Figure(
        go.Pie(
            labels=labels,
            values=values,
            hole=0.64,
            sort=False,
            marker={
                "colors": colors,
                "line": {
                    "color": SURFACE,
                    "width": 2,
                },
            },
            text=[
                (
                    f"{value / sum(values):.1%}"
                    if (sum(values) > 0 and value / sum(values) >= 0.02)
                    else ""
                )
                for value in values
            ],
            textinfo="text",
            textfont={
                "color": TEXT,
                "size": 10,
            },
            hovertemplate=(
                "<b>%{label}</b><br>Studies: %{value:,}<br>Share: %{percent}<extra></extra>"
            ),
        )
    )

    figure.add_annotation(
        text=(f"<b>{sum(values):,}</b><br><span style='font-size:10px'>studies</span>"),
        x=0.5,
        y=0.5,
        showarrow=False,
        font={
            "color": TEXT,
            "size": 14,
        },
    )

    figure.update_layout(
        showlegend=True,
        legend={
            "orientation": "h",
            "yanchor": "top",
            "y": -0.05,
            "xanchor": "center",
            "x": 0.5,
        },
    )

    return _base_layout(
        figure,
        title=title,
        height=330,
    )


def monthly_total_volume_chart(
    df: pd.DataFrame,
) -> go.Figure:
    title = "Monthly production trend"

    if df.empty or "exam_datetime" not in df.columns:
        return _empty_figure(
            title,
            "No temporal data available.",
        )

    timestamps = pd.to_datetime(
        df["exam_datetime"],
        errors="coerce",
    ).dropna()

    if timestamps.empty:
        return _empty_figure(
            title,
            "No temporal data available.",
        )

    months = timestamps.dt.to_period("M").dt.to_timestamp()

    counts = months.value_counts().sort_index()

    rolling = counts.rolling(
        window=3,
        min_periods=1,
    ).mean()

    figure = go.Figure()

    figure.add_trace(
        go.Bar(
            x=counts.index,
            y=counts.values,
            name="Monthly volume",
            marker={
                "color": "#315A78",
                "line": {
                    "color": "#5F87A4",
                    "width": 0.5,
                },
            },
            hovertemplate=("<b>%{x|%b %Y}</b><br>Studies: %{y:,}<extra></extra>"),
        )
    )

    figure.add_trace(
        go.Scatter(
            x=rolling.index,
            y=rolling.values,
            name="3-month mean",
            mode="lines+markers",
            line={
                "color": "#C7A76A",
                "width": 2.5,
            },
            marker={
                "color": "#E1C98F",
                "size": 6,
            },
            hovertemplate=("<b>%{x|%b %Y}</b><br>3-month mean: %{y:,.0f}<extra></extra>"),
        )
    )

    figure.update_xaxes(
        title=None,
        showgrid=False,
        linecolor=BORDER,
        tickfont={
            "color": MUTED,
        },
    )

    figure.update_yaxes(
        title="Studies",
        showgrid=True,
        gridcolor=GRID,
        zeroline=False,
        tickfont={
            "color": MUTED,
        },
        title_font={
            "color": MUTED,
        },
    )

    figure.update_layout(
        bargap=0.28,
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.01,
            "xanchor": "right",
            "x": 1,
        },
    )

    return _base_layout(
        figure,
        title=title,
        height=315,
    )


def procedure_group_rank_chart(
    df: pd.DataFrame,
    top_n: int = 7,
) -> go.Figure:
    title = "Procedure category ranking"

    if df.empty or "procedure_group" not in df.columns:
        return _empty_figure(
            title,
            "No procedure group data available.",
        )

    groups = procedure_display_categories(df).dropna().astype(str)

    if groups.empty:
        return _empty_figure(
            title,
            "No procedure group data available.",
        )

    counts = groups.value_counts().head(top_n).sort_values()

    colors = [
        PROCEDURE_CATEGORY_COLORS.get(
            str(label).strip().upper(),
            FALLBACK_COLORS[index % len(FALLBACK_COLORS)],
        )
        for index, label in enumerate(counts.index)
    ]

    figure = go.Figure(
        go.Bar(
            x=counts.values,
            y=counts.index,
            orientation="h",
            marker={
                "color": colors,
            },
            text=[f"{value:,}" for value in counts.values],
            textposition="outside",
            textfont={
                "color": TEXT,
                "size": 10,
            },
            cliponaxis=False,
            hovertemplate=("<b>%{y}</b><br>Studies: %{x:,}<extra></extra>"),
        )
    )

    figure.update_xaxes(
        title="Studies",
        showgrid=True,
        gridcolor=GRID,
        zeroline=False,
        linecolor=BORDER,
        tickfont={
            "color": MUTED,
        },
        title_font={
            "color": MUTED,
        },
    )

    figure.update_yaxes(
        title=None,
        showgrid=False,
        tickfont={
            "color": TEXT,
            "size": 10,
        },
    )

    figure = _base_layout(
        figure,
        title=title,
        height=max(
            290,
            40 * len(counts) + 95,
        ),
    )

    max_value = float(counts.max())

    figure.update_xaxes(
        range=[
            0,
            max_value * 1.18,
        ]
        if max_value > 0
        else None,
    )

    figure.update_layout(
        margin={
            "l": 22,
            "r": 42,
            "t": 52,
            "b": 34,
        },
    )

    return figure


# WORKFLOW_STORYTELLING_V3_BEGIN

WORKFLOW_P50_COLOR = "#74A7D8"
WORKFLOW_P90_COLOR = "#6FD2B0"
WORKFLOW_CONNECTOR_COLOR = "#556575"


def _workflow_dumbbell_chart(
    labels: list[str],
    p50_values: list[float],
    p90_values: list[float],
    title: str,
    x_title: str,
    unit: str,
    height: int,
) -> go.Figure:
    if not labels:
        return _empty_figure(
            title,
            "No valid workflow data available.",
            height=height,
        )

    figure = go.Figure()

    for label, p50_value, p90_value in zip(
        labels,
        p50_values,
        p90_values,
        strict=True,
    ):
        figure.add_trace(
            go.Scatter(
                x=[
                    p50_value,
                    p90_value,
                ],
                y=[
                    label,
                    label,
                ],
                mode="lines",
                line={
                    "color": (WORKFLOW_CONNECTOR_COLOR),
                    "width": 4,
                },
                hoverinfo="skip",
                showlegend=False,
            )
        )

    figure.add_trace(
        go.Scatter(
            x=p50_values,
            y=labels,
            mode="markers+text",
            name="P50",
            marker={
                "symbol": "circle",
                "size": 10,
                "color": WORKFLOW_P50_COLOR,
                "line": {
                    "color": SURFACE,
                    "width": 1,
                },
            },
            text=[f"{value:.1f}" for value in p50_values],
            textposition="middle left",
            textfont={
                "color": MUTED,
                "size": 10,
            },
            cliponaxis=False,
            customdata=labels,
            hovertemplate=(f"<b>%{{customdata}}</b><br>P50: %{{x:.1f}} {unit}<extra></extra>"),
        )
    )

    figure.add_trace(
        go.Scatter(
            x=p90_values,
            y=labels,
            mode="markers+text",
            name="P90",
            marker={
                "symbol": "diamond",
                "size": 11,
                "color": WORKFLOW_P90_COLOR,
                "line": {
                    "color": SURFACE,
                    "width": 1,
                },
            },
            text=[f"{value:.1f}" for value in p90_values],
            textposition="middle right",
            textfont={
                "color": TEXT,
                "size": 10,
            },
            cliponaxis=False,
            customdata=labels,
            hovertemplate=(f"<b>%{{customdata}}</b><br>P90: %{{x:.1f}} {unit}<extra></extra>"),
        )
    )

    maximum = max(
        [
            *p50_values,
            *p90_values,
            1.0,
        ]
    )

    figure.update_xaxes(
        title=x_title,
        range=[
            0,
            maximum * 1.20,
        ],
        showgrid=True,
        gridcolor=GRID,
        zeroline=False,
        linecolor=BORDER,
        tickfont={
            "color": MUTED,
        },
        title_font={
            "color": MUTED,
        },
    )

    figure.update_yaxes(
        title=None,
        showgrid=False,
        categoryorder="array",
        categoryarray=labels[::-1],
        automargin=True,
        tickfont={
            "color": TEXT,
            "size": 10,
        },
    )

    figure.update_layout(
        showlegend=False,
        hovermode="closest",
    )

    figure.add_annotation(
        text=("P50 = circle   |   P90 = diamond"),
        x=1,
        y=1.10,
        xref="paper",
        yref="paper",
        xanchor="right",
        yanchor="bottom",
        showarrow=False,
        font={
            "color": MUTED,
            "size": 9,
        },
    )

    return _base_layout(
        figure,
        title=title,
        height=height,
    )


def workflow_technical_dumbbell_chart(
    df: pd.DataFrame,
) -> go.Figure:
    title = "Technical path"

    summary = workflow_stage_summary(df)

    stage_order = [
        "Pre-acquisition wait",
        "Acquisition",
        "PACS transfer",
    ]

    if summary.empty:
        return _empty_figure(
            title,
            "No valid technical workflow data available.",
            height=320,
        )

    technical = (
        summary[summary["stage"].isin(stage_order)]
        .set_index("stage")
        .reindex(stage_order)
        .dropna(
            subset=[
                "p50_minutes",
                "p90_minutes",
            ]
        )
    )

    if technical.empty:
        return _empty_figure(
            title,
            "No valid technical workflow data available.",
            height=320,
        )

    labels = technical.index.tolist()

    return _workflow_dumbbell_chart(
        labels=labels,
        p50_values=(technical["p50_minutes"].astype(float).tolist()),
        p90_values=(technical["p90_minutes"].astype(float).tolist()),
        title=title,
        x_title="Minutes",
        unit="min",
        height=320,
    )


def workflow_reporting_dumbbell_chart(
    df: pd.DataFrame,
) -> go.Figure:
    title = "Downstream reporting"

    required = {
        "modality",
        "report_status",
        "pacs_available_at",
        "report_signed_at",
    }

    if df.empty or not required.issubset(df.columns):
        return _empty_figure(
            title,
            "No valid reporting data available.",
            height=320,
        )

    work = df.copy()

    work["modality"] = work["modality"].fillna("").astype(str).str.upper().str.strip()

    modality_order = [
        "CT",
        "MR",
        "US",
        "CR",
        "DX",
    ]

    valid = (
        work["report_status"].eq("SIGNED")
        & work["report_signed_at"].notna()
        & work["pacs_available_at"].notna()
        & work["modality"].isin(modality_order)
    )

    work = work.loc[valid].copy()

    if work.empty:
        return _empty_figure(
            title,
            "No valid signed reports available.",
            height=320,
        )

    work["tat_hours"] = (
        work["report_signed_at"] - work["pacs_available_at"]
    ).dt.total_seconds() / 3600

    work = work[work["tat_hours"].notna() & work["tat_hours"].ge(0)].copy()

    if work.empty:
        return _empty_figure(
            title,
            "No valid non-negative reporting TAT available.",
            height=320,
        )

    summary = (
        work.groupby(
            "modality",
            observed=True,
        )["tat_hours"]
        .quantile(
            [
                0.50,
                0.90,
            ]
        )
        .unstack()
        .rename(
            columns={
                0.50: "p50",
                0.90: "p90",
            }
        )
    )

    present_order = [modality for modality in modality_order if modality in summary.index]

    summary = summary.reindex(present_order).dropna(
        subset=[
            "p50",
            "p90",
        ]
    )

    if summary.empty:
        return _empty_figure(
            title,
            "No valid reporting percentile data available.",
            height=320,
        )

    labels = summary.index.tolist()

    return _workflow_dumbbell_chart(
        labels=labels,
        p50_values=(summary["p50"].astype(float).tolist()),
        p90_values=(summary["p90"].astype(float).tolist()),
        title=title,
        x_title="Hours",
        unit="h",
        height=320,
    )


# WORKFLOW_STORYTELLING_V3_END
