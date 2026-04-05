from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd

from .config import (
    EXTREMA_WINDOW_POINTS,
    EXTREMA_ZERO_THRESHOLD,
    MIN_EXTREMA_SEPARATION_POINTS,
    MIN_ZONE_POINTS,
)

ExtremaIndices = dict[str, int | None]
Sign = Literal["POS", "NEG", "NEUTRAL"]


@dataclass(frozen=True)
class SignZone:
    sign: Literal["POS", "NEG"]
    start: int
    end: int


def _empty_extrema_indices() -> ExtremaIndices:
    return {
        "+U_l": None,
        "+U_m": None,
        "+U_r": None,
        "-U_l": None,
        "-U_m": None,
        "-U_r": None,
    }


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


def _find_anchor_position(x_values: np.ndarray, anchor_x: float) -> int:
    distances = np.abs(x_values - anchor_x)
    return int(distances.argmin())


def _build_detection_signal(y_values: np.ndarray) -> np.ndarray:
    return (
        pd.Series(y_values, dtype=float)
        .rolling(
            window=EXTREMA_WINDOW_POINTS,
            center=True,
            min_periods=1,
        )
        .median()
        .to_numpy(dtype=float, copy=False)
    )


def _classify_sign(value: float) -> Sign:
    if value > EXTREMA_ZERO_THRESHOLD:
        return "POS"
    if value < -EXTREMA_ZERO_THRESHOLD:
        return "NEG"
    return "NEUTRAL"


def _suppress_short_sign_runs(signs: list[Sign]) -> list[Sign]:
    cleaned = list(signs)
    position = 0
    while position < len(cleaned):
        sign = cleaned[position]
        run_end = position + 1
        while run_end < len(cleaned) and cleaned[run_end] == sign:
            run_end += 1

        if sign != "NEUTRAL" and run_end - position < MIN_ZONE_POINTS:
            for index in range(position, run_end):
                cleaned[index] = "NEUTRAL"

        position = run_end
    return cleaned


def _build_sign_zones(signs: list[Sign]) -> list[SignZone]:
    zones: list[SignZone] = []
    current_sign: Literal["POS", "NEG"] | None = None
    current_start: int | None = None
    current_end: int | None = None

    for index, sign in enumerate(signs):
        if sign == "NEUTRAL":
            continue

        if current_sign is None:
            current_sign = sign
            current_start = index
            current_end = index
            continue

        if sign == current_sign:
            current_end = index
            continue

        assert current_start is not None
        assert current_end is not None
        zones.append(
            SignZone(sign=current_sign, start=current_start, end=current_end)
        )
        current_sign = sign
        current_start = index
        current_end = index

    if current_sign is not None:
        assert current_start is not None
        assert current_end is not None
        zones.append(
            SignZone(sign=current_sign, start=current_start, end=current_end)
        )

    return zones


def _find_nearest_pos_neg_pair(
    zones: list[SignZone], anchor_position: int
) -> tuple[SignZone, SignZone] | None:
    candidate_pairs = [
        (left_zone, right_zone)
        for left_zone, right_zone in zip(zones, zones[1:], strict=False)
        if left_zone.sign == "POS" and right_zone.sign == "NEG"
    ]
    if not candidate_pairs:
        return None

    def distance_to_pair(pair: tuple[SignZone, SignZone]) -> tuple[int, int, int]:
        left_zone, right_zone = pair
        pair_start = left_zone.start
        pair_end = right_zone.end
        if pair_start <= anchor_position <= pair_end:
            distance = 0
        elif anchor_position < pair_start:
            distance = pair_start - anchor_position
        else:
            distance = anchor_position - pair_end

        boundary_distance = abs(anchor_position - right_zone.start)
        return (distance, boundary_distance, pair_start)

    return min(candidate_pairs, key=distance_to_pair)


def _matches_zone_sign(
    value: float, zone_sign: Literal["POS", "NEG"]
) -> bool:
    return value > 0 if zone_sign == "POS" else value < 0


def _collect_local_extrema(
    y_values: np.ndarray,
    zone: SignZone,
    *,
    predicate,
) -> list[int]:
    return [
        position
        for position in range(zone.start, zone.end + 1)
        if 0 < position < len(y_values) - 1
        and predicate(y_values, position)
        and _matches_zone_sign(y_values[position], zone.sign)
    ]


def _is_far_enough(left: int, right: int) -> bool:
    return right - left >= MIN_EXTREMA_SEPARATION_POINTS


def _select_positive_extrema(
    y_values: np.ndarray, zone: SignZone
) -> tuple[int, int, int] | None:
    maxima = _collect_local_extrema(y_values, zone, predicate=_is_local_maximum)
    minima = _collect_local_extrema(y_values, zone, predicate=_is_local_minimum)
    best_candidate: tuple[float, int, int, tuple[int, int, int]] | None = None

    for left_max in maxima:
        for middle_min in minima:
            if middle_min <= left_max or not _is_far_enough(
                left_max, middle_min
            ):
                continue
            for right_max in maxima:
                if right_max <= middle_min or not _is_far_enough(
                    middle_min, right_max
                ):
                    continue

                score = (y_values[left_max] - y_values[middle_min]) + (
                    y_values[right_max] - y_values[middle_min]
                )
                span = right_max - left_max
                candidate = (
                    float(score),
                    right_max,
                    -span,
                    (left_max, middle_min, right_max),
                )
                if best_candidate is None or candidate > best_candidate:
                    best_candidate = candidate

    if best_candidate is None:
        return None

    return best_candidate[-1]


def _select_negative_extrema(
    y_values: np.ndarray, zone: SignZone
) -> tuple[int, int, int] | None:
    minima = _collect_local_extrema(y_values, zone, predicate=_is_local_minimum)
    maxima = _collect_local_extrema(y_values, zone, predicate=_is_local_maximum)
    best_candidate: tuple[float, int, int, tuple[int, int, int]] | None = None

    for left_min in minima:
        for middle_max in maxima:
            if middle_max <= left_min or not _is_far_enough(
                left_min, middle_max
            ):
                continue
            for right_min in minima:
                if right_min <= middle_max or not _is_far_enough(
                    middle_max, right_min
                ):
                    continue

                score = (y_values[middle_max] - y_values[left_min]) + (
                    y_values[middle_max] - y_values[right_min]
                )
                span = right_min - left_min
                candidate = (
                    float(score),
                    -left_min,
                    -span,
                    (left_min, middle_max, right_min),
                )
                if best_candidate is None or candidate > best_candidate:
                    best_candidate = candidate

    if best_candidate is None:
        return None

    return best_candidate[-1]


def find_six_extrema_indices(
    x_series: pd.Series,
    y_series: pd.Series,
    anchor_x: float,
) -> ExtremaIndices:
    if len(x_series) != len(y_series):
        raise ValueError("x_series and y_series must have the same length.")

    result = _empty_extrema_indices()
    if len(y_series) < 3:
        return result

    x_values = x_series.to_numpy(dtype=float, copy=False)
    y_values = y_series.to_numpy(dtype=float, copy=False)
    anchor_position = _find_anchor_position(x_values, float(anchor_x))

    y_det = _build_detection_signal(y_values)
    raw_signs = [_classify_sign(value) for value in y_det]
    cleaned_signs = _suppress_short_sign_runs(raw_signs)
    zones = _build_sign_zones(cleaned_signs)

    selected_pair = _find_nearest_pos_neg_pair(zones, anchor_position)
    if selected_pair is None:
        return result

    positive_zone, negative_zone = selected_pair
    positive_extrema = _select_positive_extrema(y_values, positive_zone)
    negative_extrema = _select_negative_extrema(y_values, negative_zone)

    if positive_extrema is not None:
        result["+U_l"], result["+U_m"], result["+U_r"] = positive_extrema
    if negative_extrema is not None:
        result["-U_l"], result["-U_m"], result["-U_r"] = negative_extrema

    return result
