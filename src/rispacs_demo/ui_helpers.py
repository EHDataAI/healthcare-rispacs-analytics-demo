from __future__ import annotations

from collections.abc import Iterable

import pandas as pd


def apply_filters(
    df: pd.DataFrame,
    start_date: object | None = None,
    end_date: object | None = None,
    modalities: Iterable[str] | None = None,
    patient_classes: Iterable[str] | None = None,
    rooms: Iterable[str] | None = None,
) -> pd.DataFrame:
    out = df.copy()

    if start_date is not None:
        start_ts = pd.Timestamp(start_date).normalize()
        out = out[out["exam_datetime"] >= start_ts]

    if end_date is not None:
        end_ts = pd.Timestamp(end_date).normalize() + pd.Timedelta(days=1)
        out = out[out["exam_datetime"] < end_ts]

    if modalities is not None:
        selected = list(modalities)
        out = out[out["modality"].isin(selected)]

    if patient_classes is not None:
        selected = list(patient_classes)
        out = out[out["patient_class"].isin(selected)]

    if rooms is not None:
        selected = list(rooms)
        out = out[out["room"].isin(selected)]

    return out.copy()


def operational_subset(
    df: pd.DataFrame,
) -> pd.DataFrame:
    if df.empty:
        return df.copy()

    required = {
        "exam_datetime",
        "acquisition_start",
        "acquisition_end",
        "pacs_available_at",
    }

    if not required.issubset(df.columns):
        return df.copy()

    valid = (
        df["exam_datetime"].notna()
        & df["acquisition_start"].notna()
        & df["acquisition_end"].notna()
        & df["pacs_available_at"].notna()
        & (df["acquisition_start"] >= df["exam_datetime"])
        & (df["acquisition_end"] >= df["acquisition_start"])
        & (df["pacs_available_at"] >= df["acquisition_end"])
    )

    return df.loc[valid].copy()


def sorted_options(
    df: pd.DataFrame,
    column: str,
) -> list[str]:
    if column not in df.columns:
        return []

    return sorted(df[column].dropna().astype(str).unique().tolist())
