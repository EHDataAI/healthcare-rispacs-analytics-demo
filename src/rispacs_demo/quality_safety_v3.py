from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.graph_objects as go

from rispacs_demo.quality import quality_summary

BACKGROUND = "#151D26"
SURFACE = "#1B2530"
TEXT = "#F3F6F8"
MUTED = "#A7B3BE"
BORDER = "#2B3743"
GRID = "#26323D"

PASS_COLOR = "#6FD2B0"
WARN_COLOR = "#F6C85F"
FAIL_COLOR = "#FF6B6B"
BAR_COLOR = "#74A7D8"


QUALITY_CHECKS = [
    (
        "missing::room",
        "Missing room",
        "WARN",
    ),
    (
        "modality_outside_allowed",
        "Modality outside allowed domain",
        "WARN",
    ),
    (
        "acquisition_end_before_start",
        "Acquisition end before start",
        "WARN",
    ),
    (
        "signed_without_report_timestamp",
        "Signed without report timestamp",
        "FAIL",
    ),
    (
        "pending_with_report_timestamp",
        "Pending with report timestamp",
        "FAIL",
    ),
    (
        "report_signed_before_pacs_available",
        "Report signed before PACS available",
        "FAIL",
    ),
]


def _rate(
    affected_rows: int,
    total_rows: int,
) -> float:
    if total_rows <= 0:
        return 0.0

    return affected_rows / total_rows


def _quality_count(
    quality: pd.DataFrame,
    check: str,
) -> int:
    match = quality.loc[
        quality["check"].eq(check),
        "affected_rows",
    ]

    if match.empty:
        return 0

    return int(match.iloc[0])


def _modality_domain_mask(
    df: pd.DataFrame,
    contract: dict[str, Any],
) -> pd.Series:
    mask = pd.Series(
        False,
        index=df.index,
        dtype=bool,
    )

    if "modality" not in df.columns:
        return mask

    allowed = (
        contract.get(
            "rules",
            {},
        )
        .get(
            "modality",
            {},
        )
        .get("allowed")
    )

    if allowed is None:
        return mask

    return df["modality"].notna() & ~df["modality"].isin(allowed)


def build_quality_profile(
    df: pd.DataFrame,
    contract: dict[str, Any],
) -> pd.DataFrame:
    quality = quality_summary(df)

    total_rows = len(df)

    modality_outside = int(
        _modality_domain_mask(
            df,
            contract,
        ).sum()
    )

    counts = {
        "modality_outside_allowed": (modality_outside),
    }

    rows: list[dict[str, object]] = []

    for (
        check,
        label,
        severity_when_affected,
    ) in QUALITY_CHECKS:
        if check in counts:
            affected_rows = int(counts[check])

        else:
            affected_rows = _quality_count(
                quality,
                check,
            )

        status = severity_when_affected if affected_rows else "PASS"

        rows.append(
            {
                "check": check,
                "label": label,
                "affected_rows": (affected_rows),
                "rate": _rate(
                    affected_rows,
                    total_rows,
                ),
                "status": status,
            }
        )

    return pd.DataFrame(rows)


def quality_issue_mask(
    df: pd.DataFrame,
    contract: dict[str, Any],
) -> pd.Series:
    issue = pd.Series(
        False,
        index=df.index,
        dtype=bool,
    )

    if df.empty:
        return issue

    # Missingness is evaluated generically,
    # except report_signed_at because its nullability
    # depends on report state.
    for column in df.columns:
        if column == "report_signed_at":
            continue

        issue |= df[column].isna()

    if "accession_alias" in df.columns:
        issue |= df["accession_alias"].duplicated()

    acquisition_columns = {
        "acquisition_start",
        "acquisition_end",
    }

    if acquisition_columns.issubset(df.columns):
        issue |= (df["acquisition_end"] < df["acquisition_start"]).fillna(False)

    report_columns = {
        "report_status",
        "report_signed_at",
    }

    if report_columns.issubset(df.columns):
        signed = df["report_status"].eq("SIGNED")

        pending = df["report_status"].eq("PENDING")

        issue |= signed & df["report_signed_at"].isna()

        issue |= pending & df["report_signed_at"].notna()

    timing_columns = {
        "report_status",
        "pacs_available_at",
        "report_signed_at",
    }

    if timing_columns.issubset(df.columns):
        issue |= (
            df["report_status"].eq("SIGNED")
            & df["report_signed_at"].notna()
            & df["pacs_available_at"].notna()
            & (df["report_signed_at"] < df["pacs_available_at"])
        )

    rules = contract.get(
        "rules",
        {},
    )

    for column, rule in rules.items():
        if column not in df.columns:
            continue

        allowed = rule.get("allowed")

        if allowed is None:
            continue

        issue |= df[column].notna() & ~df[column].isin(allowed)

    return issue.fillna(False)


def quality_issue_row_count(
    df: pd.DataFrame,
    contract: dict[str, Any],
) -> int:
    return int(
        quality_issue_mask(
            df,
            contract,
        ).sum()
    )


def build_safety_segments(
    df: pd.DataFrame,
) -> pd.DataFrame:
    columns = [
        "segment",
        "completed",
        "total",
        "completion_rate",
    ]

    if "safety_check_complete" not in df.columns:
        return pd.DataFrame(columns=columns)

    safety = df["safety_check_complete"].fillna(False).astype(bool)

    mr_mask = (
        df["modality"].eq("MR")
        if "modality" in df.columns
        else pd.Series(
            False,
            index=df.index,
            dtype=bool,
        )
    )

    segment_masks = [
        (
            "Overall",
            pd.Series(
                True,
                index=df.index,
                dtype=bool,
            ),
        ),
        (
            "MR",
            mr_mask,
        ),
        (
            "Non-MR",
            ~mr_mask,
        ),
    ]

    rows: list[dict[str, object]] = []

    for (
        segment,
        mask,
    ) in segment_masks:
        total = int(mask.sum())

        completed = int(safety.loc[mask].sum())

        completion_rate = completed / total if total else 0.0

        rows.append(
            {
                "segment": segment,
                "completed": (completed),
                "total": total,
                "completion_rate": (completion_rate),
            }
        )

    return pd.DataFrame(
        rows,
        columns=columns,
    )


def safety_summary(
    df: pd.DataFrame,
) -> dict[str, object]:
    segments = build_safety_segments(df)

    if segments.empty:
        return {
            "available": False,
            "overall": None,
            "mr": None,
            "non_mr": None,
            "incomplete": 0,
            "total": len(df),
        }

    indexed = segments.set_index("segment")

    overall = float(
        indexed.loc[
            "Overall",
            "completion_rate",
        ]
    )

    mr = float(
        indexed.loc[
            "MR",
            "completion_rate",
        ]
    )

    non_mr = float(
        indexed.loc[
            "Non-MR",
            "completion_rate",
        ]
    )

    total = int(
        indexed.loc[
            "Overall",
            "total",
        ]
    )

    completed = int(
        indexed.loc[
            "Overall",
            "completed",
        ]
    )

    return {
        "available": True,
        "overall": overall,
        "mr": mr,
        "non_mr": non_mr,
        "incomplete": (total - completed),
        "total": total,
    }


def _figure_layout(
    figure: go.Figure,
    *,
    title: str,
    x_title: str,
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
            "l": 18,
            "r": 24,
            "t": 55,
            "b": 38,
        },
        paper_bgcolor=BACKGROUND,
        plot_bgcolor=BACKGROUND,
        font={
            "color": TEXT,
            "size": 12,
        },
        showlegend=False,
        xaxis={
            "title": x_title,
            "gridcolor": GRID,
            "zeroline": False,
        },
        yaxis={
            "gridcolor": GRID,
            "zeroline": False,
        },
        hoverlabel={
            "bgcolor": SURFACE,
            "bordercolor": BORDER,
            "font": {
                "color": TEXT,
            },
        },
    )

    return figure


def quality_findings_chart(
    profile: pd.DataFrame,
) -> go.Figure:
    plot_df = profile.copy()

    color_map = {
        "PASS": PASS_COLOR,
        "WARN": WARN_COLOR,
        "FAIL": FAIL_COLOR,
    }

    colors = [
        color_map.get(
            str(status),
            BAR_COLOR,
        )
        for status in plot_df["status"]
    ]

    figure = go.Figure(
        go.Bar(
            x=plot_df["affected_rows"],
            y=plot_df["label"],
            orientation="h",
            marker={
                "color": colors,
            },
            text=[f"{int(value):,}" for value in plot_df["affected_rows"]],
            textposition="outside",
            cliponaxis=False,
            hovertemplate=("<b>%{y}</b><br>Affected rows: %{x:,}<extra></extra>"),
        )
    )

    _figure_layout(
        figure,
        title="Data quality findings",
        x_title="Affected rows",
        height=310,
    )

    figure.update_yaxes(
        autorange="reversed",
    )

    return figure


def safety_completion_chart(
    segments: pd.DataFrame,
) -> go.Figure:
    if segments.empty:
        figure = go.Figure()

        _figure_layout(
            figure,
            title=("Safety checklist completion"),
            x_title="Completion (%)",
            height=310,
        )

        figure.add_annotation(
            text=("Safety checklist field is unavailable."),
            x=0.5,
            y=0.5,
            xref="paper",
            yref="paper",
            showarrow=False,
            font={
                "color": MUTED,
            },
        )

        return figure

    rates = segments["completion_rate"] * 100

    figure = go.Figure(
        go.Bar(
            x=rates,
            y=segments["segment"],
            orientation="h",
            marker={
                "color": BAR_COLOR,
            },
            text=[f"{value:.1f}%" for value in rates],
            textposition="inside",
            hovertemplate=("<b>%{y}</b><br>Completion: %{x:.2f}%<extra></extra>"),
        )
    )

    _figure_layout(
        figure,
        title=("Safety checklist completion"),
        x_title="Completion (%)",
        height=310,
    )

    figure.update_xaxes(
        range=[
            0,
            100,
        ],
    )

    figure.update_yaxes(
        autorange="reversed",
    )

    return figure
