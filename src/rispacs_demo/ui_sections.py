from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from rispacs_demo.analytics import executive_kpis
from rispacs_demo.reporting_sla import (
    active_sla_counts,
    historical_sla_counts,
)
from rispacs_demo.visualization import workflow_stage_summary


@dataclass(frozen=True)
class MetricCard:
    label: str
    value: str
    help_text: str | None = None


def format_count(
    value: int | float,
) -> str:
    return f"{int(value):,}"


def format_hours(
    value: float | int | None,
) -> str:
    if value is None or pd.isna(value):
        return "N/A"

    return f"{float(value):.1f} h"


def format_minutes(
    value: float | int | None,
) -> str:
    if value is None or pd.isna(value):
        return "N/A"

    value = float(value)

    if value >= 60:
        return f"{value / 60:.1f} h"

    return f"{value:.1f} min"


def build_executive_cards(
    df: pd.DataFrame,
    sla_df: pd.DataFrame,
) -> list[MetricCard]:
    kpis = executive_kpis(df)
    active = active_sla_counts(sla_df)

    pending = sum(active.values())

    return [
        MetricCard(
            label="Studies",
            value=format_count(kpis["studies"]),
            help_text=("Studies in the currently applied analytical slice."),
        ),
        MetricCard(
            label="Pending reports",
            value=format_count(pending),
            help_text=("Reports pending at the operational snapshot."),
        ),
        MetricCard(
            label="Reporting TAT P50",
            value=format_hours(kpis["median_report_tat_h"]),
            help_text=("Median PACS-available-to-report-signature turnaround."),
        ),
        MetricCard(
            label="Reporting TAT P90",
            value=format_hours(kpis["p90_report_tat_h"]),
            help_text=("90th percentile PACS-available-to-report-signature turnaround."),
        ),
        MetricCard(
            label="Breached",
            value=format_count(active["BREACHED"]),
            help_text=(
                "Pending reports that have exceeded the configured synthetic reporting target."
            ),
        ),
    ]


def build_reporting_cards(
    sla_df: pd.DataFrame,
) -> list[MetricCard]:
    active = active_sla_counts(sla_df)

    pending_mask = sla_df["report_status"].eq("PENDING")

    pending_total = int(pending_mask.sum())

    if "ges_flag" in sla_df.columns:
        ges_pending = int((pending_mask & sla_df["ges_flag"].fillna(False).astype(bool)).sum())
    else:
        ges_pending = 0

    return [
        MetricCard(
            label="Pending reports",
            value=format_count(pending_total),
            help_text=("Total active pending reports in the applied analytical context."),
        ),
        MetricCard(
            label="Normal",
            value=format_count(active["NORMAL"]),
            help_text=("Pending reports outside the warning window."),
        ),
        MetricCard(
            label="Warning",
            value=format_count(active["WARNING"]),
            help_text=("Pending reports inside the configured warning window."),
        ),
        MetricCard(
            label="Critical",
            value=format_count(active["CRITICAL"]),
            help_text=("Pending reports inside the configured critical window."),
        ),
        MetricCard(
            label="Breached",
            value=format_count(active["BREACHED"]),
            help_text=("Pending reports beyond the configured reporting target."),
        ),
        MetricCard(
            label="GES-tagged pending",
            value=format_count(ges_pending),
            help_text=(
                "Subset of Pending reports carrying "
                "synthetic GES demo metadata. "
                "This is not a legal GES compliance "
                "indicator."
            ),
        ),
    ]


def build_historical_reporting_cards(
    sla_df: pd.DataFrame,
) -> list[MetricCard]:
    historical = historical_sla_counts(sla_df)

    within = historical["CLOSED_WITHIN_SLA"]
    breached = historical["CLOSED_BREACHED_SLA"]

    total = within + breached

    compliance = 100 * within / total if total > 0 else float("nan")

    return [
        MetricCard(
            label="Closed within target",
            value=format_count(within),
        ),
        MetricCard(
            label="Closed beyond target",
            value=format_count(breached),
        ),
        MetricCard(
            label="Historical compliance",
            value=(f"{compliance:.1f}%" if pd.notna(compliance) else "N/A"),
            help_text=(
                "Synthetic operational target compliance. "
                "Not a statutory or GES compliance measure."
            ),
        ),
    ]


def build_workflow_table(
    df: pd.DataFrame,
) -> pd.DataFrame:
    summary = workflow_stage_summary(df)

    if summary.empty:
        return pd.DataFrame(
            columns=[
                "Workflow stage",
                "P50",
                "P90",
                "Observations",
            ]
        )

    output = summary.copy()

    output["P50"] = output["p50_minutes"].map(format_minutes)

    output["P90"] = output["p90_minutes"].map(format_minutes)

    output = output[
        [
            "stage",
            "P50",
            "P90",
            "observations",
        ]
    ].rename(
        columns={
            "stage": "Workflow stage",
            "observations": "Observations",
        }
    )

    return output


def reporting_reconciliation(
    sla_df: pd.DataFrame,
) -> dict[str, int]:
    active = active_sla_counts(sla_df)

    pending = int(sla_df["report_status"].eq("PENDING").sum())

    active_total = sum(active.values())

    data_quality_pending = int(
        (
            sla_df["report_status"].eq("PENDING") & sla_df["operational_state"].eq("DATA_QUALITY")
        ).sum()
    )

    return {
        "pending_total": pending,
        "classified_active": active_total,
        "pending_data_quality": data_quality_pending,
        "reconciled_total": (active_total + data_quality_pending),
    }
