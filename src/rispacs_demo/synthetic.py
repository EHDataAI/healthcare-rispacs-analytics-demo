from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class DemoSpec:
    rows: int = 50_000
    seed: int = 20260928
    start_date: str = "2025-01-01"
    end_date: str = "2025-12-31"


def _random_datetimes(
    rng: np.random.Generator,
    n: int,
    start: str,
    end: str,
) -> pd.Series:
    start_ts = pd.Timestamp(start)
    end_ts = pd.Timestamp(end) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
    span_seconds = int((end_ts - start_ts).total_seconds())
    offsets = rng.integers(
        0,
        span_seconds,
        size=n,
    )

    return pd.Series(start_ts + pd.to_timedelta(offsets, unit="s"))


def generate_demo_dataset(
    spec: DemoSpec,
) -> pd.DataFrame:
    rng = np.random.default_rng(spec.seed)
    n = spec.rows

    modality = rng.choice(
        ["CT", "MR", "US", "CR", "DX"],
        n,
        p=[0.24, 0.13, 0.20, 0.18, 0.25],
    )

    room_map = {
        "CT": ["CT_01", "CT_02"],
        "MR": ["MR_01", "MR_02"],
        "US": ["US_01", "US_02", "US_03"],
        "CR": ["CR_01"],
        "DX": ["DX_01", "DX_02"],
    }

    room = np.array(
        [rng.choice(room_map[m]) for m in modality],
        dtype=object,
    )

    patient_class = rng.choice(
        [
            "OUTPATIENT",
            "INPATIENT",
            "EMERGENCY",
        ],
        n,
        p=[0.66, 0.19, 0.15],
    )

    exam_dt = _random_datetimes(
        rng,
        n,
        spec.start_date,
        spec.end_date,
    )

    wait_minutes = np.clip(
        rng.lognormal(
            mean=2.8,
            sigma=0.65,
            size=n,
        ),
        2,
        240,
    )

    acquisition_start = exam_dt + pd.to_timedelta(
        wait_minutes,
        unit="m",
    )

    base_duration = {
        "CT": 16,
        "MR": 42,
        "US": 27,
        "CR": 9,
        "DX": 8,
    }

    acquisition_minutes = np.array(
        [
            max(
                3.0,
                rng.normal(
                    base_duration[m],
                    base_duration[m] * 0.25,
                ),
            )
            for m in modality
        ]
    )

    acquisition_end = acquisition_start + pd.to_timedelta(
        acquisition_minutes,
        unit="m",
    )

    pacs_available = acquisition_end + pd.to_timedelta(
        rng.uniform(1, 12, n),
        unit="m",
    )

    ges_flag = rng.random(n) < np.where(
        patient_class == "OUTPATIENT",
        0.10,
        0.16,
    )

    urgency_factor = np.where(
        patient_class == "EMERGENCY",
        0.45,
        1.0,
    )

    ges_factor = np.where(
        ges_flag,
        0.70,
        1.0,
    )

    report_hours = np.clip(
        rng.lognormal(
            mean=2.1,
            sigma=0.85,
            size=n,
        )
        * urgency_factor
        * ges_factor,
        0.15,
        96,
    )

    planned_report_signed = pd.Series(
        pacs_available
        + pd.to_timedelta(
            report_hours,
            unit="h",
        ),
        dtype="datetime64[ns]",
    )

    # Point-in-time snapshot for the synthetic hospital.
    # It corresponds to the latest PACS-available event.
    snapshot_at = pd.Timestamp(pacs_available.max())

    report_age_hours = (snapshot_at - pacs_available).dt.total_seconds() / 3600

    # Active backlog is deliberately concentrated near
    # the operational snapshot instead of being sampled
    # uniformly throughout the entire synthetic year.
    unresolved_probability = np.select(
        [
            ((report_age_hours >= 0) & (report_age_hours < 24)),
            ((report_age_hours >= 24) & (report_age_hours < 48)),
            ((report_age_hours >= 48) & (report_age_hours < 96)),
            ((report_age_hours >= 96) & (report_age_hours < 168)),
        ],
        [
            0.45,
            0.30,
            0.12,
            0.03,
        ],
        default=0.0,
    )

    # A report whose planned signing time lies beyond
    # the snapshot cannot already be marked as SIGNED.
    scheduled_after_snapshot = planned_report_signed > snapshot_at

    pending = scheduled_after_snapshot.to_numpy() | (rng.random(n) < unresolved_probability)

    report_signed = planned_report_signed.copy()
    report_signed.loc[pending] = pd.NaT

    safety_prob = np.where(
        modality == "MR",
        0.965,
        0.985,
    )

    safety_complete = rng.random(n) < safety_prob

    procedure_group = np.select(
        [
            np.isin(
                modality,
                ["CT", "MR"],
            ),
            modality == "US",
            np.isin(
                modality,
                ["CR", "DX"],
            ),
        ],
        [
            "CROSS_SECTIONAL",
            "ULTRASOUND",
            "RADIOGRAPHY",
        ],
        default="OTHER",
    )

    df = pd.DataFrame(
        {
            "accession_alias": [f"ACC-{i:08d}" for i in range(1, n + 1)],
            "exam_datetime": exam_dt,
            "modality": modality,
            "room": room,
            "patient_class": patient_class,
            "acquisition_start": acquisition_start,
            "acquisition_end": acquisition_end,
            "pacs_available_at": pacs_available,
            "report_signed_at": report_signed,
            "report_status": np.where(
                pending,
                "PENDING",
                "SIGNED",
            ),
            "ges_flag": ges_flag.astype(bool),
            "safety_check_complete": (safety_complete.astype(bool)),
            "procedure_group": procedure_group,
        }
    )

    # Small, deliberate imperfections for the public
    # Data Quality Lab.
    dirty_count = max(
        1,
        int(n * 0.01),
    )

    dirty_idx = rng.choice(
        df.index.to_numpy(),
        dirty_count,
        replace=False,
    )

    third = max(
        1,
        dirty_count // 3,
    )

    df.loc[
        dirty_idx[:third],
        "room",
    ] = None

    df.loc[
        dirty_idx[third : 2 * third],
        "modality",
    ] = "UNKNOWN"

    reversed_idx = dirty_idx[2 * third :]

    df.loc[
        reversed_idx,
        "acquisition_end",
    ] = df.loc[
        reversed_idx,
        "acquisition_start",
    ] - pd.Timedelta(minutes=5)

    return df.sort_values("exam_datetime").reset_index(drop=True)


def write_demo_dataset(
    path: str | Path,
    spec: DemoSpec,
) -> Path:
    out = Path(path)

    out.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    generate_demo_dataset(spec).to_parquet(
        out,
        index=False,
    )

    return out
