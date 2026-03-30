from __future__ import annotations

from typing import Callable

import numpy as np
import pandas as pd

ExtremaIndices = dict[str, int | None]


def _is_local_maximum(y_values: np.ndarray, position: int) -> bool:
    current = y_values[position]
    left = y_values[position - 1]
    right = y_values[position + 1]
    return (
        current >= left
        and current >= right
        and (current > left or current > right)
    )


def _is_local_minimum(y_values: np.ndarray, position: int) -> bool:
    current = y_values[position]
    left = y_values[position - 1]
    right = y_values[position + 1]
    return (
        current <= left
        and current <= right
        and (current < left or current < right)
    )


def _find_first_extremum(
    y_values: np.ndarray,
    start: int,
    stop: int,
    step: int,
    predicate: Callable[[np.ndarray, int], bool],
) -> int | None:
    for position in range(start, stop, step):
        if position <= 0 or position >= len(y_values) - 1:
            continue
        if predicate(y_values, position):
            return position
    return None


def _find_anchor_position(x_values: np.ndarray, anchor_x: float) -> int:
    distances = np.abs(x_values - anchor_x)
    return int(distances.argmin())


def find_six_extrema_indices(
    x_series: pd.Series,
    y_series: pd.Series,
    anchor_x: float,
) -> ExtremaIndices:
    if len(x_series) != len(y_series):
        raise ValueError("x_series and y_series must have the same length.")

    x_values = x_series.to_numpy(dtype=float, copy=False)
    y_values = y_series.to_numpy(copy=False)

    result: ExtremaIndices = {
        "+U_l": None,
        "+U_m": None,
        "+U_r": None,
        "-U_l": None,
        "-U_m": None,
        "-U_r": None,
    }
    if len(y_values) < 3:
        return result

    anchor_position = _find_anchor_position(x_values, float(anchor_x))

    plus_u_r = _find_first_extremum(
        y_values,
        start=anchor_position - 1,
        stop=0,
        step=-1,
        predicate=_is_local_maximum,
    )
    plus_u_m = (
        _find_first_extremum(
            y_values,
            start=plus_u_r - 1,
            stop=0,
            step=-1,
            predicate=_is_local_minimum,
        )
        if plus_u_r is not None
        else None
    )
    plus_u_l = (
        _find_first_extremum(
            y_values,
            start=plus_u_m - 1,
            stop=0,
            step=-1,
            predicate=_is_local_maximum,
        )
        if plus_u_m is not None
        else None
    )

    minus_u_l = _find_first_extremum(
        y_values,
        start=anchor_position + 1,
        stop=len(y_values) - 1,
        step=1,
        predicate=_is_local_minimum,
    )
    minus_u_m = (
        _find_first_extremum(
            y_values,
            start=minus_u_l + 1,
            stop=len(y_values) - 1,
            step=1,
            predicate=_is_local_maximum,
        )
        if minus_u_l is not None
        else None
    )
    minus_u_r = (
        _find_first_extremum(
            y_values,
            start=minus_u_m + 1,
            stop=len(y_values) - 1,
            step=1,
            predicate=_is_local_minimum,
        )
        if minus_u_m is not None
        else None
    )

    result["+U_l"] = plus_u_l
    result["+U_m"] = plus_u_m
    result["+U_r"] = plus_u_r
    result["-U_l"] = minus_u_l
    result["-U_m"] = minus_u_m
    result["-U_r"] = minus_u_r
    return result
