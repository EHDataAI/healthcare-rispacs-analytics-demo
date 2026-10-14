import pandas as pd

from rispacs_demo.quality import quality_summary
from rispacs_demo.synthetic import (
    DemoSpec,
    generate_demo_dataset,
)


def test_quality_detects_deliberate_issues():
    df = generate_demo_dataset(DemoSpec(rows=3000, seed=11))
    quality = quality_summary(df)

    assert (quality["affected_rows"] > 0).any()
    assert "acquisition_end_before_start" in set(quality["check"])


def test_pending_report_timestamp_null_is_expected():
    df = generate_demo_dataset(DemoSpec(rows=3000, seed=12))
    quality = quality_summary(df)

    checks = quality.set_index("check")

    assert "missing::report_signed_at" not in set(quality["check"])
    assert (
        checks.loc[
            "signed_without_report_timestamp",
            "affected_rows",
        ]
        == 0
    )
    assert (
        checks.loc[
            "pending_with_report_timestamp",
            "affected_rows",
        ]
        == 0
    )


def test_report_status_timestamp_inconsistency_is_detected():
    df = generate_demo_dataset(DemoSpec(rows=3000, seed=13))

    signed_idx = df.index[df["report_status"].eq("SIGNED")][0]
    pending_idx = df.index[df["report_status"].eq("PENDING")][0]

    df.loc[signed_idx, "report_signed_at"] = pd.NaT
    df.loc[
        pending_idx,
        "report_signed_at",
    ] = df.loc[pending_idx, "pacs_available_at"] + pd.Timedelta(hours=1)

    quality = quality_summary(df).set_index("check")

    assert (
        quality.loc[
            "signed_without_report_timestamp",
            "affected_rows",
        ]
        == 1
    )
    assert (
        quality.loc[
            "pending_with_report_timestamp",
            "affected_rows",
        ]
        == 1
    )
