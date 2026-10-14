from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from rispacs_demo.analytics import enrich_metrics, executive_kpis, reporting_alerts
from rispacs_demo.config import load_yaml
from rispacs_demo.contracts import load_contract, validate_contract
from rispacs_demo.quality import quality_summary
from rispacs_demo.synthetic import DemoSpec, write_demo_dataset

st.set_page_config(page_title="RIS/PACS Analytics Demo", layout="wide")
st.title("RIS/PACS Analytics Demo")
st.caption("Synthetic operational analytics. Demonstration only; not clinical decision support.")

cfg = load_yaml("config/demo.yml")
data_path = Path("data/demo_radiology.parquet")

if not data_path.exists():
    with st.spinner("Generating synthetic demo dataset..."):
        write_demo_dataset(
            data_path,
            DemoSpec(rows=int(cfg.get("rows", 50_000)), seed=int(cfg.get("seed", 20260928))),
        )


@st.cache_data(show_spinner=False)
def load_data(path: str) -> pd.DataFrame:
    return pd.read_parquet(path)


df = load_data(str(data_path))
metrics = enrich_metrics(df)
snapshot_at = pd.Timestamp(metrics["pacs_available_at"].max())

with st.sidebar:
    st.header("Filters")
    modality_values = sorted(metrics["modality"].dropna().unique().tolist())
    selected_modalities = st.multiselect("Modality", modality_values, default=modality_values)
    patient_values = sorted(metrics["patient_class"].dropna().unique().tolist())
    selected_patient = st.multiselect("Patient class", patient_values, default=patient_values)

filtered = metrics[
    metrics["modality"].isin(selected_modalities) & metrics["patient_class"].isin(selected_patient)
].copy()

pages = st.tabs(
    [
        "Executive Pulse",
        "Workflow Bottleneck",
        "Reporting SLA & GES",
        "Data Quality",
        "Safety Overview",
    ]
)

with pages[0]:
    kpi = executive_kpis(filtered)
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Studies", f"{kpi['studies']:,}")
    c2.metric("Pending reports", f"{kpi['pending_reports']:,}")
    c3.metric("GES demo labels", f"{kpi['ges_labeled']:,}")
    c4.metric("Median report TAT", f"{kpi['median_report_tat_h']:.1f} h")
    c5.metric("P90 report TAT", f"{kpi['p90_report_tat_h']:.1f} h")

    monthly = filtered.assign(month=filtered["exam_datetime"].dt.to_period("M").astype(str))
    monthly = monthly.groupby(["month", "modality"], as_index=False).size()
    st.plotly_chart(
        px.line(
            monthly, x="month", y="size", color="modality", markers=True, title="Monthly volume"
        ),
        use_container_width=True,
    )

with pages[1]:
    st.subheader("Basic workflow bottleneck analysis")
    workflow = filtered.copy()
    workflow["wait_minutes"] = (
        workflow["acquisition_start"] - workflow["exam_datetime"]
    ).dt.total_seconds() / 60
    agg = workflow.groupby("modality", as_index=False).agg(
        median_wait_min=("wait_minutes", "median"),
        p90_wait_min=("wait_minutes", lambda x: x.quantile(0.90)),
        median_acquisition_min=("acquisition_minutes", "median"),
    )
    st.dataframe(agg.round(1), use_container_width=True, hide_index=True)
    st.plotly_chart(
        px.bar(agg, x="modality", y="p90_wait_min", title="P90 wait time by modality"),
        use_container_width=True,
    )

with pages[2]:
    sla = cfg["reporting_sla"]
    warning_hours = float(
        st.number_input("Warning threshold (hours)", 1.0, 168.0, float(sla["warning_hours"]))
    )
    critical_hours = float(
        st.number_input(
            "Critical threshold (hours)", warning_hours, 336.0, float(sla["critical_hours"])
        )
    )
    alerts = reporting_alerts(
        filtered,
        warning_hours,
        critical_hours,
        now=snapshot_at,
    )
    st.caption(f"Operational snapshot: {snapshot_at:%Y-%m-%d %H:%M}")

    a1, a2, a3, a4 = st.columns(4)
    a1.metric("Pending", int(alerts["report_status"].eq("PENDING").sum()))
    a2.metric("Warning", int(alerts["sla_state"].eq("WARNING").sum()))
    a3.metric("Critical", int(alerts["sla_state"].eq("CRITICAL").sum()))
    a4.metric(
        "GES pending", int((alerts["ges_flag"] & alerts["report_status"].eq("PENDING")).sum())
    )

    pending = alerts[alerts["report_status"].eq("PENDING")].copy()
    display_cols = [
        "priority_score",
        "accession_alias",
        "modality",
        "room",
        "patient_class",
        "ges_flag",
        "report_age_hours",
        "sla_state",
    ]
    st.dataframe(pending[display_cols].head(500), use_container_width=True, hide_index=True)
    st.download_button(
        "Download filtered alert table (CSV)",
        pending[display_cols].to_csv(index=False).encode("utf-8"),
        file_name="reporting_alerts_demo.csv",
        mime="text/csv",
    )

with pages[3]:
    contract = load_contract("config/data_contract.yml")
    result = validate_contract(filtered, contract)
    st.metric("Contract status", result["status"])
    if result["missing_columns"]:
        st.error("Missing columns: " + ", ".join(result["missing_columns"]))
    if result["violations"]:
        st.warning("; ".join(result["violations"]))
    quality = quality_summary(filtered)
    st.dataframe(quality, use_container_width=True, hide_index=True)
    st.download_button(
        "Download quality checks (CSV)",
        quality.to_csv(index=False).encode("utf-8"),
        file_name="quality_checks_demo.csv",
        mime="text/csv",
    )

with pages[4]:
    st.subheader("Aggregate synthetic checklist compliance")
    safety = (
        filtered.groupby("modality", as_index=False)["safety_check_complete"]
        .mean()
        .rename(columns={"safety_check_complete": "compliance"})
    )
    safety["compliance_pct"] = safety["compliance"] * 100
    st.plotly_chart(
        px.bar(
            safety,
            x="modality",
            y="compliance_pct",
            range_y=[0, 100],
            title="Safety checklist completion",
        ),
        use_container_width=True,
    )
    st.caption(
        "Synthetic aggregate compliance only. "
        "No MRI eligibility or clinical safety decision logic is included."
    )
