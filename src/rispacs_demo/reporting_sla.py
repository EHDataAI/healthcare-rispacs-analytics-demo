from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

ACTIVE_SLA_STATES = [
    "NORMAL",
    "WARNING",
    "CRITICAL",
    "BREACHED",
]

HISTORICAL_SLA_STATES = [
    "CLOSED_WITHIN_SLA",
    "CLOSED_BREACHED_SLA",
]


@dataclass(frozen=True)
class ReportingSLAConfig:
    target_hours: float = 72.0
    warning_window_hours: float = 48.0
    critical_window_hours: float = 24.0

    def validate(self) -> None:
        values = [
            self.target_hours,
            self.warning_window_hours,
            self.critical_window_hours,
        ]

        if not all(np.isfinite(value) for value in values):
            raise ValueError("SLA configuration values must be finite.")

        if self.target_hours <= 0:
            raise ValueError("target_hours must be greater than zero.")

        if self.warning_window_hours <= 0:
            raise ValueError("warning_window_hours must be greater than zero.")

        if self.critical_window_hours <= 0:
            raise ValueError("critical_window_hours must be greater than zero.")

        if self.warning_window_hours >= self.target_hours:
            raise ValueError("warning_window_hours must be lower than target_hours.")

        if self.critical_window_hours >= self.warning_window_hours:
            raise ValueError("critical_window_hours must be lower than warning_window_hours.")


DEFAULT_REPORTING_SLA = ReportingSLAConfig()


def classify_remaining_hours(
    remaining_hours: float,
    config: ReportingSLAConfig = DEFAULT_REPORTING_SLA,
) -> str:
    config.validate()

    if not np.isfinite(remaining_hours):
        return "DATA_QUALITY"

    if remaining_hours <= 0:
        return "BREACHED"

    if remaining_hours <= config.critical_window_hours:
        return "CRITICAL"

    if remaining_hours <= config.warning_window_hours:
        return "WARNING"

    return "NORMAL"


def _empty_result(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    out["report_age_hours"] = pd.Series(dtype="float64")
    out["sla_remaining_hours"] = pd.Series(dtype="float64")
    out["report_tat_hours"] = pd.Series(dtype="float64")
    out["operational_state"] = pd.Series(dtype="object")
    out["historical_sla_state"] = pd.Series(dtype="object")
    out["report_state"] = pd.Series(dtype="object")

    return out


def apply_reporting_sla(
    df: pd.DataFrame,
    config: ReportingSLAConfig = DEFAULT_REPORTING_SLA,
    snapshot_at: pd.Timestamp | None = None,
) -> pd.DataFrame:
    config.validate()

    required = {
        "report_status",
        "pacs_available_at",
        "report_signed_at",
    }

    missing = required.difference(df.columns)

    if missing:
        missing_text = ", ".join(sorted(missing))
        raise ValueError(f"Missing required columns: {missing_text}")

    if df.empty:
        return _empty_result(df)

    out = df.copy()

    out["pacs_available_at"] = pd.to_datetime(
        out["pacs_available_at"],
        errors="coerce",
    )

    out["report_signed_at"] = pd.to_datetime(
        out["report_signed_at"],
        errors="coerce",
    )

    if snapshot_at is None:
        snapshot_at = out["pacs_available_at"].max()

    snapshot_at = pd.Timestamp(snapshot_at)

    if pd.isna(snapshot_at):
        raise ValueError("snapshot_at could not be resolved.")

    out["report_age_hours"] = np.nan
    out["sla_remaining_hours"] = np.nan
    out["report_tat_hours"] = np.nan
    out["operational_state"] = "DATA_QUALITY"
    out["historical_sla_state"] = "NOT_APPLICABLE"
    out["report_state"] = "DATA_QUALITY"

    pending_mask = out["report_status"].eq("PENDING")

    valid_pending = (
        pending_mask
        & out["pacs_available_at"].notna()
        & out["report_signed_at"].isna()
        & out["pacs_available_at"].le(snapshot_at)
    )

    pending_age = (
        snapshot_at
        - out.loc[
            valid_pending,
            "pacs_available_at",
        ]
    ).dt.total_seconds() / 3600

    out.loc[
        valid_pending,
        "report_age_hours",
    ] = pending_age

    remaining = config.target_hours - pending_age

    out.loc[
        valid_pending,
        "sla_remaining_hours",
    ] = remaining

    pending_states = remaining.map(
        lambda value: classify_remaining_hours(
            float(value),
            config,
        )
    )

    out.loc[
        valid_pending,
        "operational_state",
    ] = pending_states

    out.loc[
        valid_pending,
        "report_state",
    ] = "PENDING_" + pending_states.astype(str)

    signed_mask = out["report_status"].eq("SIGNED")

    valid_signed = (
        signed_mask
        & out["pacs_available_at"].notna()
        & out["report_signed_at"].notna()
        & out["report_signed_at"].ge(out["pacs_available_at"])
        & out["report_signed_at"].le(snapshot_at)
    )

    signed_tat = (
        out.loc[
            valid_signed,
            "report_signed_at",
        ]
        - out.loc[
            valid_signed,
            "pacs_available_at",
        ]
    ).dt.total_seconds() / 3600

    out.loc[
        valid_signed,
        "report_tat_hours",
    ] = signed_tat

    within_sla = valid_signed & out["report_tat_hours"].le(config.target_hours)

    breached_sla = valid_signed & out["report_tat_hours"].gt(config.target_hours)

    out.loc[
        valid_signed,
        "operational_state",
    ] = "CLOSED"

    out.loc[
        within_sla,
        "historical_sla_state",
    ] = "CLOSED_WITHIN_SLA"

    out.loc[
        breached_sla,
        "historical_sla_state",
    ] = "CLOSED_BREACHED_SLA"

    out.loc[
        valid_signed,
        "report_state",
    ] = out.loc[
        valid_signed,
        "historical_sla_state",
    ]

    return out


def active_sla_counts(
    sla_df: pd.DataFrame,
) -> dict[str, int]:
    if "operational_state" not in sla_df.columns:
        raise ValueError("operational_state column is required.")

    counts = (
        sla_df["operational_state"]
        .value_counts()
        .reindex(
            ACTIVE_SLA_STATES,
            fill_value=0,
        )
    )

    return {state: int(counts.loc[state]) for state in ACTIVE_SLA_STATES}


def historical_sla_counts(
    sla_df: pd.DataFrame,
) -> dict[str, int]:
    if "historical_sla_state" not in sla_df.columns:
        raise ValueError("historical_sla_state column is required.")

    counts = (
        sla_df["historical_sla_state"]
        .value_counts()
        .reindex(
            HISTORICAL_SLA_STATES,
            fill_value=0,
        )
    )

    return {state: int(counts.loc[state]) for state in HISTORICAL_SLA_STATES}
