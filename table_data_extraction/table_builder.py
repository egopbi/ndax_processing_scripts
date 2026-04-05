from __future__ import annotations

from typing import Mapping, Sequence

import pandas as pd

EXTREMA_COLUMNS: tuple[str, ...] = (
    "+U_l",
    "+U_m",
    "+U_r",
    "-U_l",
    "-U_m",
    "-U_r",
)


def anchor_extrema_key(anchor_index: int, extrema_label: str) -> str:
    return f"anchor_{anchor_index}__{extrema_label}"


def comparison_table_columns_for_anchors(
    anchors: Sequence[float],
) -> tuple[str, ...]:
    block_columns = tuple(
        anchor_extrema_key(anchor_index, extrema_label)
        for anchor_index, _anchor in enumerate(anchors)
        for extrema_label in EXTREMA_COLUMNS
    )
    return ("name", *block_columns, "Короткое замыкание")


def build_comparison_row(
    *,
    label: str,
    y_series: pd.Series,
    anchors: Sequence[float],
    short_circuit_hours: int | None,
    extrema_indices_by_anchor: Sequence[Mapping[str, int | None]],
) -> dict[str, object]:
    if len(anchors) != len(extrema_indices_by_anchor):
        raise ValueError("anchors and extrema_indices_by_anchor must align.")

    row: dict[str, object] = {"name": label}
    for anchor_index, extrema_indices in enumerate(extrema_indices_by_anchor):
        for extrema_label in EXTREMA_COLUMNS:
            extrema_position = extrema_indices.get(extrema_label)
            row[anchor_extrema_key(anchor_index, extrema_label)] = (
                ""
                if extrema_position is None
                else y_series.iloc[extrema_position]
            )
    row["Короткое замыкание"] = (
        "" if short_circuit_hours is None else short_circuit_hours
    )
    return row
