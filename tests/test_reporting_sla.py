import pandas as pd
import pytest

from rispacs_demo.reporting_sla import (
    ReportingSLAConfig,
    active_sla_counts,
    apply_reporting_sla,
    classify_remaining_hours,
    historical_sla_counts,
)

CONFIG = ReportingSLAConfig(
    target_hours=72,
    warning_window_hours=48,
    critical_window_hours=24,
)


def _pending_frame(
    ages_hours: list[float],
    snapshot: pd.Timestamp,
) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "report_status": ["PENDING" for _ in ages_hours],
            "pacs_available_at": [snapshot - pd.Timedelta(hours=age) for age in ages_hours],
            "report_signed_at": [pd.NaT for _ in ages_hours],
        }
    )


def test_config_requires_warning_above_critical_window():
    invalid = ReportingSLAConfig(
        target_hours=72,
        warning_window_hours=24,
        critical_window_hours=48,
    )

    with pytest.raises(ValueError):
        invalid.validate()


def test_remaining_hour_boundaries():
    assert (
        classify_remaining_hours(
            49,
            CONFIG,
        )
        == "NORMAL"
    )

    assert (
        classify_remaining_hours(
            48,
            CONFIG,
        )
        == "WARNING"
    )

    assert (
        classify_remaining_hours(
            25,
            CONFIG,
        )
        == "WARNING"
    )

    assert (
        classify_remaining_hours(
            24,
            CONFIG,
        )
        == "CRITICAL"
    )

    assert (
        classify_remaining_hours(
            1,
            CONFIG,
        )
        == "CRITICAL"
    )

    assert (
        classify_remaining_hours(
            0,
            CONFIG,
        )
        == "BREACHED"
    )

    assert (
        classify_remaining_hours(
            -8,
            CONFIG,
        )
        == "BREACHED"
    )


def test_pending_age_boundaries_map_to_expected_states():
    snapshot = pd.Timestamp("2026-01-01 12:00:00")

    df = _pending_frame(
        ages_hours=[
            0,
            23,
            24,
            47,
            48,
            71,
            72,
            80,
        ],
        snapshot=snapshot,
    )

    result = apply_reporting_sla(
        df,
        config=CONFIG,
        snapshot_at=snapshot,
    )

    assert result["operational_state"].tolist() == [
        "NORMAL",
        "NORMAL",
        "WARNING",
        "WARNING",
        "CRITICAL",
        "CRITICAL",
        "BREACHED",
        "BREACHED",
    ]


def test_signed_reports_use_historical_sla_only():
    snapshot = pd.Timestamp("2026-01-10 12:00:00")

    pacs_time = pd.Timestamp("2026-01-01 00:00:00")

    df = pd.DataFrame(
        {
            "report_status": [
                "SIGNED",
                "SIGNED",
                "SIGNED",
            ],
            "pacs_available_at": [
                pacs_time,
                pacs_time,
                pacs_time,
            ],
            "report_signed_at": [
                pacs_time + pd.Timedelta(hours=71),
                pacs_time + pd.Timedelta(hours=72),
                pacs_time + pd.Timedelta(hours=73),
            ],
        }
    )

    result = apply_reporting_sla(
        df,
        config=CONFIG,
        snapshot_at=snapshot,
    )

    assert result["operational_state"].tolist() == [
        "CLOSED",
        "CLOSED",
        "CLOSED",
    ]

    assert result["historical_sla_state"].tolist() == [
        "CLOSED_WITHIN_SLA",
        "CLOSED_WITHIN_SLA",
        "CLOSED_BREACHED_SLA",
    ]


def test_inconsistent_status_timestamp_is_data_quality():
    snapshot = pd.Timestamp("2026-01-01 12:00:00")

    df = pd.DataFrame(
        {
            "report_status": [
                "PENDING",
                "SIGNED",
            ],
            "pacs_available_at": [
                snapshot - pd.Timedelta(hours=10),
                snapshot - pd.Timedelta(hours=10),
            ],
            "report_signed_at": [
                snapshot - pd.Timedelta(hours=1),
                pd.NaT,
            ],
        }
    )

    result = apply_reporting_sla(
        df,
        config=CONFIG,
        snapshot_at=snapshot,
    )

    assert result["operational_state"].tolist() == [
        "DATA_QUALITY",
        "DATA_QUALITY",
    ]


def test_active_counts_reconcile_pending_states():
    snapshot = pd.Timestamp("2026-01-01 12:00:00")

    df = _pending_frame(
        ages_hours=[
            10,
            30,
            55,
            80,
        ],
        snapshot=snapshot,
    )

    result = apply_reporting_sla(
        df,
        config=CONFIG,
        snapshot_at=snapshot,
    )

    counts = active_sla_counts(result)

    assert counts == {
        "NORMAL": 1,
        "WARNING": 1,
        "CRITICAL": 1,
        "BREACHED": 1,
    }


def test_historical_counts_reconcile_signed_reports():
    snapshot = pd.Timestamp("2026-01-10 12:00:00")

    pacs = pd.Timestamp("2026-01-01 00:00:00")

    df = pd.DataFrame(
        {
            "report_status": [
                "SIGNED",
                "SIGNED",
            ],
            "pacs_available_at": [
                pacs,
                pacs,
            ],
            "report_signed_at": [
                pacs + pd.Timedelta(hours=24),
                pacs + pd.Timedelta(hours=96),
            ],
        }
    )

    result = apply_reporting_sla(
        df,
        config=CONFIG,
        snapshot_at=snapshot,
    )

    counts = historical_sla_counts(result)

    assert counts == {
        "CLOSED_WITHIN_SLA": 1,
        "CLOSED_BREACHED_SLA": 1,
    }
