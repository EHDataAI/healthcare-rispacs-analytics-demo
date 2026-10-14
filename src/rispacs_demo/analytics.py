from __future__ import annotations

import numpy as np
import pandas as pd


def enrich_metrics(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    out["acquisition_minutes"] = (
        out["acquisition_end"] - out["acquisition_start"]
    ).dt.total_seconds() / 60

    out["report_tat_hours"] = (
        out["report_signed_at"] - out["pacs_available_at"]
    ).dt.total_seconds() / 3600

    return out


def reporting_alerts(
    df: pd.DataFrame,
    warning_hours: float = 24,
    critical_hours: float = 48,
    now: pd.Timestamp | None = None,
) -> pd.DataFrame:
    if warning_hours >= critical_hours:
        raise ValueError("warning_hours must be lower than critical_hours")

    out = enrich_metrics(df)

    if now is None:
        now = pd.Timestamp(out["pacs_available_at"].max())

    pending = out["report_status"].eq("PENDING")
    signed = out["report_status"].eq("SIGNED")
    signed_complete = signed & out["report_tat_hours"].notna()

    pending_age = (now - out["pacs_available_at"]).dt.total_seconds() / 3600

    out["report_age_hours"] = np.where(
        pending,
        pending_age,
        out["report_tat_hours"],
    )

    out["operational_state"] = np.select(
        [
            pending & (out["report_age_hours"] >= critical_hours),
            pending & (out["report_age_hours"] >= warning_hours),
            pending,
        ],
        [
            "CRITICAL",
            "WARNING",
            "NORMAL",
        ],
        default="CLOSED",
    )

    out["historical_sla_state"] = np.select(
        [
            signed_complete & (out["report_tat_hours"] >= critical_hours),
            signed_complete,
            signed,
        ],
        [
            "CLOSED_BREACHED_SLA",
            "CLOSED_WITHIN_SLA",
            "DATA_QUALITY",
        ],
        default="NOT_APPLICABLE",
    )

    out["report_state"] = np.select(
        [
            pending & (out["report_age_hours"] >= critical_hours),
            pending & (out["report_age_hours"] >= warning_hours),
            pending,
            signed_complete & (out["report_tat_hours"] >= critical_hours),
            signed_complete,
            signed,
        ],
        [
            "PENDING_CRITICAL",
            "PENDING_WARNING",
            "PENDING_NORMAL",
            "CLOSED_BREACHED_SLA",
            "CLOSED_WITHIN_SLA",
            "DATA_QUALITY",
        ],
        default="DATA_QUALITY",
    )

    # Compatibility field used by the current public UI.
    # It represents only the active operational alarm state.
    out["sla_state"] = out["operational_state"]

    active_priority = (
        out["ges_flag"].astype(int) * 3
        + out["patient_class"].eq("EMERGENCY").astype(int) * 2
        + out["operational_state"].eq("WARNING").astype(int) * 2
        + out["operational_state"].eq("CRITICAL").astype(int) * 4
    )

    out["priority_score"] = np.where(
        pending,
        active_priority,
        0,
    )

    out["is_pending"] = pending

    return out.sort_values(
        [
            "is_pending",
            "priority_score",
            "report_age_hours",
        ],
        ascending=[False, False, False],
    )


def executive_kpis(
    df: pd.DataFrame,
) -> dict[str, float | int]:
    metrics = enrich_metrics(df)

    signed_tat = metrics.loc[
        metrics["report_status"].eq("SIGNED"),
        "report_tat_hours",
    ].dropna()

    signed_tat = signed_tat[signed_tat >= 0]

    acquisition = metrics["acquisition_minutes"].dropna()
    acquisition = acquisition[acquisition >= 0]

    return {
        "studies": int(len(metrics)),
        "pending_reports": int(metrics["report_status"].eq("PENDING").sum()),
        "ges_labeled": int(metrics["ges_flag"].sum()),
        "median_report_tat_h": (float(signed_tat.median()) if len(signed_tat) else 0.0),
        "p90_report_tat_h": (float(signed_tat.quantile(0.90)) if len(signed_tat) else 0.0),
        "median_acquisition_min": (float(acquisition.median()) if len(acquisition) else 0.0),
    }
