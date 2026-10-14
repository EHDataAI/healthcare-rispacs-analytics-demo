import pandas as pd

from rispacs_demo.synthetic import (
    DemoSpec,
    generate_demo_dataset,
)
from rispacs_demo.ui_helpers import (
    apply_filters,
    operational_subset,
    sorted_options,
)


def test_apply_filters_restricts_modality_and_patient_class():
    df = generate_demo_dataset(
        DemoSpec(
            rows=5000,
            seed=201,
        )
    )

    filtered = apply_filters(
        df,
        modalities=["MR"],
        patient_classes=["OUTPATIENT"],
    )

    assert not filtered.empty
    assert set(filtered["modality"].unique()) == {"MR"}
    assert set(filtered["patient_class"].unique()) == {"OUTPATIENT"}


def test_empty_modality_selection_returns_empty_dataset():
    df = generate_demo_dataset(
        DemoSpec(
            rows=1000,
            seed=202,
        )
    )

    filtered = apply_filters(
        df,
        modalities=[],
    )

    assert filtered.empty


def test_date_filter_is_inclusive_by_calendar_day():
    df = generate_demo_dataset(
        DemoSpec(
            rows=5000,
            seed=203,
        )
    )

    filtered = apply_filters(
        df,
        start_date="2025-03-01",
        end_date="2025-03-31",
    )

    assert not filtered.empty
    assert filtered["exam_datetime"].min() >= pd.Timestamp("2025-03-01")
    assert filtered["exam_datetime"].max() < pd.Timestamp("2025-04-01")


def test_operational_subset_removes_invalid_acquisitions():
    df = generate_demo_dataset(
        DemoSpec(
            rows=5000,
            seed=204,
        )
    )

    invalid_before = (df["acquisition_end"] < df["acquisition_start"]).sum()

    operational = operational_subset(df)

    invalid_after = (operational["acquisition_end"] < operational["acquisition_start"]).sum()

    assert invalid_before > 0
    assert invalid_after == 0
    assert len(operational) < len(df)


def test_sorted_options_ignores_missing_values():
    df = generate_demo_dataset(
        DemoSpec(
            rows=5000,
            seed=205,
        )
    )

    rooms = sorted_options(df, "room")

    assert rooms
    assert all(isinstance(room, str) for room in rooms)
