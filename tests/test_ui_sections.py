from rispacs_demo.reporting_sla import (
    ReportingSLAConfig,
    apply_reporting_sla,
)
from rispacs_demo.synthetic import (
    DemoSpec,
    generate_demo_dataset,
)
from rispacs_demo.ui_helpers import (
    operational_subset,
)
from rispacs_demo.ui_sections import (
    build_executive_cards,
    build_historical_reporting_cards,
    build_reporting_cards,
    build_workflow_table,
    format_hours,
    format_minutes,
    reporting_reconciliation,
)

CONFIG = ReportingSLAConfig(
    target_hours=72,
    warning_window_hours=48,
    critical_window_hours=24,
)


def _demo_context(
    seed: int,
    rows: int = 5000,
):
    df = generate_demo_dataset(
        DemoSpec(
            rows=rows,
            seed=seed,
        )
    )

    snapshot = df["pacs_available_at"].max()

    sla_df = apply_reporting_sla(
        df,
        config=CONFIG,
        snapshot_at=snapshot,
    )

    return df, sla_df


def test_duration_formatters():
    assert format_minutes(15) == "15.0 min"
    assert format_minutes(90) == "1.5 h"
    assert format_hours(7) == "7.0 h"


def test_executive_cards_have_expected_labels():
    df, sla_df = _demo_context(seed=501)

    cards = build_executive_cards(
        df,
        sla_df,
    )

    labels = [card.label for card in cards]

    assert labels == [
        "Studies",
        "Pending reports",
        "Reporting TAT P50",
        "Reporting TAT P90",
        "Breached",
    ]


def test_reporting_cards_have_all_active_states():
    _, sla_df = _demo_context(seed=502)

    cards = build_reporting_cards(sla_df)

    labels = [card.label for card in cards]

    assert labels == [
        "Pending reports",
        "Normal",
        "Warning",
        "Critical",
        "Breached",
        "GES-tagged pending",
    ]


def test_reporting_reconciliation_matches_pending():
    _, sla_df = _demo_context(seed=503)

    reconciliation = reporting_reconciliation(sla_df)

    assert reconciliation["reconciled_total"] == reconciliation["pending_total"]


def test_historical_reporting_cards_exist():
    _, sla_df = _demo_context(seed=504)

    cards = build_historical_reporting_cards(sla_df)

    assert len(cards) == 3

    assert cards[0].label == ("Closed within target")

    assert cards[1].label == ("Closed beyond target")

    assert cards[2].label == ("Historical compliance")


def test_workflow_table_contains_expected_stages():
    df, _ = _demo_context(seed=505)

    operational = operational_subset(df)

    table = build_workflow_table(operational)

    assert not table.empty

    assert set(table["Workflow stage"]) == {
        "Pre-acquisition wait",
        "Acquisition",
        "PACS transfer",
        "Reporting",
    }

    assert list(table.columns) == [
        "Workflow stage",
        "P50",
        "P90",
        "Observations",
    ]


def test_reporting_cards_pending_total_and_ges_subset():
    _, sla_df = _demo_context(seed=506)

    cards = build_reporting_cards(sla_df)

    values = {
        card.label: int(
            str(card.value).replace(
                ",",
                "",
            )
        )
        for card in cards
    }

    reconciliation = reporting_reconciliation(sla_df)

    assert values["Pending reports"] == reconciliation["pending_total"]

    assert values["GES-tagged pending"] <= values["Pending reports"]

    assert (
        values["Normal"]
        + values["Warning"]
        + values["Critical"]
        + values["Breached"]
        + reconciliation["pending_data_quality"]
        == values["Pending reports"]
    )
