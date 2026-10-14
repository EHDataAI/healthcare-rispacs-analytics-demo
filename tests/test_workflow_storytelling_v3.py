from rispacs_demo.synthetic import (
    DemoSpec,
    generate_demo_dataset,
)
from rispacs_demo.ui_helpers import (
    operational_subset,
)
from rispacs_demo.visualization_v3 import (
    workflow_reporting_dumbbell_chart,
    workflow_technical_dumbbell_chart,
)


def _marker_traces(figure):
    return [trace for trace in figure.data if "markers" in (trace.mode or "")]


def test_workflow_technical_uses_dumbbell_semantics():
    df = generate_demo_dataset(
        DemoSpec(
            rows=5000,
            seed=701,
        )
    )

    operational = operational_subset(df)

    figure = workflow_technical_dumbbell_chart(operational)

    assert figure.layout.title.text == ("Technical path")

    assert figure.layout.xaxis.title.text == "Minutes"

    assert all(trace.type == "scatter" for trace in figure.data)

    markers = _marker_traces(figure)

    assert len(markers) == 2

    assert markers[0].marker.symbol == "circle"

    assert markers[1].marker.symbol == "diamond"

    assert len(markers[0].y) == 3
    assert len(markers[1].y) == 3


def test_workflow_reporting_uses_hours_and_dumbbells():
    df = generate_demo_dataset(
        DemoSpec(
            rows=5000,
            seed=702,
        )
    )

    figure = workflow_reporting_dumbbell_chart(df)

    assert figure.layout.title.text == ("Downstream reporting")

    assert figure.layout.xaxis.title.text == "Hours"

    assert all(trace.type == "scatter" for trace in figure.data)

    markers = _marker_traces(figure)

    assert len(markers) == 2

    assert markers[0].marker.symbol == "circle"

    assert markers[1].marker.symbol == "diamond"

    assert len(markers[0].y) > 0
    assert len(markers[1].y) > 0
