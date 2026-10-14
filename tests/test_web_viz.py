
from rispacs_demo.analytics import reporting_alerts
from rispacs_demo.synthetic import (
    DemoSpec,
    generate_demo_dataset,
)
from rispacs_demo.web_viz import (
    executive_volume_animation_html,
    reporting_backlog_animation_html,
)


def test_executive_web_animation_contains_autoplay_svg():
    df = generate_demo_dataset(
        DemoSpec(
            rows=5000,
            seed=301,
        )
    )

    markup = executive_volume_animation_html(df)

    assert "<svg" in markup
    assert "requestAnimationFrame" in markup
    assert "Repetir" in markup
    assert "prefers-reduced-motion" in markup


def test_reporting_web_animation_contains_all_states():
    df = generate_demo_dataset(
        DemoSpec(
            rows=5000,
            seed=302,
        )
    )

    alerts = reporting_alerts(
        df,
        warning_hours=24,
        critical_hours=48,
    )

    markup = reporting_backlog_animation_html(
        alerts,
        warning_hours=24,
        critical_hours=48,
    )

    assert "Normal" in markup
    assert "Warning" in markup
    assert "Critical" in markup
    assert "Repetir" in markup
