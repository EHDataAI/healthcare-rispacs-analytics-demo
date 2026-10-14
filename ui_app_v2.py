from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st
import yaml

from rispacs_demo.analytics import executive_kpis, reporting_alerts
from rispacs_demo.quality import quality_summary
from rispacs_demo.ui_helpers import (
    apply_filters,
    operational_subset,
    sorted_options,
)
from rispacs_demo.visualization import (
    MODALITY_ORDER,
    current_backlog_chart,
    modality_volume_chart,
    monthly_volume_trend,
    patient_class_chart,
    pending_age_p90_chart,
    reporting_tat_by_modality_chart,
    room_workload_chart,
    technical_workflow_latency_chart,
    workflow_stage_summary,
)
from rispacs_demo.web_viz import (
    executive_volume_animation_html,
    reporting_backlog_animation_html,
)

ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data" / "demo_radiology.parquet"
DEMO_CONFIG_PATH = ROOT / "config" / "demo.yml"
CONTRACT_PATH = ROOT / "config" / "data_contract.yml"

PLOTLY_CONFIG = {
    "displaylogo": False,
    "responsive": True,
}

st.set_page_config(
    page_title="RIS/PACS Analytics Demo",
    layout="wide",
)


@st.cache_data(show_spinner=False)
def load_dataset(path: str) -> pd.DataFrame:
    df = pd.read_parquet(path)

    datetime_columns = [
        "exam_datetime",
        "acquisition_start",
        "acquisition_end",
        "pacs_available_at",
        "report_signed_at",
    ]

    for column in datetime_columns:
        if column in df.columns:
            df[column] = pd.to_datetime(
                df[column],
                errors="coerce",
            )

    return df


@st.cache_data(show_spinner=False)
def load_yaml(path: str) -> dict:
    with Path(path).open(
        "r",
        encoding="utf-8",
    ) as file:
        content = yaml.safe_load(file)

    return content or {}


def normalize_date_range(
    value: object,
    fallback_start: object,
    fallback_end: object,
) -> tuple[object, object]:
    if isinstance(value, (tuple, list)):
        if len(value) == 2:
            return value[0], value[1]

        if len(value) == 1:
            return value[0], value[0]

    if value is not None:
        return value, value

    return fallback_start, fallback_end


def selected_or_none(
    selected: list[str],
    all_options: list[str],
) -> list[str] | None:
    if set(selected) == set(all_options):
        return None

    return selected


def format_hours(value: float | int | None) -> str:
    if value is None or pd.isna(value):
        return "N/A"

    return f"{float(value):.1f} h"


def format_minutes(value: float | int | None) -> str:
    if value is None or pd.isna(value):
        return "N/A"

    value = float(value)

    if value >= 60:
        return f"{value / 60:.1f} h"

    return f"{value:.1f} min"


def evaluate_demo_contract(
    df: pd.DataFrame,
    contract: dict,
) -> dict[str, object]:
    missing_columns: list[str] = []
    violations: list[str] = []

    required = contract.get(
        "required_columns",
        [],
    )

    for column in required:
        if column not in df.columns:
            missing_columns.append(column)

    rules = contract.get(
        "rules",
        {},
    )

    for column, rule in rules.items():
        if column not in df.columns:
            continue

        allowed = rule.get("allowed")

        if allowed is None:
            continue

        invalid = int((df[column].notna() & ~df[column].isin(allowed)).sum())

        if invalid:
            violations.append(f"{column}: {invalid} values outside allowed set")

    if missing_columns:
        status = "FAIL"
    elif violations:
        status = "WARN"
    else:
        status = "PASS"

    return {
        "status": status,
        "missing_columns": missing_columns,
        "violations": violations,
    }


def render_metric_card(
    label: str,
    value: str,
    help_text: str | None = None,
) -> None:
    with st.container(border=True):
        st.metric(
            label=label,
            value=value,
            help=help_text,
        )


if not DATA_PATH.exists():
    st.error("Synthetic demo dataset was not found. Run scripts/generate_demo_data.py first.")
    st.stop()

df = load_dataset(str(DATA_PATH))
cfg = load_yaml(str(DEMO_CONFIG_PATH))
contract = load_yaml(str(CONTRACT_PATH))

snapshot_at = pd.Timestamp(df["pacs_available_at"].max())

default_warning = int(
    cfg.get(
        "reporting_sla",
        {},
    ).get(
        "warning_hours",
        24,
    )
)

default_critical = int(
    cfg.get(
        "reporting_sla",
        {},
    ).get(
        "critical_hours",
        48,
    )
)

default_warning = max(
    1,
    min(167, default_warning),
)

default_critical = max(
    default_warning + 1,
    min(336, default_critical),
)

st.title("RIS/PACS Analytics")

st.caption(
    "Synthetic operational analytics demo. "
    f"Point-in-time snapshot: {snapshot_at:%Y-%m-%d %H:%M}. "
    "No real patient or institutional data are included."
)

with st.expander(
    "Global filters and operational controls",
    expanded=True,
):
    min_date = pd.Timestamp(df["exam_datetime"].min()).date()

    max_date = pd.Timestamp(df["exam_datetime"].max()).date()

    raw_modalities = sorted_options(
        df,
        "modality",
    )

    modality_options = [modality for modality in MODALITY_ORDER if modality in raw_modalities]

    modality_options.extend(
        modality for modality in raw_modalities if modality not in MODALITY_ORDER
    )

    patient_order = [
        "OUTPATIENT",
        "INPATIENT",
        "EMERGENCY",
    ]

    raw_patient_classes = sorted_options(
        df,
        "patient_class",
    )

    patient_options = [
        patient_class for patient_class in patient_order if patient_class in raw_patient_classes
    ]

    patient_options.extend(
        patient_class for patient_class in raw_patient_classes if patient_class not in patient_order
    )

    room_options = sorted_options(
        df,
        "room",
    )

    filter_col_1, filter_col_2, filter_col_3, filter_col_4 = st.columns(4)

    with filter_col_1:
        date_range = st.date_input(
            "Date range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
            key="_v2_date_range",
        )

    with filter_col_2:
        selected_modalities = st.multiselect(
            "Modality",
            options=modality_options,
            default=modality_options,
            key="v2mod",
        )

    with filter_col_3:
        selected_patient_classes = st.multiselect(
            "Patient class",
            options=patient_options,
            default=patient_options,
            key="_v2_patient_classes",
        )

    with filter_col_4:
        selected_rooms = st.multiselect(
            "Room",
            options=room_options,
            default=room_options,
            key="_v2_rooms",
        )

    control_col_1, control_col_2, control_col_3 = st.columns([1, 1, 1])

    if "_v2_warning_hours" not in st.session_state:
        st.session_state["_v2_warning_hours"] = default_warning

    if "_v2_critical_hours" not in st.session_state:
        st.session_state["_v2_critical_hours"] = default_critical

    with control_col_1:
        warning_hours = int(
            st.number_input(
                "Warning threshold (hours)",
                min_value=1,
                max_value=167,
                step=1,
                key="_v2_warning_hours",
                help=(
                    "Early operational reporting warning threshold. The demo default is 24 hours."
                ),
            )
        )

    if st.session_state["_v2_critical_hours"] <= warning_hours:
        st.session_state["_v2_critical_hours"] = min(
            336,
            warning_hours + 1,
        )

    with control_col_2:
        critical_hours = int(
            st.number_input(
                "Critical threshold (hours)",
                min_value=warning_hours + 1,
                max_value=336,
                step=1,
                key="v2crit",
                help=(
                    "Operational escalation threshold. "
                    "It must remain greater than the warning threshold."
                ),
            )
        )

    with control_col_3:
        motion_enabled = st.toggle(
            "Motion",
            value=True,
            key="_v2_motion",
            help=(
                "Enable selected analytical animations. "
                "Disable for a fully static dashboard experience."
            ),
        )

    st.caption(
        "The 24 h / 48 h defaults are configurable operational demo "
        "thresholds. They are not universal legal GES deadlines."
    )

start_date, end_date = normalize_date_range(
    date_range,
    min_date,
    max_date,
)

filtered = apply_filters(
    df,
    start_date=start_date,
    end_date=end_date,
    modalities=selected_or_none(
        selected_modalities,
        modality_options,
    ),
    patient_classes=selected_or_none(
        selected_patient_classes,
        patient_options,
    ),
    rooms=selected_or_none(
        selected_rooms,
        room_options,
    ),
)

operational = operational_subset(filtered)

kpis = executive_kpis(filtered)

alerts = reporting_alerts(
    filtered,
    warning_hours=warning_hours,
    critical_hours=critical_hours,
    now=snapshot_at,
)

pending_mask = alerts["report_status"].eq("PENDING")

normal_count = int((pending_mask & alerts["operational_state"].eq("NORMAL")).sum())

warning_count = int((pending_mask & alerts["operational_state"].eq("WARNING")).sum())

critical_count = int((pending_mask & alerts["operational_state"].eq("CRITICAL")).sum())

ges_pending = int((pending_mask & alerts["ges_flag"].astype(bool)).sum())

st.caption(f"Filtered slice: {len(filtered):,} of {len(df):,} synthetic studies.")

metric_columns = st.columns(5)

with metric_columns[0]:
    render_metric_card(
        "Studies",
        f"{int(kpis['studies']):,}",
        "Studies in the currently filtered analytical slice.",
    )

with metric_columns[1]:
    render_metric_card(
        "Pending reports",
        f"{int(kpis['pending_reports']):,}",
        "Reports still pending at the operational snapshot.",
    )

with metric_columns[2]:
    render_metric_card(
        "Reporting TAT P50",
        format_hours(kpis["median_report_tat_h"]),
        "Median signed-report turnaround time.",
    )

with metric_columns[3]:
    render_metric_card(
        "Reporting TAT P90",
        format_hours(kpis["p90_report_tat_h"]),
        "90th percentile signed-report turnaround time.",
    )

with metric_columns[4]:
    render_metric_card(
        "Critical backlog",
        f"{critical_count:,}",
        (f"Pending reports whose operational age is at or above {critical_hours} hours."),
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

with tabs[0]:
    st.subheader("Executive overview")

    st.write(
        "High-level activity and reporting performance for the currently selected analytical slice."
    )

    if motion_enabled:
        st.iframe(
            executive_volume_animation_html(filtered),
            width="stretch",
            height=520,
        )
    else:
        st.plotly_chart(
            modality_volume_chart(filtered),
            use_container_width=True,
            config=PLOTLY_CONFIG,
            key="executive_primary_static",
        )

    executive_left, executive_right = st.columns(2)

    with executive_left:
        st.plotly_chart(
            monthly_volume_trend(filtered),
            use_container_width=True,
            config=PLOTLY_CONFIG,
            key="executive_monthly_volume",
        )

    with executive_right:
        st.plotly_chart(
            patient_class_chart(filtered),
            use_container_width=True,
            config=PLOTLY_CONFIG,
            key="executive_patient_class",
        )

    with st.expander(
        "Export filtered synthetic data",
        expanded=False,
    ):
        csv_data = filtered.to_csv(index=False).encode("utf-8")

        st.download_button(
            label="Download filtered CSV",
            data=csv_data,
            file_name="rispacs_demo_filtered.csv",
            mime="text/csv",
        )

with tabs[1]:
    st.subheader("Operations")

    st.write(
        "Operational workload and time distributions. "
        "Records with invalid temporal sequences are excluded "
        "from time-based operational indicators but remain "
        "available in Data Quality."
    )

    operations_left, operations_right = st.columns(2)

    with operations_left:
        st.plotly_chart(
            monthly_volume_trend(filtered),
            use_container_width=True,
            config=PLOTLY_CONFIG,
            key="operations_monthly_volume",
        )

    with operations_right:
        st.plotly_chart(
            room_workload_chart(filtered),
            use_container_width=True,
            config=PLOTLY_CONFIG,
            key="operations_room_workload",
        )

    operations_second_left, operations_second_right = st.columns(2)

    with operations_second_left:
        st.plotly_chart(
            modality_volume_chart(filtered),
            use_container_width=True,
            config=PLOTLY_CONFIG,
            key="operations_modality_volume",
        )

    with operations_second_right:
        st.plotly_chart(
            patient_class_chart(filtered),
            use_container_width=True,
            config=PLOTLY_CONFIG,
            key="operations_patient_class",
        )

    stage_summary = workflow_stage_summary(operational)

    pre_acquisition = stage_summary[stage_summary["stage"].eq("Pre-acquisition wait")]

    acquisition = stage_summary[stage_summary["stage"].eq("Acquisition")]

    pre_p50 = float(pre_acquisition.iloc[0]["p50_minutes"]) if not pre_acquisition.empty else None

    pre_p90 = float(pre_acquisition.iloc[0]["p90_minutes"]) if not pre_acquisition.empty else None

    acq_p50 = float(acquisition.iloc[0]["p50_minutes"]) if not acquisition.empty else None

    acq_p90 = float(acquisition.iloc[0]["p90_minutes"]) if not acquisition.empty else None

    timing_columns = st.columns(4)

    with timing_columns[0]:
        render_metric_card(
            "Pre-acquisition P50",
            format_minutes(pre_p50),
        )

    with timing_columns[1]:
        render_metric_card(
            "Pre-acquisition P90",
            format_minutes(pre_p90),
        )

    with timing_columns[2]:
        render_metric_card(
            "Acquisition P50",
            format_minutes(acq_p50),
        )

    with timing_columns[3]:
        render_metric_card(
            "Acquisition P90",
            format_minutes(acq_p90),
        )

with tabs[2]:
    st.subheader("Reporting SLA / GES-tagged")

    st.write("Active reporting backlog is separated from historical signed-report performance.")

    reporting_metrics = st.columns(4)

    with reporting_metrics[0]:
        render_metric_card(
            "Normal",
            f"{normal_count:,}",
            f"Pending for less than {warning_hours} hours.",
        )

    with reporting_metrics[1]:
        render_metric_card(
            "Warning",
            f"{warning_count:,}",
            (f"Pending from {warning_hours} hours up to less than {critical_hours} hours."),
        )

    with reporting_metrics[2]:
        render_metric_card(
            "Critical",
            f"{critical_count:,}",
            f"Pending for at least {critical_hours} hours.",
        )

    with reporting_metrics[3]:
        render_metric_card(
            "GES-tagged pending",
            f"{ges_pending:,}",
            (
                "Synthetic records associated with a GES-tagged "
                "workflow. This is not a legal GES compliance measure."
            ),
        )

    if motion_enabled:
        st.iframe(
            reporting_backlog_animation_html(
                alerts,
                warning_hours=warning_hours,
                critical_hours=critical_hours,
            ),
            width="stretch",
            height=520,
        )
    else:
        st.plotly_chart(
            current_backlog_chart(alerts),
            use_container_width=True,
            config=PLOTLY_CONFIG,
            key="reporting_current_backlog_static",
        )

    st.plotly_chart(
        pending_age_p90_chart(
            alerts,
            warning_hours=warning_hours,
            critical_hours=critical_hours,
        ),
        use_container_width=True,
        config=PLOTLY_CONFIG,
        key="reporting_pending_age",
    )

    historical_within = int(alerts["historical_sla_state"].eq("CLOSED_WITHIN_SLA").sum())

    historical_breached = int(alerts["historical_sla_state"].eq("CLOSED_BREACHED_SLA").sum())

    historical_columns = st.columns(2)

    with historical_columns[0]:
        render_metric_card(
            "Closed within demo SLA",
            f"{historical_within:,}",
            "Signed reports below the configured critical threshold.",
        )

    with historical_columns[1]:
        render_metric_card(
            "Closed beyond demo SLA",
            f"{historical_breached:,}",
            "Signed reports at or above the configured critical threshold.",
        )

    st.info(
        "GES note: GES Opportunity Guarantee deadlines depend on the "
        "specific health problem and intervention. The synthetic "
        "GES tag in this demo does not determine legal compliance."
    )

with tabs[3]:
    st.subheader("Workflow TAT & bottlenecks")

    st.write("Exam datetime → Acquisition start → Acquisition end → PACS available → Report signed")

    st.caption(
        "Technical workflow latency is shown in minutes, while "
        "reporting turnaround is analysed separately in hours."
    )

    workflow_left, workflow_right = st.columns(2)

    with workflow_left:
        st.plotly_chart(
            technical_workflow_latency_chart(operational),
            use_container_width=True,
            config=PLOTLY_CONFIG,
            key="workflow_technical_latency",
        )

    with workflow_right:
        st.plotly_chart(
            reporting_tat_by_modality_chart(filtered),
            use_container_width=True,
            config=PLOTLY_CONFIG,
            key="workflow_reporting_tat",
        )

    workflow_summary = workflow_stage_summary(operational)

    if workflow_summary.empty:
        st.warning("No valid workflow observations are available for the selected filters.")
    else:
        workflow_display = workflow_summary.copy()

        workflow_display["P50"] = workflow_display["p50_minutes"].map(format_minutes)

        workflow_display["P90"] = workflow_display["p90_minutes"].map(format_minutes)

        workflow_display = workflow_display[
            [
                "stage",
                "P50",
                "P90",
                "observations",
            ]
        ].rename(
            columns={
                "stage": "Workflow stage",
                "observations": "Observations",
            }
        )

        st.dataframe(
            workflow_display,
            hide_index=True,
            use_container_width=True,
        )

    st.caption(
        "Invalid or negative temporal sequences are excluded from "
        "workflow performance calculations and retained for Data Quality."
    )

with tabs[4]:
    st.subheader("Quality & Safety")

    quality_left, safety_right = st.columns([1.15, 0.85])

    with quality_left:
        st.markdown("#### Data Quality")

        contract_result = evaluate_demo_contract(
            df,
            contract,
        )

        contract_columns = st.columns(3)

        with contract_columns[0]:
            render_metric_card(
                "Contract status",
                str(contract_result["status"]),
            )

        with contract_columns[1]:
            render_metric_card(
                "Missing required columns",
                str(len(contract_result["missing_columns"])),
            )

        with contract_columns[2]:
            render_metric_card(
                "Contract violations",
                str(len(contract_result["violations"])),
            )

        if contract_result["violations"]:
            for violation in contract_result["violations"]:
                st.warning(str(violation))

        if contract_result["missing_columns"]:
            st.error("Missing required columns: " + ", ".join(contract_result["missing_columns"]))

        quality = quality_summary(filtered)

        affected_quality = quality[quality["affected_rows"].gt(0)].copy()

        if affected_quality.empty:
            st.success("No Data Quality issues were detected in the filtered slice.")
        else:
            st.dataframe(
                affected_quality,
                hide_index=True,
                use_container_width=True,
            )

        with st.expander(
            "Show all Data Quality checks",
            expanded=False,
        ):
            st.dataframe(
                quality,
                hide_index=True,
                use_container_width=True,
            )

        with st.expander(
            "Show public data contract",
            expanded=False,
        ):
            st.code(
                yaml.safe_dump(
                    contract,
                    sort_keys=False,
                ),
                language="yaml",
            )

        st.caption(
            "The synthetic dataset intentionally contains a small "
            "number of controlled inconsistencies so the public "
            "Data Quality workflow can be demonstrated."
        )

    with safety_right:
        st.markdown("#### Safety overview")

        valid_safety = filtered[filtered["modality"].isin(MODALITY_ORDER)].copy()

        if valid_safety.empty:
            st.warning("No valid modality observations are available for the selected filters.")
        else:
            safety_rate = float(valid_safety["safety_check_complete"].mean() * 100)

            render_metric_card(
                "Checklist completion",
                f"{safety_rate:.1f}%",
                (
                    "Synthetic aggregate checklist completion. "
                    "This is not a clinical eligibility measure."
                ),
            )

            safety_by_modality = (
                valid_safety.groupby(
                    "modality",
                    observed=True,
                )["safety_check_complete"]
                .mean()
                .mul(100)
                .rename("Completion (%)")
                .to_frame()
            )

            st.bar_chart(safety_by_modality)

        st.warning(
            "Synthetic aggregate compliance only. "
            "No MRI eligibility, implant screening or clinical "
            "safety decision logic is included."
        )
