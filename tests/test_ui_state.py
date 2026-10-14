from datetime import date

import pytest

from rispacs_demo.synthetic import (
    DemoSpec,
    generate_demo_dataset,
)
from rispacs_demo.ui_state import (
    DashboardFilters,
    apply_dashboard_filters,
    default_dashboard_filters,
)


def test_default_filters_cover_dataset():
    df = generate_demo_dataset(
        DemoSpec(
            rows=5000,
            seed=401,
        )
    )

    filters = default_dashboard_filters(df)

    filtered = apply_dashboard_filters(
        df,
        filters,
    )

    assert len(filtered) == len(df)


def test_filter_signature_is_deterministic():
    filters = DashboardFilters(
        start_date=date(2025, 1, 1),
        end_date=date(2025, 12, 31),
        modalities=("CT", "MR"),
        patient_classes=("OUTPATIENT",),
        rooms=("CT_01",),
    )

    assert filters.signature() == filters.signature()
    assert len(filters.signature()) == 16


def test_filter_signature_changes_with_context():
    first = DashboardFilters(
        start_date=date(2025, 1, 1),
        end_date=date(2025, 12, 31),
        modalities=("CT",),
        patient_classes=("OUTPATIENT",),
        rooms=("CT_01",),
    )

    second = DashboardFilters(
        start_date=date(2025, 1, 1),
        end_date=date(2025, 12, 31),
        modalities=("MR",),
        patient_classes=("OUTPATIENT",),
        rooms=("CT_01",),
    )

    assert first.signature() != second.signature()


def test_invalid_date_range_is_rejected():
    filters = DashboardFilters(
        start_date=date(2025, 12, 31),
        end_date=date(2025, 1, 1),
        modalities=("CT",),
        patient_classes=("OUTPATIENT",),
        rooms=("CT_01",),
    )

    with pytest.raises(ValueError):
        filters.validate()


def test_invalid_sla_window_order_is_rejected():
    filters = DashboardFilters(
        start_date=date(2025, 1, 1),
        end_date=date(2025, 12, 31),
        modalities=("CT",),
        patient_classes=("OUTPATIENT",),
        rooms=("CT_01",),
        target_hours=72,
        warning_window_hours=24,
        critical_window_hours=48,
    )

    with pytest.raises(ValueError):
        filters.validate()


def test_dashboard_filters_restrict_modality():
    df = generate_demo_dataset(
        DemoSpec(
            rows=5000,
            seed=402,
        )
    )

    defaults = default_dashboard_filters(df)

    filters = DashboardFilters(
        start_date=defaults.start_date,
        end_date=defaults.end_date,
        modalities=("MR",),
        patient_classes=defaults.patient_classes,
        rooms=defaults.rooms,
    )

    filtered = apply_dashboard_filters(
        df,
        filters,
    )

    assert not filtered.empty
    assert set(filtered["modality"].unique()) == {"MR"}


def test_empty_modality_selection_returns_empty():
    df = generate_demo_dataset(
        DemoSpec(
            rows=2000,
            seed=403,
        )
    )

    defaults = default_dashboard_filters(df)

    filters = DashboardFilters(
        start_date=defaults.start_date,
        end_date=defaults.end_date,
        modalities=(),
        patient_classes=defaults.patient_classes,
        rooms=defaults.rooms,
    )

    filtered = apply_dashboard_filters(
        df,
        filters,
    )

    assert filtered.empty


def test_default_sla_configuration_is_valid():
    df = generate_demo_dataset(
        DemoSpec(
            rows=1000,
            seed=404,
        )
    )

    filters = default_dashboard_filters(df)

    config = filters.sla_config()

    assert config.target_hours == 72
    assert config.warning_window_hours == 48
    assert config.critical_window_hours == 24
