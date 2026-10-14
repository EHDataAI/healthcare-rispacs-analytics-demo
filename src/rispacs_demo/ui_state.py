from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from hashlib import sha256

import pandas as pd

from rispacs_demo.reporting_sla import ReportingSLAConfig
from rispacs_demo.ui_helpers import apply_filters


@dataclass(frozen=True)
class DashboardFilters:
    start_date: date
    end_date: date
    modalities: tuple[str, ...]
    patient_classes: tuple[str, ...]
    rooms: tuple[str, ...]
    target_hours: float = 72.0
    warning_window_hours: float = 48.0
    critical_window_hours: float = 24.0

    def validate(self) -> None:
        if self.start_date > self.end_date:
            raise ValueError("start_date must not be after end_date.")

        self.sla_config().validate()

    def sla_config(self) -> ReportingSLAConfig:
        return ReportingSLAConfig(
            target_hours=self.target_hours,
            warning_window_hours=self.warning_window_hours,
            critical_window_hours=self.critical_window_hours,
        )

    def signature(self) -> str:
        payload = "|".join(
            [
                self.start_date.isoformat(),
                self.end_date.isoformat(),
                ",".join(self.modalities),
                ",".join(self.patient_classes),
                ",".join(self.rooms),
                f"{self.target_hours:g}",
                f"{self.warning_window_hours:g}",
                f"{self.critical_window_hours:g}",
            ]
        )

        return sha256(payload.encode("utf-8")).hexdigest()[:16]


def default_dashboard_filters(
    df: pd.DataFrame,
) -> DashboardFilters:
    if df.empty:
        raise ValueError("Cannot create default filters from an empty dataset.")

    exam_datetime = pd.to_datetime(
        df["exam_datetime"],
        errors="coerce",
    )

    valid_dates = exam_datetime.dropna()

    if valid_dates.empty:
        raise ValueError("exam_datetime contains no valid dates.")

    modalities = tuple(sorted(df["modality"].dropna().astype(str).unique().tolist()))

    patient_classes = tuple(sorted(df["patient_class"].dropna().astype(str).unique().tolist()))

    rooms = tuple(sorted(df["room"].dropna().astype(str).unique().tolist()))

    filters = DashboardFilters(
        start_date=valid_dates.min().date(),
        end_date=valid_dates.max().date(),
        modalities=modalities,
        patient_classes=patient_classes,
        rooms=rooms,
    )

    filters.validate()

    return filters


def _selection_for_filter(
    df: pd.DataFrame,
    column: str,
    selected: tuple[str, ...],
) -> list[str] | None:
    available = set(df[column].dropna().astype(str).unique().tolist())

    if set(selected) == available:
        return None

    return list(selected)


def apply_dashboard_filters(
    df: pd.DataFrame,
    filters: DashboardFilters,
) -> pd.DataFrame:
    filters.validate()

    return apply_filters(
        df,
        start_date=filters.start_date,
        end_date=filters.end_date,
        modalities=_selection_for_filter(
            df,
            "modality",
            filters.modalities,
        ),
        patient_classes=_selection_for_filter(
            df,
            "patient_class",
            filters.patient_classes,
        ),
        rooms=_selection_for_filter(
            df,
            "room",
            filters.rooms,
        ),
    )
