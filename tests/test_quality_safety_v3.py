import pandas as pd

from rispacs_demo.quality_safety_v3 import (
    build_quality_profile,
    build_safety_segments,
    quality_findings_chart,
    quality_issue_row_count,
    safety_completion_chart,
    safety_summary,
)


def _contract() -> dict[str, object]:
    return {
        "rules": {
            "modality": {
                "allowed": [
                    "CT",
                    "MR",
                    "US",
                    "CR",
                    "DX",
                ],
            },
            "report_status": {
                "allowed": [
                    "PENDING",
                    "SIGNED",
                ],
            },
        },
    }


def _frame() -> pd.DataFrame:
    base = pd.Timestamp("2026-01-01 08:00:00")

    return pd.DataFrame(
        {
            "accession_alias": [
                "A1",
                "A2",
                "A3",
                "A4",
            ],
            "exam_datetime": [
                base,
                base,
                base,
                base,
            ],
            "modality": [
                "CT",
                "UNKNOWN",
                "MR",
                "US",
            ],
            "room": [
                "CT_01",
                None,
                "MR_01",
                "US_01",
            ],
            "patient_class": [
                "OUTPATIENT",
                "OUTPATIENT",
                "EMERGENCY",
                "INPATIENT",
            ],
            "acquisition_start": [
                base + pd.Timedelta(minutes=10),
                base + pd.Timedelta(minutes=15),
                base + pd.Timedelta(minutes=20),
                base + pd.Timedelta(minutes=30),
            ],
            "acquisition_end": [
                base + pd.Timedelta(minutes=30),
                base + pd.Timedelta(minutes=35),
                base + pd.Timedelta(minutes=40),
                base + pd.Timedelta(minutes=25),
            ],
            "pacs_available_at": [
                base + pd.Timedelta(hours=2),
                base + pd.Timedelta(hours=2),
                base + pd.Timedelta(hours=2),
                base + pd.Timedelta(hours=3),
            ],
            "report_signed_at": pd.to_datetime(
                [
                    base + pd.Timedelta(hours=3),
                    None,
                    base + pd.Timedelta(hours=5),
                    base + pd.Timedelta(hours=2),
                ]
            ),
            "report_status": [
                "SIGNED",
                "PENDING",
                "PENDING",
                "SIGNED",
            ],
            "ges_flag": [
                False,
                False,
                True,
                False,
            ],
            "safety_check_complete": [
                True,
                True,
                False,
                True,
            ],
            "procedure_group": [
                "CROSS_SECTIONAL",
                "CROSS_SECTIONAL",
                "CROSS_SECTIONAL",
                "ULTRASOUND",
            ],
        }
    )


def test_quality_profile_contains_expected_findings():
    profile = build_quality_profile(
        _frame(),
        _contract(),
    ).set_index("check")

    assert (
        profile.loc[
            "missing::room",
            "affected_rows",
        ]
        == 1
    )

    assert (
        profile.loc[
            "modality_outside_allowed",
            "affected_rows",
        ]
        == 1
    )

    assert (
        profile.loc[
            "acquisition_end_before_start",
            "affected_rows",
        ]
        == 1
    )

    assert (
        profile.loc[
            "pending_with_report_timestamp",
            "affected_rows",
        ]
        == 1
    )

    assert (
        profile.loc[
            "report_signed_before_pacs_available",
            "affected_rows",
        ]
        == 1
    )


def test_quality_issue_rows_are_unique():
    affected = quality_issue_row_count(
        _frame(),
        _contract(),
    )

    assert affected == 3


def test_safety_summary_and_segments():
    df = _frame()

    summary = safety_summary(df)

    segments = build_safety_segments(df).set_index("segment")

    assert summary["available"]

    assert summary["overall"] == 0.75

    assert summary["incomplete"] == 1

    assert (
        segments.loc[
            "MR",
            "completion_rate",
        ]
        == 0.0
    )

    assert (
        segments.loc[
            "Non-MR",
            "completion_rate",
        ]
        == 1.0
    )


def test_quality_findings_chart_is_valid():
    profile = build_quality_profile(
        _frame(),
        _contract(),
    )

    figure = quality_findings_chart(profile)

    assert figure.layout.title.text == "Data quality findings"

    assert figure.layout.xaxis.title.text == "Affected rows"

    assert len(figure.data) == 1


def test_safety_completion_chart_is_valid():
    segments = build_safety_segments(_frame())

    figure = safety_completion_chart(segments)

    assert figure.layout.title.text == "Safety checklist completion"

    assert figure.layout.xaxis.title.text == "Completion (%)"

    assert len(figure.data) == 1
