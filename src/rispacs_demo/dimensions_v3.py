from __future__ import annotations

import pandas as pd


def room_groups_by_modality(
    df: pd.DataFrame,
) -> dict[str, tuple[str, ...]]:
    required = {
        "modality",
        "room",
    }

    if df.empty or not required.issubset(df.columns):
        return {}

    valid = (
        df.loc[
            :,
            [
                "modality",
                "room",
            ],
        ]
        .dropna(
            subset=[
                "modality",
                "room",
            ]
        )
        .copy()
    )

    if valid.empty:
        return {}

    valid["modality"] = valid["modality"].astype(str).str.strip().str.upper()

    valid["room"] = valid["room"].astype(str).str.strip()

    valid = valid[valid["modality"].ne("") & valid["room"].ne("")]

    mapping: dict[
        str,
        tuple[str, ...],
    ] = {}

    for modality, group in valid.groupby(
        "modality",
        sort=True,
    ):
        mapping[str(modality)] = tuple(sorted(set(group["room"])))

    return mapping


def resolve_room_selection(
    room_groups: dict[
        str,
        tuple[str, ...],
    ],
    selected_groups: list[str] | tuple[str, ...],
    selected_rooms: list[str] | tuple[str, ...],
) -> tuple[str, ...]:
    groups = tuple(str(value) for value in selected_groups)

    if groups:
        resolved: set[str] = set()

        for modality in groups:
            resolved.update(
                room_groups.get(
                    modality,
                    (),
                )
            )

        return tuple(sorted(resolved))

    return tuple(sorted({str(room) for room in selected_rooms}))


def procedure_display_categories(
    df: pd.DataFrame,
) -> pd.Series:
    if df.empty or "procedure_group" not in df.columns:
        return pd.Series(
            dtype="object",
        )

    groups = df["procedure_group"].fillna("Unknown procedure").astype(str).str.strip()

    if "modality" not in df.columns:
        return groups

    modalities = df["modality"].fillna("").astype(str).str.strip().str.upper()

    normalized_groups = (
        groups.str.casefold()
        .str.replace(
            "_",
            "-",
            regex=False,
        )
        .str.replace(
            " ",
            "-",
            regex=False,
        )
    )

    result = groups.copy()

    cross_sectional = normalized_groups == "cross-sectional"

    result.loc[cross_sectional & modalities.eq("CT")] = "CT"

    result.loc[cross_sectional & modalities.eq("MR")] = "MR"

    other_cross_sectional = cross_sectional & ~modalities.isin(
        [
            "CT",
            "MR",
        ]
    )

    result.loc[other_cross_sectional] = modalities.loc[other_cross_sectional].replace(
        "",
        "Other cross-sectional",
    )

    return result
