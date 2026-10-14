from pathlib import Path

from streamlit.testing.v1 import AppTest

ROOT_DIR = Path(__file__).resolve().parents[1]

APP_PATH = ROOT_DIR / "ui_app_v3.py"


def _run_app():
    app = AppTest.from_file(APP_PATH)

    app.run(timeout=20)

    return app


def _by_label(
    elements,
    label: str,
):
    matches = [element for element in elements if element.label == label]

    assert len(matches) == 1

    return matches[0]


def test_v3_app_starts_without_exception():
    app = _run_app()

    assert not app.exception


def test_v3_has_expected_navigation():
    app = _run_app()

    labels = [tab.label for tab in app.tabs]

    assert labels == [
        "Executive",
        "Operations",
        "Reporting",
        "Workflow",
        "Quality & Safety",
    ]


def test_v3_has_filter_action_buttons():
    app = _run_app()

    labels = [button.label for button in app.button]

    assert "RESTABLECER" in labels
    assert "APLICAR FILTROS" in labels


def test_v3_default_context_has_executive_metrics():
    app = _run_app()

    metric_labels = [metric.label for metric in app.metric]

    assert "Studies" in metric_labels
    assert "Pending reports" in metric_labels
    assert "Reporting TAT P50" in metric_labels
    assert "Reporting TAT P90" in metric_labels
    assert "Breached" in metric_labels


def test_v3_reset_restores_default_context():
    app = _run_app()

    modality = _by_label(
        app.multiselect,
        "Modality",
    )

    target = _by_label(
        app.number_input,
        "Target (hours)",
    )

    initial_modalities = list(modality.value)

    initial_target = target.value

    assert initial_target == 72.0

    modality.set_value(["CT"])

    target.set_value(96.0)

    _by_label(
        app.button,
        "APLICAR FILTROS",
    ).click()

    app.run(timeout=20)

    assert not app.exception

    filtered_studies = _by_label(
        app.metric,
        "Studies",
    ).value

    assert filtered_studies != "50,000"

    _by_label(
        app.button,
        "RESTABLECER",
    ).click()

    app.run(timeout=20)

    assert not app.exception

    restored_modalities = list(
        _by_label(
            app.multiselect,
            "Modality",
        ).value
    )

    restored_target = _by_label(
        app.number_input,
        "Target (hours)",
    ).value

    restored_studies = _by_label(
        app.metric,
        "Studies",
    ).value

    assert restored_modalities == initial_modalities

    assert restored_target == initial_target

    assert restored_studies == "50,000"
