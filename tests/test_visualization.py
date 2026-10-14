import plotly.graph_objects as go

from rispacs_demo.analytics import reporting_alerts
from rispacs_demo.synthetic import (
    DemoSpec,
    generate_demo_dataset,
)
from rispacs_demo.visualization import (
    animated_backlog_evolution,
    animated_cumulative_volume,
    animated_workflow_chart,
    pending_age_p90_chart,
    reporting_tat_by_modality_chart,
    technical_workflow_latency_chart,
    workflow_stage_summary,
)


def test_animated_cumulative_volume_has_frames():
    df = generate_demo_dataset(
        DemoSpec(
            rows=5000,
            seed=101,
        )
    )

    fig = animated_cumulative_volume(df)

    assert isinstance(fig, go.Figure)
    assert len(fig.frames) > 0


def test_animated_backlog_evolution_has_frames():
    df = generate_demo_dataset(
        DemoSpec(
            rows=5000,
            seed=102,
        )
    )

    snapshot_at = df["pacs_available_at"].max()

    fig = animated_backlog_evolution(
        df,
        warning_hours=24,
        critical_hours=48,
        snapshot_at=snapshot_at,
    )

    assert isinstance(fig, go.Figure)
    assert len(fig.frames) > 0


def test_pending_age_chart_is_plotly_figure():
    df = generate_demo_dataset(
        DemoSpec(
            rows=5000,
            seed=103,
        )
    )

    alerts = reporting_alerts(
        df,
        warning_hours=24,
        critical_hours=48,
    )

    fig = pending_age_p90_chart(
        alerts,
        warning_hours=24,
        critical_hours=48,
    )

    assert isinstance(fig, go.Figure)


def test_workflow_summary_has_non_negative_metrics():
    df = generate_demo_dataset(
        DemoSpec(
            rows=5000,
            seed=104,
        )
    )

    summary = workflow_stage_summary(df)

    assert not summary.empty
    assert (summary["p50_minutes"] >= 0).all()
    assert (summary["p90_minutes"] >= 0).all()
    assert (summary["p90_minutes"] >= summary["p50_minutes"]).all()


def test_animated_workflow_has_frames():
    df = generate_demo_dataset(
        DemoSpec(
            rows=5000,
            seed=105,
        )
    )

    fig = animated_workflow_chart(df)

    assert isinstance(fig, go.Figure)
    assert len(fig.frames) > 0


def test_animated_workflow_reveals_every_stage():
    df = generate_demo_dataset(
        DemoSpec(
            rows=5000,
            seed=106,
        )
    )

    summary = workflow_stage_summary(df)
    fig = animated_workflow_chart(df)

    assert len(fig.frames) == len(summary)

    assert list(fig.layout.xaxis.ticktext) == summary["stage"].tolist()

    final_frame = fig.frames[-1]

    assert len(final_frame.data[1].x) == len(summary)

    assert list(final_frame.data[1].x) == list(range(len(summary)))


def test_technical_workflow_latency_is_plotly_figure():
    df = generate_demo_dataset(
        DemoSpec(
            rows=5000,
            seed=107,
        )
    )

    fig = technical_workflow_latency_chart(df)

    assert isinstance(fig, go.Figure)
    assert len(fig.data) > 0


def test_reporting_tat_by_modality_is_plotly_figure():
    df = generate_demo_dataset(
        DemoSpec(
            rows=5000,
            seed=108,
        )
    )

    fig = reporting_tat_by_modality_chart(df)

    assert isinstance(fig, go.Figure)
    assert len(fig.data) > 0
