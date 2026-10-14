import pandas as pd

from rispacs_demo.synthetic import (
    DemoSpec,
    generate_demo_dataset,
)
from rispacs_demo.visualization_v3 import (
    modality_mix_chart,
    monthly_total_volume_chart,
    procedure_group_rank_chart,
    room_workload_rank_chart,
)


def _demo():
    return generate_demo_dataset(
        DemoSpec(
            rows=5000,
            seed=705,
        )
    )


def test_room_workload_is_horizontal_ranking():
    figure = room_workload_rank_chart(
        _demo(),
        top_n=6,
    )

    assert len(figure.data) == 1
    assert figure.data[0].type == "bar"
    assert figure.data[0].orientation == "h"
    assert len(figure.data[0].y) <= 6


def test_modality_mix_is_donut():
    figure = modality_mix_chart(_demo())

    assert len(figure.data) == 1
    assert figure.data[0].type == "pie"
    assert figure.data[0].hole > 0.5


def test_monthly_total_has_volume_and_mean():
    figure = monthly_total_volume_chart(_demo())

    trace_types = [trace.type for trace in figure.data]

    assert trace_types == [
        "bar",
        "scatter",
    ]


def test_procedure_group_is_horizontal_ranking():
    figure = procedure_group_rank_chart(
        _demo(),
        top_n=6,
    )

    assert len(figure.data) == 1
    assert figure.data[0].type == "bar"
    assert figure.data[0].orientation == "h"
    assert len(figure.data[0].y) <= 6


def test_operations_charts_handle_empty_data():
    empty = pd.DataFrame()

    figures = [
        room_workload_rank_chart(empty),
        modality_mix_chart(empty),
        monthly_total_volume_chart(empty),
        procedure_group_rank_chart(empty),
    ]

    for figure in figures:
        assert len(figure.layout.annotations) >= 1


def test_procedure_group_separates_ct_and_mri():
    df = pd.DataFrame(
        {
            "procedure_group": [
                "Cross-sectional",
                "Cross-sectional",
                "Cross-sectional",
                "Ultrasound",
            ],
            "modality": [
                "CT",
                "CT",
                "MR",
                "US",
            ],
        }
    )

    figure = procedure_group_rank_chart(
        df,
        top_n=6,
    )

    labels = {str(value) for value in figure.data[0].y}

    assert "CT" in labels
    assert "MR" in labels
    assert "Cross-sectional" not in labels
