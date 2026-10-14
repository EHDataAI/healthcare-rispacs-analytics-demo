import pandas as pd

from rispacs_demo.visualization_v3 import (
    MODALITY_COLORS,
    procedure_group_rank_chart,
)


def test_procedure_category_colors_match_modality_semantics():
    df = pd.DataFrame(
        {
            "procedure_group": [
                "CROSS_SECTIONAL",
                "CROSS_SECTIONAL",
                "Ultrasound",
                "Radiography",
                "UNKNOWN",
            ],
            "modality": [
                "CT",
                "MR",
                "US",
                "DX",
                "UNKNOWN",
            ],
        }
    )

    figure = procedure_group_rank_chart(
        df,
        top_n=7,
    )

    labels = [str(value) for value in figure.data[0].y]

    colors = list(figure.data[0].marker.color)

    observed = dict(
        zip(
            labels,
            colors,
            strict=True,
        )
    )

    assert observed["CT"] == MODALITY_COLORS["CT"]
    assert observed["MR"] == MODALITY_COLORS["MR"]
    assert observed["Ultrasound"] == MODALITY_COLORS["US"]
    assert observed["Radiography"] == MODALITY_COLORS["DX"]
    assert observed["UNKNOWN"] == MODALITY_COLORS["UNKNOWN"]
