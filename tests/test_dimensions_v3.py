import pandas as pd

from rispacs_demo.dimensions_v3 import (
    procedure_display_categories,
    resolve_room_selection,
    room_groups_by_modality,
)


def test_room_groups_use_observed_relationships():
    df = pd.DataFrame(
        {
            "modality": [
                "CT",
                "CT",
                "MR",
                "MR",
                None,
            ],
            "room": [
                "CT_02",
                "CT_01",
                "MR_01",
                None,
                "IGNORED",
            ],
        }
    )

    groups = room_groups_by_modality(df)

    assert groups == {
        "CT": (
            "CT_01",
            "CT_02",
        ),
        "MR": ("MR_01",),
    }


def test_selected_room_group_overrides_individual_rooms():
    groups = {
        "CT": (
            "CT_01",
            "CT_02",
        ),
        "MR": ("MR_01",),
    }

    resolved = resolve_room_selection(
        room_groups=groups,
        selected_groups=[
            "CT",
        ],
        selected_rooms=[
            "MR_01",
        ],
    )

    assert resolved == (
        "CT_01",
        "CT_02",
    )


def test_multiple_room_groups_are_combined():
    groups = {
        "CT": (
            "CT_01",
            "CT_02",
        ),
        "MR": (
            "MR_01",
            "MR_02",
        ),
    }

    resolved = resolve_room_selection(
        room_groups=groups,
        selected_groups=[
            "CT",
            "MR",
        ],
        selected_rooms=[],
    )

    assert resolved == (
        "CT_01",
        "CT_02",
        "MR_01",
        "MR_02",
    )


def test_individual_rooms_used_when_no_group_selected():
    groups = {
        "CT": (
            "CT_01",
            "CT_02",
        ),
        "MR": ("MR_01",),
    }

    resolved = resolve_room_selection(
        room_groups=groups,
        selected_groups=[],
        selected_rooms=[
            "MR_01",
            "CT_02",
        ],
    )

    assert resolved == (
        "CT_02",
        "MR_01",
    )


def test_cross_sectional_separates_ct_and_mri():
    df = pd.DataFrame(
        {
            "procedure_group": [
                "Cross-sectional",
                "Cross-sectional",
                "Ultrasound",
                "Radiography",
            ],
            "modality": [
                "CT",
                "MR",
                "US",
                "CR",
            ],
        }
    )

    result = list(procedure_display_categories(df))

    assert result == [
        "CT",
        "MR",
        "Ultrasound",
        "Radiography",
    ]


def test_dimensions_handle_empty_dataframe():
    empty = pd.DataFrame()

    assert room_groups_by_modality(empty) == {}

    assert procedure_display_categories(empty).empty


def test_cross_sectional_underscore_variant():
    df = pd.DataFrame(
        {
            "procedure_group": [
                "CROSS_SECTIONAL",
                "CROSS_SECTIONAL",
            ],
            "modality": [
                "CT",
                "MR",
            ],
        }
    )

    result = list(procedure_display_categories(df))

    assert result == [
        "CT",
        "MR",
    ]
