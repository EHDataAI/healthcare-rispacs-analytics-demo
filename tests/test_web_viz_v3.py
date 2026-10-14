from rispacs_demo.reporting_sla import (
    ReportingSLAConfig,
    apply_reporting_sla,
)
from rispacs_demo.synthetic import (
    DemoSpec,
    generate_demo_dataset,
)
from rispacs_demo.ui_theme import (
    PALETTE,
    dashboard_css,
)
from rispacs_demo.web_viz_v3 import (
    executive_volume_animation_html,
    reporting_backlog_animation_html,
)

CONFIG = ReportingSLAConfig(
    target_hours=72,
    warning_window_hours=48,
    critical_window_hours=24,
)


def test_theme_contains_core_palette():
    required = {
        "graphite",
        "slate",
        "surface",
        "normal",
        "warning",
        "critical",
        "breached",
    }

    assert required.issubset(PALETTE)

    css = dashboard_css()

    assert ".ris-title" in css
    assert ".ris-kpi" in css


def test_executive_animation_is_autoplay_only():
    df = generate_demo_dataset(
        DemoSpec(
            rows=5000,
            seed=601,
        )
    )

    markup = executive_volume_animation_html(
        df,
        context_key="abc123",
    )

    assert "requestAnimationFrame" in markup
    assert "abc123" in markup
    assert "Repetir" not in markup
    assert "Play" not in markup
    assert "Pause" not in markup


def test_executive_animation_has_no_external_script():
    df = generate_demo_dataset(
        DemoSpec(
            rows=1000,
            seed=602,
        )
    )

    markup = executive_volume_animation_html(
        df,
        context_key="safe-test",
    )

    assert "<script src=" not in markup

    assert "prefers-reduced-motion" in markup


def test_reporting_animation_contains_four_states():
    df = generate_demo_dataset(
        DemoSpec(
            rows=5000,
            seed=603,
        )
    )

    snapshot = df["pacs_available_at"].max()

    sla_df = apply_reporting_sla(
        df,
        config=CONFIG,
        snapshot_at=snapshot,
    )

    markup = reporting_backlog_animation_html(
        sla_df,
        config=CONFIG,
        context_key="reporting123",
    )

    for label in [
        "Normal",
        "Warning",
        "Critical",
        "Breached",
    ]:
        assert label in markup


def test_reporting_animation_uses_countdown_semantics():
    df = generate_demo_dataset(
        DemoSpec(
            rows=3000,
            seed=604,
        )
    )

    snapshot = df["pacs_available_at"].max()

    sla_df = apply_reporting_sla(
        df,
        config=CONFIG,
        snapshot_at=snapshot,
    )

    markup = reporting_backlog_animation_html(
        sla_df,
        config=CONFIG,
        context_key="sla-countdown",
    )

    assert "48 h remaining" in markup
    assert "24" in markup
    assert "Target exceeded" in markup
