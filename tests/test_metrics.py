import pandas as pd

from rispacs_demo.analytics import (
    executive_kpis,
    reporting_alerts,
)
from rispacs_demo.synthetic import (
    DemoSpec,
    generate_demo_dataset,
)


def test_metrics_are_computable():
    df = generate_demo_dataset(DemoSpec(rows=1000, seed=7))
    kpi = executive_kpis(df)

    assert kpi["studies"] == 1000
    assert kpi["pending_reports"] >= 0
    assert kpi["p90_report_tat_h"] >= kpi["median_report_tat_h"]


def test_reporting_alert_states():
    df = generate_demo_dataset(DemoSpec(rows=500, seed=9))

    alerts = reporting_alerts(
        df,
        warning_hours=24,
        critical_hours=48,
        now=pd.Timestamp("2026-01-03"),
    )

    allowed = {
        "NORMAL",
        "WARNING",
        "CRITICAL",
        "CLOSED",
    }

    assert set(alerts["operational_state"].unique()).issubset(allowed)


def test_reporting_sla_boundaries_and_closed_states():
    now = pd.Timestamp("2026-01-03 00:00:00")

    rows = [
        {
            "accession_alias": "ACC-P1",
            "age": pd.Timedelta(
                hours=23,
                minutes=59,
                seconds=59,
            ),
            "status": "PENDING",
            "tat": None,
        },
        {
            "accession_alias": "ACC-P2",
            "age": pd.Timedelta(hours=24),
            "status": "PENDING",
            "tat": None,
        },
        {
            "accession_alias": "ACC-P3",
            "age": pd.Timedelta(
                hours=47,
                minutes=59,
                seconds=59,
            ),
            "status": "PENDING",
            "tat": None,
        },
        {
            "accession_alias": "ACC-P4",
            "age": pd.Timedelta(hours=48),
            "status": "PENDING",
            "tat": None,
        },
        {
            "accession_alias": "ACC-S1",
            "age": pd.Timedelta(hours=60),
            "status": "SIGNED",
            "tat": pd.Timedelta(hours=10),
        },
        {
            "accession_alias": "ACC-S2",
            "age": pd.Timedelta(hours=60),
            "status": "SIGNED",
            "tat": pd.Timedelta(hours=52),
        },
    ]

    records = []

    for row in rows:
        pacs_at = now - row["age"]

        report_signed_at = pacs_at + row["tat"] if row["tat"] is not None else pd.NaT

        records.append(
            {
                "accession_alias": row["accession_alias"],
                "exam_datetime": pacs_at,
                "modality": "CT",
                "room": "CT_01",
                "patient_class": "OUTPATIENT",
                "acquisition_start": pacs_at - pd.Timedelta(minutes=20),
                "acquisition_end": pacs_at - pd.Timedelta(minutes=5),
                "pacs_available_at": pacs_at,
                "report_signed_at": report_signed_at,
                "report_status": row["status"],
                "ges_flag": False,
                "safety_check_complete": True,
                "procedure_group": "CROSS_SECTIONAL",
            }
        )

    df = pd.DataFrame(records)

    result = reporting_alerts(
        df,
        warning_hours=24,
        critical_hours=48,
        now=now,
    ).set_index("accession_alias")

    assert result.loc["ACC-P1", "report_state"] == "PENDING_NORMAL"
    assert result.loc["ACC-P2", "report_state"] == "PENDING_WARNING"
    assert result.loc["ACC-P3", "report_state"] == "PENDING_WARNING"
    assert result.loc["ACC-P4", "report_state"] == "PENDING_CRITICAL"
    assert result.loc["ACC-S1", "report_state"] == "CLOSED_WITHIN_SLA"
    assert result.loc["ACC-S2", "report_state"] == "CLOSED_BREACHED_SLA"

    assert result.loc["ACC-S1", "operational_state"] == "CLOSED"
    assert result.loc["ACC-S2", "operational_state"] == "CLOSED"


def test_invalid_sla_thresholds_are_rejected():
    df = generate_demo_dataset(DemoSpec(rows=100, seed=21))

    try:
        reporting_alerts(
            df,
            warning_hours=48,
            critical_hours=24,
        )
    except ValueError:
        pass
    else:
        raise AssertionError("Invalid SLA thresholds were not rejected")
