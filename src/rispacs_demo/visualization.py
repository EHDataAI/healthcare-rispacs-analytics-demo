from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

MODALITY_ORDER = ["CT", "MR", "US", "CR", "DX"]
SLA_STATE_ORDER = ["NORMAL", "WARNING", "CRITICAL"]

SLA_STATE_COLORS = {
    "NORMAL": "#2E8B57",
    "WARNING": "#D99A2B",
    "CRITICAL": "#C0392B",
}


def _empty_figure(title: str, message: str) -> go.Figure:
    fig = go.Figure()
    fig.update_layout(
        title=title,
        template="plotly_white",
        height=360,
    )
    fig.add_annotation(
        text=message,
        x=0.5,
        y=0.5,
        xref="paper",
        yref="paper",
        showarrow=False,
    )
    return fig


def _present_modalities(df: pd.DataFrame) -> list[str]:
    if "modality" not in df.columns:
        return []

    present = set(df["modality"].dropna().astype(str))
    return [modality for modality in MODALITY_ORDER if modality in present]


def animated_cumulative_volume(
    df: pd.DataFrame,
) -> go.Figure:
    title = "Cumulative study volume by modality"

    if df.empty:
        return _empty_figure(title, "No data for the selected filters.")

    work = df.copy()
    work["exam_datetime"] = pd.to_datetime(
        work["exam_datetime"],
        errors="coerce",
    )

    modalities = _present_modalities(work)

    work = work[work["exam_datetime"].notna() & work["modality"].isin(modalities)].copy()

    if work.empty or not modalities:
        return _empty_figure(title, "No valid modality data available.")

    work["month"] = work["exam_datetime"].dt.to_period("M")

    monthly = (
        work.groupby(
            ["month", "modality"],
            observed=True,
        )
        .size()
        .rename("monthly_studies")
        .reset_index()
    )

    months = pd.period_range(
        start=work["month"].min(),
        end=work["month"].max(),
        freq="M",
    )

    grid = pd.MultiIndex.from_product(
        [months, modalities],
        names=["month", "modality"],
    ).to_frame(index=False)

    monthly = grid.merge(
        monthly,
        on=["month", "modality"],
        how="left",
    )

    monthly["monthly_studies"] = monthly["monthly_studies"].fillna(0).astype(int)

    monthly = monthly.sort_values(["month", "modality"])

    monthly["cumulative_studies"] = monthly.groupby(
        "modality",
        observed=True,
    )["monthly_studies"].cumsum()

    monthly["month_label"] = monthly["month"].dt.strftime("%b %Y")

    month_order = [period.strftime("%b %Y") for period in months]

    y_max = max(
        int(monthly["cumulative_studies"].max()),
        1,
    )

    fig = px.bar(
        monthly,
        x="modality",
        y="cumulative_studies",
        color="modality",
        animation_frame="month_label",
        animation_group="modality",
        category_orders={
            "month_label": month_order,
            "modality": modalities,
        },
        range_y=[0, y_max * 1.10],
        labels={
            "modality": "Modality",
            "cumulative_studies": "Cumulative studies",
            "month_label": "Month",
        },
        title=title,
    )

    fig.update_layout(
        template="plotly_white",
        showlegend=False,
        height=470,
        transition={"duration": 350},
        margin=dict(l=30, r=20, t=70, b=30),
    )

    if fig.layout.sliders:
        fig.layout.sliders[0].currentvalue.prefix = "Month: "

    if fig.layout.updatemenus:
        buttons = fig.layout.updatemenus[0].buttons

        if buttons:
            buttons[0].args[1]["frame"]["duration"] = 550
            buttons[0].args[1]["transition"]["duration"] = 350

    return fig


def monthly_volume_trend(
    df: pd.DataFrame,
) -> go.Figure:
    title = "Monthly study volume"

    if df.empty:
        return _empty_figure(title, "No data for the selected filters.")

    work = df.copy()
    work["exam_datetime"] = pd.to_datetime(
        work["exam_datetime"],
        errors="coerce",
    )

    modalities = _present_modalities(work)

    work = work[work["exam_datetime"].notna() & work["modality"].isin(modalities)].copy()

    if work.empty:
        return _empty_figure(title, "No valid data available.")

    work["month"] = work["exam_datetime"].dt.to_period("M").dt.to_timestamp()

    monthly = (
        work.groupby(
            ["month", "modality"],
            observed=True,
        )
        .size()
        .rename("studies")
        .reset_index()
    )

    fig = px.line(
        monthly,
        x="month",
        y="studies",
        color="modality",
        markers=True,
        category_orders={
            "modality": modalities,
        },
        labels={
            "month": "Month",
            "studies": "Studies",
            "modality": "Modality",
        },
        title=title,
    )

    fig.update_layout(
        template="plotly_white",
        height=420,
        margin=dict(l=30, r=20, t=70, b=30),
    )

    return fig


def modality_volume_chart(
    df: pd.DataFrame,
) -> go.Figure:
    title = "Study volume by modality"

    modalities = _present_modalities(df)

    if df.empty or not modalities:
        return _empty_figure(title, "No modality data available.")

    counts = (
        df.loc[
            df["modality"].isin(modalities),
            "modality",
        ]
        .value_counts()
        .reindex(modalities, fill_value=0)
        .rename_axis("modality")
        .reset_index(name="studies")
    )

    fig = px.bar(
        counts,
        x="modality",
        y="studies",
        labels={
            "modality": "Modality",
            "studies": "Studies",
        },
        title=title,
    )

    fig.update_layout(
        template="plotly_white",
        height=400,
        showlegend=False,
    )

    return fig


def patient_class_chart(
    df: pd.DataFrame,
) -> go.Figure:
    title = "Studies by patient class"

    if df.empty:
        return _empty_figure(title, "No patient-class data available.")

    counts = (
        df["patient_class"]
        .dropna()
        .value_counts()
        .rename_axis("patient_class")
        .reset_index(name="studies")
    )

    fig = px.bar(
        counts,
        x="patient_class",
        y="studies",
        labels={
            "patient_class": "Patient class",
            "studies": "Studies",
        },
        title=title,
    )

    fig.update_layout(
        template="plotly_white",
        height=400,
        showlegend=False,
    )

    return fig


def room_workload_chart(
    df: pd.DataFrame,
) -> go.Figure:
    title = "Room workload"

    if df.empty:
        return _empty_figure(title, "No room data available.")

    counts = (
        df.loc[df["room"].notna(), "room"]
        .value_counts()
        .rename_axis("room")
        .reset_index(name="studies")
    )

    if counts.empty:
        return _empty_figure(title, "No valid room data available.")

    fig = px.bar(
        counts,
        x="studies",
        y="room",
        orientation="h",
        labels={
            "room": "Room",
            "studies": "Studies",
        },
        title=title,
    )

    fig.update_layout(
        template="plotly_white",
        height=max(380, 35 * len(counts)),
        showlegend=False,
        yaxis={"categoryorder": "total ascending"},
    )

    return fig


def current_backlog_chart(
    alerts: pd.DataFrame,
) -> go.Figure:
    title = "Current active reporting backlog"

    if alerts.empty:
        return _empty_figure(title, "No reporting data available.")

    pending = alerts[alerts["report_status"].eq("PENDING")].copy()

    if pending.empty:
        return _empty_figure(title, "No active pending reports.")

    counts = (
        pending["operational_state"]
        .value_counts()
        .reindex(
            SLA_STATE_ORDER,
            fill_value=0,
        )
        .rename_axis("state")
        .reset_index(name="reports")
    )

    fig = px.bar(
        counts,
        x="state",
        y="reports",
        color="state",
        category_orders={
            "state": SLA_STATE_ORDER,
        },
        color_discrete_map=SLA_STATE_COLORS,
        labels={
            "state": "Operational state",
            "reports": "Pending reports",
        },
        title=title,
    )

    fig.update_layout(
        template="plotly_white",
        height=400,
        showlegend=False,
    )

    return fig


def animated_backlog_evolution(
    df: pd.DataFrame,
    warning_hours: float = 24,
    critical_hours: float = 48,
    days: int = 7,
    step_hours: int = 6,
    snapshot_at: pd.Timestamp | None = None,
) -> go.Figure:
    title = "Active reporting backlog evolution"

    if warning_hours >= critical_hours:
        raise ValueError("warning_hours must be lower than critical_hours")

    if df.empty:
        return _empty_figure(title, "No reporting data available.")

    work = df.copy()

    work["pacs_available_at"] = pd.to_datetime(
        work["pacs_available_at"],
        errors="coerce",
    )
    work["report_signed_at"] = pd.to_datetime(
        work["report_signed_at"],
        errors="coerce",
    )

    modalities = _present_modalities(work)

    work = work[work["pacs_available_at"].notna() & work["modality"].isin(modalities)].copy()

    if work.empty or not modalities:
        return _empty_figure(title, "No valid reporting data available.")

    if snapshot_at is None:
        snapshot_at = pd.Timestamp(work["pacs_available_at"].max())

    start_at = snapshot_at - pd.Timedelta(days=days)

    snapshots = pd.date_range(
        start=start_at,
        end=snapshot_at,
        freq=f"{step_hours}h",
    )

    rows: list[pd.DataFrame] = []
    snapshot_order: list[str] = []

    state_grid = pd.MultiIndex.from_product(
        [modalities, SLA_STATE_ORDER],
        names=["modality", "state"],
    ).to_frame(index=False)

    for moment in snapshots:
        label = moment.strftime("%d %b %H:%M")
        snapshot_order.append(label)

        active_mask = work["pacs_available_at"].le(moment) & (
            work["report_signed_at"].isna() | work["report_signed_at"].gt(moment)
        )

        active = work.loc[
            active_mask,
            ["modality", "pacs_available_at"],
        ].copy()

        if active.empty:
            grouped = state_grid.copy()
            grouped["reports"] = 0
        else:
            active["age_hours"] = (moment - active["pacs_available_at"]).dt.total_seconds() / 3600

            active["state"] = np.select(
                [
                    active["age_hours"] >= critical_hours,
                    active["age_hours"] >= warning_hours,
                ],
                [
                    "CRITICAL",
                    "WARNING",
                ],
                default="NORMAL",
            )

            grouped = (
                active.groupby(
                    ["modality", "state"],
                    observed=True,
                )
                .size()
                .rename("reports")
                .reset_index()
            )

            grouped = state_grid.merge(
                grouped,
                on=["modality", "state"],
                how="left",
            )

            grouped["reports"] = grouped["reports"].fillna(0).astype(int)

        grouped["snapshot"] = label
        grouped["animation_key"] = grouped["modality"] + "|" + grouped["state"]

        rows.append(grouped)

    evolution = pd.concat(
        rows,
        ignore_index=True,
    )

    x_max = max(
        int(
            evolution.groupby(
                ["snapshot", "modality"],
                observed=True,
            )["reports"]
            .sum()
            .max()
        ),
        1,
    )

    fig = px.bar(
        evolution,
        x="reports",
        y="modality",
        color="state",
        orientation="h",
        animation_frame="snapshot",
        animation_group="animation_key",
        barmode="stack",
        category_orders={
            "snapshot": snapshot_order,
            "modality": modalities,
            "state": SLA_STATE_ORDER,
        },
        color_discrete_map=SLA_STATE_COLORS,
        range_x=[0, x_max * 1.10],
        labels={
            "reports": "Active pending reports",
            "modality": "Modality",
            "state": "Operational state",
            "snapshot": "Snapshot",
        },
        title=title,
    )

    fig.update_layout(
        template="plotly_white",
        height=470,
        transition={"duration": 300},
        margin=dict(l=30, r=20, t=70, b=30),
    )

    if fig.layout.sliders:
        fig.layout.sliders[0].currentvalue.prefix = "Snapshot: "

    if fig.layout.updatemenus:
        buttons = fig.layout.updatemenus[0].buttons

        if buttons:
            buttons[0].args[1]["frame"]["duration"] = 450
            buttons[0].args[1]["transition"]["duration"] = 300

    return fig


def pending_age_p90_chart(
    alerts: pd.DataFrame,
    warning_hours: float = 24,
    critical_hours: float = 48,
) -> go.Figure:
    title = "Pending report age P90 by modality"

    if alerts.empty:
        return _empty_figure(title, "No reporting data available.")

    pending = alerts[
        alerts["report_status"].eq("PENDING")
        & alerts["report_age_hours"].ge(0)
        & alerts["modality"].isin(MODALITY_ORDER)
    ].copy()

    if pending.empty:
        return _empty_figure(title, "No active pending reports.")

    summary = (
        pending.groupby(
            "modality",
            observed=True,
        )["report_age_hours"]
        .quantile(0.90)
        .rename("p90_age_hours")
        .reset_index()
        .sort_values("p90_age_hours")
    )

    fig = px.bar(
        summary,
        x="p90_age_hours",
        y="modality",
        orientation="h",
        labels={
            "p90_age_hours": "P90 pending age (hours)",
            "modality": "Modality",
        },
        title=title,
    )

    fig.add_vline(
        x=warning_hours,
        line_dash="dash",
        annotation_text=f"Warning {warning_hours:g} h",
        annotation_position="top",
    )

    fig.add_vline(
        x=critical_hours,
        line_dash="dash",
        annotation_text=f"Critical {critical_hours:g} h",
        annotation_position="top right",
    )

    fig.update_layout(
        template="plotly_white",
        height=420,
        showlegend=False,
    )

    return fig


def workflow_stage_summary(
    df: pd.DataFrame,
) -> pd.DataFrame:
    columns = [
        "stage",
        "p50_minutes",
        "p90_minutes",
        "observations",
    ]

    if df.empty:
        return pd.DataFrame(columns=columns)

    work = df.copy()

    stage_values = {
        "Pre-acquisition wait": (
            work["acquisition_start"] - work["exam_datetime"]
        ).dt.total_seconds()
        / 60,
        "Acquisition": (work["acquisition_end"] - work["acquisition_start"]).dt.total_seconds()
        / 60,
        "PACS transfer": (work["pacs_available_at"] - work["acquisition_end"]).dt.total_seconds()
        / 60,
        "Reporting": (work["report_signed_at"] - work["pacs_available_at"]).dt.total_seconds() / 60,
    }

    rows = []

    for stage, values in stage_values.items():
        clean = values.dropna()
        clean = clean[np.isfinite(clean) & clean.ge(0)]

        if clean.empty:
            continue

        rows.append(
            {
                "stage": stage,
                "p50_minutes": float(clean.quantile(0.50)),
                "p90_minutes": float(clean.quantile(0.90)),
                "observations": int(len(clean)),
            }
        )

    return pd.DataFrame(
        rows,
        columns=columns,
    )


def _format_workflow_duration(minutes: float) -> str:
    if minutes >= 60:
        return f"{minutes / 60:.1f} h"

    return f"{minutes:.1f} min"


def animated_workflow_chart(
    df: pd.DataFrame,
) -> go.Figure:
    title = "Workflow progression"

    summary = workflow_stage_summary(df)

    if summary.empty:
        return _empty_figure(
            title,
            "No valid workflow data available.",
        )

    stages = summary["stage"].tolist()

    positions = np.arange(
        len(stages),
        dtype=float,
    )

    p50_labels = [_format_workflow_duration(value) for value in summary["p50_minutes"]]

    p90_labels = [_format_workflow_duration(value) for value in summary["p90_minutes"]]

    metric_labels = [
        f"P50 {p50}<br>P90 {p90}"
        for p50, p90 in zip(
            p50_labels,
            p90_labels,
            strict=True,
        )
    ]

    hover_labels = [
        (f"<b>{stage}</b><br>P50: {p50}<br>P90: {p90}<extra></extra>")
        for stage, p50, p90 in zip(
            stages,
            p50_labels,
            p90_labels,
            strict=True,
        )
    ]

    baseline = go.Scatter(
        x=positions,
        y=np.zeros(len(stages)),
        mode="lines",
        line={
            "width": 3,
            "dash": "dot",
            "color": "rgba(128,128,128,0.40)",
        },
        hoverinfo="skip",
        showlegend=False,
    )

    initial_progress = go.Scatter(
        x=positions[:1],
        y=np.zeros(1),
        mode="lines",
        line={
            "width": 7,
            "color": "#4C78A8",
        },
        hoverinfo="skip",
        showlegend=False,
    )

    initial_nodes = go.Scatter(
        x=positions[:1],
        y=np.zeros(1),
        mode="markers+text",
        marker={
            "size": 26,
            "color": "#4C78A8",
            "line": {
                "width": 2,
                "color": "white",
            },
        },
        text=metric_labels[:1],
        textposition="top center",
        hovertext=hover_labels[:1],
        hovertemplate="%{hovertext}",
        showlegend=False,
    )

    frames: list[go.Frame] = []

    for count in range(
        1,
        len(stages) + 1,
    ):
        progress = go.Scatter(
            x=positions[:count],
            y=np.zeros(count),
            mode="lines",
            line={
                "width": 7,
                "color": "#4C78A8",
            },
            hoverinfo="skip",
            showlegend=False,
        )

        nodes = go.Scatter(
            x=positions[:count],
            y=np.zeros(count),
            mode="markers+text",
            marker={
                "size": 26,
                "color": "#4C78A8",
                "line": {
                    "width": 2,
                    "color": "white",
                },
            },
            text=metric_labels[:count],
            textposition="top center",
            hovertext=hover_labels[:count],
            hovertemplate="%{hovertext}",
            showlegend=False,
        )

        frames.append(
            go.Frame(
                name=str(count),
                data=[
                    progress,
                    nodes,
                ],
                traces=[
                    1,
                    2,
                ],
            )
        )

    slider_steps = []

    for index, stage in enumerate(
        stages,
        start=1,
    ):
        slider_steps.append(
            {
                "args": [
                    [str(index)],
                    {
                        "frame": {
                            "duration": 500,
                            "redraw": True,
                        },
                        "mode": "immediate",
                        "transition": {
                            "duration": 300,
                        },
                    },
                ],
                "label": stage,
                "method": "animate",
            }
        )

    fig = go.Figure(
        data=[
            baseline,
            initial_progress,
            initial_nodes,
        ],
        frames=frames,
    )

    fig.update_layout(
        title=title,
        template="plotly_white",
        height=430,
        xaxis={
            "title": "Workflow stage",
            "tickmode": "array",
            "tickvals": positions,
            "ticktext": stages,
            "range": [
                -0.35,
                len(stages) - 0.65,
            ],
            "fixedrange": True,
        },
        yaxis={
            "visible": False,
            "range": [
                -0.35,
                0.65,
            ],
            "fixedrange": True,
        },
        updatemenus=[
            {
                "type": "buttons",
                "direction": "left",
                "x": 0,
                "y": 1.18,
                "buttons": [
                    {
                        "label": "Play",
                        "method": "animate",
                        "args": [
                            None,
                            {
                                "frame": {
                                    "duration": 700,
                                    "redraw": True,
                                },
                                "transition": {
                                    "duration": 350,
                                },
                                "fromcurrent": False,
                                "mode": "immediate",
                            },
                        ],
                    },
                    {
                        "label": "Pause",
                        "method": "animate",
                        "args": [
                            [None],
                            {
                                "frame": {
                                    "duration": 0,
                                    "redraw": False,
                                },
                                "transition": {
                                    "duration": 0,
                                },
                                "mode": "immediate",
                            },
                        ],
                    },
                ],
            }
        ],
        sliders=[
            {
                "active": 0,
                "currentvalue": {
                    "prefix": "Revealed through: ",
                },
                "pad": {
                    "t": 45,
                },
                "steps": slider_steps,
            }
        ],
        margin={
            "l": 45,
            "r": 45,
            "t": 105,
            "b": 110,
        },
    )

    fig.add_annotation(
        text=("Stage spacing is schematic. P50 and P90 values show the measured duration."),
        x=0.5,
        y=-0.30,
        xref="paper",
        yref="paper",
        showarrow=False,
        font={
            "size": 11,
        },
    )

    return fig


def technical_workflow_latency_chart(
    df: pd.DataFrame,
) -> go.Figure:
    title = "Technical workflow latency"

    summary = workflow_stage_summary(df)

    technical = summary[
        summary["stage"].isin(
            [
                "Pre-acquisition wait",
                "Acquisition",
                "PACS transfer",
            ]
        )
    ].copy()

    if technical.empty:
        return _empty_figure(
            title,
            "No valid technical workflow data available.",
        )

    long = technical.melt(
        id_vars=["stage"],
        value_vars=[
            "p50_minutes",
            "p90_minutes",
        ],
        var_name="percentile",
        value_name="minutes",
    )

    long["percentile"] = long["percentile"].map(
        {
            "p50_minutes": "P50",
            "p90_minutes": "P90",
        }
    )

    stage_order = [
        "Pre-acquisition wait",
        "Acquisition",
        "PACS transfer",
    ]

    fig = px.bar(
        long,
        x="minutes",
        y="stage",
        color="percentile",
        orientation="h",
        barmode="group",
        category_orders={
            "stage": stage_order,
            "percentile": ["P50", "P90"],
        },
        labels={
            "minutes": "Minutes",
            "stage": "Workflow stage",
            "percentile": "Percentile",
        },
        title=title,
    )

    fig.update_layout(
        template="plotly_white",
        height=430,
        yaxis={
            "categoryorder": "array",
            "categoryarray": stage_order[::-1],
        },
        margin=dict(
            l=30,
            r=20,
            t=70,
            b=35,
        ),
    )

    return fig


def reporting_tat_by_modality_chart(
    df: pd.DataFrame,
) -> go.Figure:
    title = "Reporting TAT by modality"

    if df.empty:
        return _empty_figure(
            title,
            "No reporting data available.",
        )

    work = df.copy()

    valid = (
        work["report_status"].eq("SIGNED")
        & work["report_signed_at"].notna()
        & work["pacs_available_at"].notna()
        & work["modality"].isin(MODALITY_ORDER)
    )

    work = work.loc[valid].copy()

    if work.empty:
        return _empty_figure(
            title,
            "No valid signed reports available.",
        )

    work["tat_hours"] = (
        work["report_signed_at"] - work["pacs_available_at"]
    ).dt.total_seconds() / 3600

    work = work[work["tat_hours"].ge(0)]

    if work.empty:
        return _empty_figure(
            title,
            "No valid non-negative reporting TAT is available.",
        )

    summary = (
        work.groupby(
            "modality",
            observed=True,
        )["tat_hours"]
        .quantile([0.50, 0.90])
        .unstack()
        .rename(
            columns={
                0.50: "P50",
                0.90: "P90",
            }
        )
        .reset_index()
    )

    long = summary.melt(
        id_vars=["modality"],
        value_vars=["P50", "P90"],
        var_name="percentile",
        value_name="hours",
    )

    fig = px.bar(
        long,
        x="hours",
        y="modality",
        color="percentile",
        orientation="h",
        barmode="group",
        category_orders={
            "modality": MODALITY_ORDER,
            "percentile": ["P50", "P90"],
        },
        labels={
            "hours": "Hours",
            "modality": "Modality",
            "percentile": "Percentile",
        },
        title=title,
    )

    fig.update_layout(
        template="plotly_white",
        height=430,
        margin=dict(
            l=30,
            r=20,
            t=70,
            b=35,
        ),
    )

    return fig
