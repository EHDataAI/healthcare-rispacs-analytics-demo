import pandas as pd

from rispacs_demo.analytics import reporting_alerts
from rispacs_demo.synthetic import (
    DemoSpec,
    generate_demo_dataset,
)


def test_active_backlog_is_point_in_time_coherent():
    df = generate_demo_dataset(
        DemoSpec(
            rows=50_000,
            seed=20260928,
        )
    )

    snapshot_at = pd.Timestamp(df["pacs_available_at"].max())

    pending = df["report_status"].eq("PENDING")
    signed = df["report_status"].eq("SIGNED")

    assert pending.any()

    assert (
        df.loc[
            pending,
            "report_signed_at",
        ]
        .isna()
        .all()
    )

    assert (
        df.loc[
            signed,
            "report_signed_at",
        ]
        .notna()
        .all()
    )

    future_signed = signed & (df["report_signed_at"] > snapshot_at)

    assert not future_signed.any()

    pending_age = (
        snapshot_at
        - df.loc[
            pending,
            "pacs_available_at",
        ]
    ).dt.total_seconds() / 3600

    assert pending_age.min() >= 0
    assert pending_age.max() < 168

    alerts = reporting_alerts(
        df,
        warning_hours=24,
        critical_hours=48,
        now=snapshot_at,
    )

    active = alerts.loc[
        alerts["report_status"].eq("PENDING"),
        "operational_state",
    ]

    assert {
        "NORMAL",
        "WARNING",
        "CRITICAL",
    }.issubset(set(active.unique()))


def test_default_snapshot_matches_latest_pacs_event():
    df = generate_demo_dataset(
        DemoSpec(
            rows=10_000,
            seed=20260928,
        )
    )

    snapshot_at = pd.Timestamp(df["pacs_available_at"].max())

    default_result = reporting_alerts(
        df,
        warning_hours=24,
        critical_hours=48,
    ).set_index("accession_alias")

    explicit_result = reporting_alerts(
        df,
        warning_hours=24,
        critical_hours=48,
        now=snapshot_at,
    ).set_index("accession_alias")

    pd.testing.assert_series_equal(
        default_result["operational_state"].sort_index(),
        explicit_result["operational_state"].sort_index(),
    )
