from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml
from pandas.api.types import (
    is_bool_dtype,
    is_datetime64_any_dtype,
)

SUPPORTED_TYPES = {
    "string",
    "boolean",
    "datetime",
}


def load_contract(
    path: str | Path,
) -> dict[str, Any]:
    with Path(path).open(
        "r",
        encoding="utf-8",
    ) as fh:
        return yaml.safe_load(fh)


def _string_values_valid(
    series: pd.Series,
) -> bool:
    values = series.dropna()

    if values.empty:
        return True

    return bool(
        values.map(
            lambda value: isinstance(
                value,
                str,
            )
        ).all()
    )


def _boolean_values_valid(
    series: pd.Series,
) -> bool:
    if is_bool_dtype(series.dtype):
        return True

    values = series.dropna()

    if values.empty:
        return True

    return bool(
        values.map(
            lambda value: isinstance(
                value,
                (
                    bool,
                    np.bool_,
                ),
            )
        ).all()
    )


def _type_matches(
    series: pd.Series,
    expected_type: str,
) -> bool:
    normalized = str(expected_type).strip().lower()

    if normalized == "string":
        return _string_values_valid(series)

    if normalized == "boolean":
        return _boolean_values_valid(series)

    if normalized == "datetime":
        return bool(is_datetime64_any_dtype(series.dtype))

    return False


def validate_contract(
    df: pd.DataFrame,
    contract: dict[str, Any],
) -> dict[str, Any]:
    required_columns = contract.get(
        "required_columns",
        [],
    )

    missing_columns = [column for column in required_columns if column not in df.columns]

    type_violations: list[str] = []
    domain_violations: list[str] = []

    rules = contract.get(
        "rules",
        {},
    )

    for column, rule in rules.items():
        if column not in df.columns:
            continue

        expected_type = rule.get("type")

        type_is_valid = True

        if expected_type is not None:
            normalized_type = str(expected_type).strip().lower()

            if normalized_type not in SUPPORTED_TYPES:
                type_violations.append(f"{column}: unsupported contract type {expected_type!r}")

                type_is_valid = False

            elif not _type_matches(
                df[column],
                normalized_type,
            ):
                type_violations.append(
                    f"{column}: expected type {normalized_type}, found {df[column].dtype}"
                )

                type_is_valid = False

        if not type_is_valid:
            continue

        allowed = rule.get("allowed")

        if allowed is not None:
            non_null = df[column].dropna()

            invalid = non_null.loc[~non_null.isin(allowed)]

            if not invalid.empty:
                domain_violations.append(f"{column}: {len(invalid)} values outside allowed set")

    violations = [
        *type_violations,
        *domain_violations,
    ]

    if missing_columns or type_violations:
        status = "FAIL"

    elif domain_violations:
        status = "WARN"

    else:
        status = "PASS"

    return {
        "status": status,
        "missing_columns": (missing_columns),
        "violations": violations,
        "type_violations": (type_violations),
        "domain_violations": (domain_violations),
    }
