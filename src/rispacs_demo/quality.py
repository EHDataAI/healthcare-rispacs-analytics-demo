from __future__ import annotations

import pandas as pd


def _quality_row(
    check: str,
    affected_rows: int,
    total_rows: int,
    severity_when_affected: str,
) -> dict[str, object]:
    return {
        "check": check,
        "affected_rows": affected_rows,
        "rate": affected_rows / total_rows,
        "severity": severity_when_affected if affected_rows else "PASS",
    }


def quality_summary(df: pd.DataFrame) -> pd.DataFrame:
    n = max(len(df), 1)
    rows: list[dict[str, object]] = []

    state_aware_columns = {"report_signed_at"}

    for col in df.columns:
        if col in state_aware_columns:
            continue

        missing = int(df[col].isna().sum())
        rows.append(
            _quality_row(
                f"missing::{col}",
                missing,
                n,
                "WARN",
            )
        )

    duplicates = int(df["accession_alias"].duplicated().sum()) if "accession_alias" in df else 0
    rows.append(
        _quality_row(
            "duplicate_accession_alias",
            duplicates,
            n,
            "FAIL",
        )
    )

    required_acquisition = {"acquisition_start", "acquisition_end"}
    if required_acquisition.issubset(df.columns):
        invalid_time = int((df["acquisition_end"] < df["acquisition_start"]).sum())
    else:
        invalid_time = 0

    rows.append(
        _quality_row(
            "acquisition_end_before_start",
            invalid_time,
            n,
            "WARN",
        )
    )

    report_columns = {"report_status", "report_signed_at"}
    if report_columns.issubset(df.columns):
        signed_without_timestamp = int(
            (df["report_status"].eq("SIGNED") & df["report_signed_at"].isna()).sum()
        )
        pending_with_timestamp = int(
            (df["report_status"].eq("PENDING") & df["report_signed_at"].notna()).sum()
        )
    else:
        signed_without_timestamp = 0
        pending_with_timestamp = 0

    rows.append(
        _quality_row(
            "signed_without_report_timestamp",
            signed_without_timestamp,
            n,
            "FAIL",
        )
    )
    rows.append(
        _quality_row(
            "pending_with_report_timestamp",
            pending_with_timestamp,
            n,
            "FAIL",
        )
    )

    timing_columns = {
        "report_status",
        "pacs_available_at",
        "report_signed_at",
    }
    if timing_columns.issubset(df.columns):
        signed_before_pacs = int(
            (
                df["report_status"].eq("SIGNED")
                & df["report_signed_at"].notna()
                & df["pacs_available_at"].notna()
                & (df["report_signed_at"] < df["pacs_available_at"])
            ).sum()
        )
    else:
        signed_before_pacs = 0

    rows.append(
        _quality_row(
            "report_signed_before_pacs_available",
            signed_before_pacs,
            n,
            "FAIL",
        )
    )

    return pd.DataFrame(rows)
