from __future__ import annotations

from typing import Mapping

import pandas as pd

EXTREMA_COLUMNS: tuple[str, ...] = (
    "+U_l",
    "+U_m",
    "+U_r",
    "-U_l",
    "-U_m",
    "-U_r",
)
COMPARISON_TABLE_COLUMNS: tuple[str, ...] = (
    "name",
    *EXTREMA_COLUMNS,
    "Короткое замыкание",
)


def build_comparison_row(
    *,
    label: str,
    x_series: pd.Series,
    y_series: pd.Series,
    anchor_x: float,
    short_circuit_hours: int | None,
    extrema_indices: Mapping[str, int | None],
) -> dict[str, object]:
    if len(x_series) != len(y_series):
        raise ValueError("x_series and y_series must have the same length.")

    _ = anchor_x
    row: dict[str, object] = {"name": label}
    for extrema_label in EXTREMA_COLUMNS:
        extrema_position = extrema_indices.get(extrema_label)
        row[extrema_label] = (
            "" if extrema_position is None else y_series.iloc[extrema_position]
        )
    row["Короткое замыкание"] = (
        "" if short_circuit_hours is None else short_circuit_hours
    )
    return row
