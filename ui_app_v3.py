from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from rispacs_demo.contracts import load_contract, validate_contract
from rispacs_demo.dimensions_v3 import (
    resolve_room_selection,
    room_groups_by_modality,
)
from rispacs_demo.quality_safety_v3 import (
    build_quality_profile,
    build_safety_segments,
    quality_findings_chart,
    quality_issue_row_count,
    safety_completion_chart,
    safety_summary,
)
from rispacs_demo.reporting_sla import apply_reporting_sla
from rispacs_demo.ui_helpers import operational_subset
from rispacs_demo.ui_sections import (
    build_executive_cards,
    build_historical_reporting_cards,
    build_reporting_cards,
    reporting_reconciliation,
)
from rispacs_demo.ui_state import (
    DashboardFilters,
    apply_dashboard_filters,
    default_dashboard_filters,
)
from rispacs_demo.ui_theme import dashboard_css
from rispacs_demo.visualization import (
    monthly_volume_trend,
    patient_class_chart,
    reporting_tat_by_modality_chart,
)
from rispacs_demo.visualization_v3 import (
    modality_mix_chart,
    monthly_total_volume_chart,
    procedure_group_rank_chart,
    room_workload_rank_chart,
    workflow_reporting_dumbbell_chart,
    workflow_technical_dumbbell_chart,
)
from rispacs_demo.web_viz_v3 import (
    executive_volume_animation_html,
    reporting_backlog_animation_html,
)

APP_DIR = Path(__file__).resolve().parent

DATA_PATH = APP_DIR / "data" / "demo_radiology.parquet"

CONTRACT_PATH = APP_DIR / "config" / "data_contract.yml"


st.set_page_config(
    page_title="HIS/RIS/PACS Analytics DEMO",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_data
def load_demo_data() -> pd.DataFrame:
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Demo dataset not found: {DATA_PATH}")

    return pd.read_parquet(DATA_PATH)


def render_metric_cards(
    cards,
) -> None:
    columns = st.columns(len(cards))

    for column, card in zip(
        columns,
        cards,
        strict=True,
    ):
        with column:
            st.metric(
                label=card.label,
                value=card.value,
                help=card.help_text,
            )


CHART_CONFIG = {
    "displayModeBar": False,
    "responsive": True,
}


DARK_TRACE_COLORS = {
    "CT": "#74A7D8",
    "MR": "#6FD2B0",
    "US": "#C7A76A",
    "CR": "#A88FD8",
    "DX": "#8FA2B4",
}

PATIENT_CLASS_COLORS = {
    "OUTPATIENT": "#74A7D8",
    "INPATIENT": "#6FD2B0",
    "EMERGENCY": "#FF6B6B",
}

FALLBACK_TRACE_COLORS = [
    "#74A7D8",
    "#6FD2B0",
    "#C7A76A",
    "#A88FD8",
    "#8FA2B4",
]


def _harmonize_trace_colors(
    figure,
):
    for index, trace in enumerate(figure.data):
        fallback = FALLBACK_TRACE_COLORS[index % len(FALLBACK_TRACE_COLORS)]

        name = str(
            getattr(
                trace,
                "name",
                "",
            )
            or ""
        ).upper()

        color = DARK_TRACE_COLORS.get(
            name,
            fallback,
        )

        trace_type = getattr(
            trace,
            "type",
            "",
        )

        if trace_type in {
            "scatter",
            "scattergl",
        }:
            if (
                getattr(
                    trace,
                    "line",
                    None,
                )
                is not None
            ):
                trace.line.color = color

            if (
                getattr(
                    trace,
                    "marker",
                    None,
                )
                is not None
            ):
                trace.marker.color = color

        elif trace_type == "bar":
            x_values = getattr(
                trace,
                "x",
                None,
            )

            labels = (
                [str(value).upper() for value in list(x_values)] if x_values is not None else []
            )

            if labels and all(label in PATIENT_CLASS_COLORS for label in labels):
                trace.marker.color = [PATIENT_CLASS_COLORS[label] for label in labels]

            elif labels and all(label in DARK_TRACE_COLORS for label in labels):
                trace.marker.color = [DARK_TRACE_COLORS[label] for label in labels]

            else:
                trace.marker.color = color

    return figure


def _compact_figure(
    figure,
    height: int = 300,
):
    figure = _harmonize_trace_colors(figure)

    figure.update_layout(
        height=height,
        margin={
            "l": 18,
            "r": 18,
            "t": 48,
            "b": 30,
        },
        paper_bgcolor="#151D26",
        plot_bgcolor="#151D26",
        font={
            "family": ("Inter, Segoe UI, Arial, sans-serif"),
            "color": "#F3F6F8",
            "size": 11,
        },
        title_font={
            "color": "#F3F6F8",
            "size": 14,
        },
        legend={
            "font": {
                "color": "#A7B3BE",
            },
            "bgcolor": ("rgba(0,0,0,0)"),
            "borderwidth": 0,
        },
        hoverlabel={
            "bgcolor": "#1B2530",
            "bordercolor": "#2B3743",
            "font": {
                "color": "#F3F6F8",
            },
        },
        colorway=(FALLBACK_TRACE_COLORS),
    )

    figure.update_xaxes(
        showgrid=False,
        linecolor="#2B3743",
        tickfont={
            "color": "#A7B3BE",
        },
        title_font={
            "color": "#A7B3BE",
        },
        zeroline=False,
    )

    figure.update_yaxes(
        gridcolor="#26323D",
        linecolor="#2B3743",
        zeroline=False,
        tickfont={
            "color": "#A7B3BE",
        },
        title_font={
            "color": "#A7B3BE",
        },
    )

    return figure


FILTER_START_DATE_KEY = "filter_start_date_v3"
FILTER_END_DATE_KEY = "filter_end_date_v3"
FILTER_MODALITY_KEY = "filter_modality_v3"
FILTER_PATIENT_CLASS_KEY = "filter_patient_class_v3"
FILTER_ROOM_GROUP_KEY = "filter_room_group_v3"
FILTER_ROOM_KEY = "filter_room_v3"
FILTER_TARGET_KEY = "filter_target_v3"
FILTER_WARNING_KEY = "filter_warning_v3"
FILTER_CRITICAL_KEY = "filter_critical_v3"


def _set_filter_widget_state(
    filters: DashboardFilters,
) -> None:
    st.session_state[FILTER_START_DATE_KEY] = filters.start_date

    st.session_state[FILTER_END_DATE_KEY] = filters.end_date

    st.session_state[FILTER_MODALITY_KEY] = list(filters.modalities)

    st.session_state[FILTER_PATIENT_CLASS_KEY] = list(filters.patient_classes)

    st.session_state[FILTER_ROOM_GROUP_KEY] = []

    st.session_state[FILTER_ROOM_KEY] = list(filters.rooms)

    st.session_state[FILTER_TARGET_KEY] = float(filters.target_hours)

    st.session_state[FILTER_WARNING_KEY] = float(filters.warning_window_hours)

    st.session_state[FILTER_CRITICAL_KEY] = float(filters.critical_window_hours)


def _ensure_filter_widget_state(
    filters: DashboardFilters,
) -> None:
    defaults = {
        FILTER_START_DATE_KEY: (filters.start_date),
        FILTER_END_DATE_KEY: (filters.end_date),
        FILTER_MODALITY_KEY: list(filters.modalities),
        FILTER_PATIENT_CLASS_KEY: list(filters.patient_classes),
        FILTER_ROOM_GROUP_KEY: [],
        FILTER_ROOM_KEY: list(filters.rooms),
        FILTER_TARGET_KEY: float(filters.target_hours),
        FILTER_WARNING_KEY: float(filters.warning_window_hours),
        FILTER_CRITICAL_KEY: float(filters.critical_window_hours),
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _reset_filter_state(
    defaults: DashboardFilters,
) -> None:
    _set_filter_widget_state(defaults)

    st.session_state["applied_filters_v3"] = defaults


def render_sidebar(
    df: pd.DataFrame,
    applied: DashboardFilters,
) -> DashboardFilters:
    all_options = default_dashboard_filters(df)

    room_groups = room_groups_by_modality(df)

    _ensure_filter_widget_state(applied)

    with st.sidebar:
        st.subheader("Filters")

        st.caption("Changes take effect after APLICAR FILTROS or RESTABLECER.")

        with st.form("dashboard_filters"):
            st.markdown("**Period**")

            start_date = st.date_input(
                "From",
                min_value=all_options.start_date,
                max_value=all_options.end_date,
                key=FILTER_START_DATE_KEY,
            )

            end_date = st.date_input(
                "To",
                min_value=all_options.start_date,
                max_value=all_options.end_date,
                key=FILTER_END_DATE_KEY,
            )

            modalities = st.multiselect(
                "Modality",
                options=list(all_options.modalities),
                key=FILTER_MODALITY_KEY,
            )

            patient_classes = st.multiselect(
                "Patient class",
                options=list(all_options.patient_classes),
                key=FILTER_PATIENT_CLASS_KEY,
            )

            room_group_modalities = st.multiselect(
                "Room modality groups",
                options=list(room_groups),
                key=FILTER_ROOM_GROUP_KEY,
                help=(
                    "Quick selection of all observed rooms "
                    "belonging to one or more modalities. "
                    "When one or more groups are selected, "
                    "they take precedence over the individual "
                    "Room selection below. The Modality filter "
                    "continues to apply independently."
                ),
            )

            rooms = st.multiselect(
                "Room",
                options=list(all_options.rooms),
                key=FILTER_ROOM_KEY,
                help=("Used when no Room modality group is selected."),
            )

            st.divider()

            st.caption("Synthetic operational reporting target")

            target_hours = st.number_input(
                "Target (hours)",
                min_value=1.0,
                step=1.0,
                key=FILTER_TARGET_KEY,
            )

            warning_window_hours = st.number_input(
                "Warning window (hours)",
                min_value=1.0,
                step=1.0,
                key=FILTER_WARNING_KEY,
            )

            critical_window_hours = st.number_input(
                "Critical window (hours)",
                min_value=1.0,
                step=1.0,
                key=FILTER_CRITICAL_KEY,
            )

            reset_column, apply_column = st.columns(2)

            with reset_column:
                st.form_submit_button(
                    "RESTABLECER",
                    use_container_width=True,
                    type="secondary",
                    on_click=_reset_filter_state,
                    args=(all_options,),
                )

            with apply_column:
                submitted = st.form_submit_button(
                    "APLICAR FILTROS",
                    use_container_width=True,
                    type="primary",
                )

        if not submitted:
            return applied

        resolved_rooms = resolve_room_selection(
            room_groups=room_groups,
            selected_groups=room_group_modalities,
            selected_rooms=rooms,
        )

        candidate = DashboardFilters(
            start_date=start_date,
            end_date=end_date,
            modalities=tuple(modalities),
            patient_classes=tuple(patient_classes),
            rooms=resolved_rooms,
            target_hours=float(target_hours),
            warning_window_hours=float(warning_window_hours),
            critical_window_hours=float(critical_window_hours),
        )

        try:
            candidate.validate()
        except ValueError as exc:
            st.error(str(exc))
            return applied

        return candidate


df = load_demo_data()

defaults = default_dashboard_filters(df)

if "applied_filters_v3" not in st.session_state:
    st.session_state["applied_filters_v3"] = defaults

applied_filters = st.session_state["applied_filters_v3"]

st.markdown(
    dashboard_css(),
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="ris-header">
        <div class="ris-title">
            HIS/RIS/PACS Analytics DEMO
        </div>
        <div class="ris-subtitle">
            Synthetic operational analytics for
            radiology workflow, reporting and data quality.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

tabs = st.tabs(
    [
        "Executive",
        "Operations",
        "Reporting",
        "Workflow",
        "Quality & Safety",
    ]
)

candidate_filters = render_sidebar(
    df,
    applied_filters,
)

if candidate_filters != applied_filters:
    st.session_state["applied_filters_v3"] = candidate_filters

    applied_filters = candidate_filters

filtered = apply_dashboard_filters(
    df,
    applied_filters,
)

snapshot_at = pd.Timestamp(df["pacs_available_at"].max())

sla_config = applied_filters.sla_config()

sla_df = apply_reporting_sla(
    filtered,
    config=sla_config,
    snapshot_at=snapshot_at,
)

context_key = applied_filters.signature()

with st.sidebar:
    st.divider()

    st.caption("Applied analytical context")

    modality_context = ", ".join(applied_filters.modalities) or "None"

    patient_context = ", ".join(applied_filters.patient_classes) or "None"

    st.markdown(
        f"**{len(filtered):,} studies**  \n"
        f"{applied_filters.start_date.isoformat()} "
        f"to {applied_filters.end_date.isoformat()}  \n"
        f"Modalities: {modality_context}  \n"
        f"Patient classes: {patient_context}  \n"
        f"Rooms: {len(applied_filters.rooms)} selected"
    )

    st.caption(f"Context ID: {context_key[:8]}...")

    st.caption(
        "Reporting thresholds are synthetic operational parameters and are not legal GES deadlines."
    )


with tabs[0]:
    st.markdown(
        '<div class="ris-analytic-heading">EXECUTIVE OVERVIEW</div>',
        unsafe_allow_html=True,
    )

    st.caption("How is the service performing under the applied analytical context?")

    executive_cards = build_executive_cards(
        filtered,
        sla_df,
    )

    render_metric_cards(executive_cards)

    st.markdown(
        '<hr class="ris-rule">',
        unsafe_allow_html=True,
    )

    executive_left, executive_right = st.columns(
        [1.35, 1.0],
        gap="large",
    )

    with executive_left:
        with st.container(border=True):
            components.html(
                executive_volume_animation_html(
                    filtered,
                    context_key=context_key,
                ),
                height=315,
                scrolling=False,
            )

    with executive_right:
        patient_figure = patient_class_chart(filtered)

        st.plotly_chart(
            _compact_figure(
                patient_figure,
                height=315,
            ),
            use_container_width=True,
            config=CHART_CONFIG,
        )

    monthly_figure = monthly_volume_trend(filtered)

    st.plotly_chart(
        _compact_figure(
            monthly_figure,
            height=290,
        ),
        use_container_width=True,
        config=CHART_CONFIG,
    )


with tabs[1]:
    st.markdown(
        '<div class="ris-analytic-heading">OPERATIONS</div>',
        unsafe_allow_html=True,
    )

    st.caption("Where is workload concentrated across rooms, modalities and procedure groups?")

    operations_left, operations_right = st.columns(
        [1.25, 0.75],
        gap="large",
    )

    with operations_left:
        room_figure = room_workload_rank_chart(
            filtered,
            top_n=6,
        )

        st.plotly_chart(
            room_figure,
            use_container_width=True,
            config=CHART_CONFIG,
        )

    with operations_right:
        mix_figure = modality_mix_chart(filtered)

        st.plotly_chart(
            mix_figure,
            use_container_width=True,
            config=CHART_CONFIG,
        )

    operations_bottom_left, operations_bottom_right = st.columns(
        [1.25, 0.75],
        gap="large",
    )

    with operations_bottom_left:
        monthly_total = monthly_total_volume_chart(filtered)

        st.plotly_chart(
            monthly_total,
            use_container_width=True,
            config=CHART_CONFIG,
        )

    with operations_bottom_right:
        procedure_figure = procedure_group_rank_chart(
            filtered,
            top_n=6,
        )

        st.plotly_chart(
            procedure_figure,
            use_container_width=True,
            config=CHART_CONFIG,
        )

    st.caption(
        "Workload represents observed study volume. "
        "It does not imply equipment utilization or "
        "capacity because denominator availability "
        "is not present in the demo dataset."
    )


with tabs[2]:
    st.markdown(
        '<div class="ris-analytic-heading">REPORTING CONTROL</div>',
        unsafe_allow_html=True,
    )

    st.caption(
        "Which pending reports require attention relative to the configured operational target?"
    )

    reporting_cards = build_reporting_cards(sla_df)

    render_metric_cards(reporting_cards)

    st.markdown(
        '<hr class="ris-rule">',
        unsafe_allow_html=True,
    )

    reporting_left, reporting_right = st.columns(
        [1.30, 1.0],
        gap="large",
    )

    with reporting_left:
        with st.container(border=True):
            components.html(
                reporting_backlog_animation_html(
                    sla_df,
                    config=sla_config,
                    context_key=context_key,
                ),
                height=315,
                scrolling=False,
            )

    with reporting_right:
        tat_figure = reporting_tat_by_modality_chart(filtered)

        st.plotly_chart(
            _compact_figure(
                tat_figure,
                height=315,
            ),
            use_container_width=True,
            config=CHART_CONFIG,
        )

    st.markdown(
        '<div class="ris-analytic-heading">HISTORICAL TARGET PERFORMANCE</div>',
        unsafe_allow_html=True,
    )

    st.caption("Historical performance against the synthetic operational reporting target.")

    historical_cards = build_historical_reporting_cards(sla_df)

    render_metric_cards(historical_cards)

    reconciliation = reporting_reconciliation(sla_df)

    reconciled = reconciliation["reconciled_total"] == reconciliation["pending_total"]

    if reconciled:
        st.caption(
            "Reporting reconciliation: "
            f"{reconciliation['reconciled_total']:,} / "
            f"{reconciliation['pending_total']:,} "
            "pending studies classified."
        )
    else:
        st.error("Reporting reconciliation requires review.")

    st.caption(
        "GES-tagged is synthetic demo metadata. "
        "The configured reporting target is not "
        "a statutory GES deadline."
    )


with tabs[3]:
    st.markdown(
        '<div class="ris-analytic-heading">WORKFLOW LATENCY</div>',
        unsafe_allow_html=True,
    )

    st.caption("Where is time consumed from the exam timestamp to the signed report?")

    with st.container(border=True):
        process_steps = [
            ("1", "Exam timestamp"),
            ("2", "Acquisition start"),
            ("3", "Acquisition end"),
            ("4", "PACS available"),
            ("5", "Report signed"),
        ]

        process_columns = st.columns(
            len(process_steps),
            gap="small",
        )

        for index, (
            step_number,
            step_label,
        ) in enumerate(process_steps):
            with process_columns[index]:
                st.caption(f"STEP {step_number}")

                st.markdown(f"**{step_label}**")

        technical_phase, reporting_phase = st.columns(
            [3, 1],
            gap="medium",
        )

        with technical_phase:
            st.caption("TECHNICAL PATH | Steps 1 to 4 | minutes")

        with reporting_phase:
            st.caption("REPORTING PATH | Step 4 to 5 | hours")

    workflow_df = operational_subset(filtered)

    workflow_left, workflow_right = st.columns(
        [1.18, 1.0],
        gap="large",
    )

    with workflow_left:
        technical_figure = workflow_technical_dumbbell_chart(workflow_df)

        st.plotly_chart(
            _compact_figure(
                technical_figure,
                height=330,
            ),
            use_container_width=True,
            config=CHART_CONFIG,
        )

    with workflow_right:
        workflow_reporting_figure = workflow_reporting_dumbbell_chart(filtered)

        st.plotly_chart(
            _compact_figure(
                workflow_reporting_figure,
                height=330,
            ),
            use_container_width=True,
            config=CHART_CONFIG,
        )

    st.caption(
        "P50 represents the median and P90 the "
        "upper-tail operational experience. "
        "Technical stages are shown in minutes; "
        "reporting turnaround is shown separately "
        "in hours. Invalid or negative durations "
        "are excluded."
    )


with tabs[4]:
    st.markdown(
        '<div class="ris-analytic-heading">QUALITY & SAFETY</div>',
        unsafe_allow_html=True,
    )

    st.caption("Can the current analytical slice be trusted?")

    contract = load_contract(CONTRACT_PATH)

    contract_result = validate_contract(
        filtered,
        contract,
    )

    quality_profile = build_quality_profile(
        filtered,
        contract,
    )

    affected_rows = quality_issue_row_count(
        filtered,
        contract,
    )

    safety = safety_summary(filtered)

    safety_segments = build_safety_segments(filtered)

    active_findings = int(quality_profile["affected_rows"].gt(0).sum())

    affected_rate = affected_rows / len(filtered) if len(filtered) else 0.0

    if safety["available"] and safety["overall"] is not None:
        safety_value = f"{float(safety['overall']):.1%}"
    else:
        safety_value = "N/A"

    (
        contract_card,
        findings_card,
        affected_card,
        safety_card,
    ) = st.columns(
        4,
        gap="medium",
    )

    with contract_card:
        st.metric(
            "Data contract",
            contract_result["status"],
            help=(
                "Contract v"
                f"{contract.get('version', 'unknown')}. "
                "FAIL indicates missing required columns "
                "or incompatible declared types. "
                "WARN indicates a domain anomaly."
            ),
        )

    with findings_card:
        st.metric(
            "Active DQ findings",
            f"{active_findings:,}",
            help=(
                "Number of public data-quality rules "
                "with at least one affected row "
                "in the current analytical slice."
            ),
        )

    with affected_card:
        st.metric(
            "Rows with DQ issue",
            f"{affected_rows:,}",
            help=(
                f"{affected_rate:.2%} of the current slice. "
                "Each row is counted once even when "
                "multiple findings apply."
            ),
        )

    with safety_card:
        st.metric(
            "Safety checklist",
            safety_value,
            help=(
                "Synthetic checklist-completion indicator. "
                "It is not a clinical safety, legal, "
                "or regulatory compliance measure."
            ),
        )

    contract_version = contract.get(
        "version",
        "unknown",
    )

    st.caption(
        f"Contract v{contract_version} | {len(filtered):,} rows in the current analytical slice."
    )

    domain_violations = contract_result.get(
        "domain_violations",
        [],
    )

    type_violations = contract_result.get(
        "type_violations",
        [],
    )

    missing_columns = contract_result.get(
        "missing_columns",
        [],
    )

    if missing_columns:
        st.error("Contract FAIL - missing required columns: " + ", ".join(missing_columns))

    elif type_violations:
        st.error("Contract FAIL - type violations: " + "; ".join(type_violations))

    elif domain_violations:
        st.caption("Contract WARN - domain anomaly detected: " + "; ".join(domain_violations))

    quality_left, quality_right = st.columns(
        [1.15, 0.85],
        gap="large",
    )

    with quality_left:
        quality_figure = quality_findings_chart(quality_profile)

        st.plotly_chart(
            quality_figure,
            use_container_width=True,
            config={
                "displayModeBar": False,
            },
        )

        quality_table = quality_profile[
            [
                "label",
                "affected_rows",
                "rate",
                "status",
            ]
        ].copy()

        quality_table["rate"] = quality_table["rate"].map(lambda value: f"{value:.2%}")

        quality_table = quality_table.rename(
            columns={
                "label": "Check",
                "affected_rows": ("Affected rows"),
                "rate": "Rate",
                "status": "Status",
            }
        )

        st.dataframe(
            quality_table,
            hide_index=True,
            use_container_width=True,
        )

        st.caption("Rows with multiple findings are counted once in the headline affected-row KPI.")

    with quality_right:
        safety_figure = safety_completion_chart(safety_segments)

        st.plotly_chart(
            safety_figure,
            use_container_width=True,
            config={
                "displayModeBar": False,
            },
        )

        if safety["available"]:
            st.metric(
                "Incomplete checklist rows",
                f"{int(safety['incomplete']):,}",
            )

            st.caption(
                "MR and Non-MR are shown separately "
                "because the synthetic generator "
                "uses different completion probabilities."
            )

    st.info(
        "Safety checklist completion is synthetic operational metadata. "
        "It must not be interpreted as evidence of clinical safety, "
        "legal compliance, accreditation, or regulatory certification."
    )
