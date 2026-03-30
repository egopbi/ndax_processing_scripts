from __future__ import annotations

import math
from decimal import Decimal, ROUND_HALF_UP
from statistics import median

import pandas as pd

from .extrema import _is_local_maximum, _is_local_minimum
from .preprocess import trim_leading_rest_rows

STARTUP_TAIL_MIN_POINTS = 5


def _timestamps_are_usable(dataframe: pd.DataFrame) -> bool:
    if "Timestamp" not in dataframe.columns:
        return False

    parsed_timestamps = pd.to_datetime(
        dataframe["Timestamp"], errors="coerce", format="mixed"
    )
    return parsed_timestamps.notna().all()


def _find_first_extremum_position(values: pd.Series) -> int | None:
    y_values = values.to_numpy(copy=False)
    for position in range(1, len(y_values) - 1):
        if _is_local_maximum(y_values, position) or _is_local_minimum(
            y_values, position
        ):
            return position
    return None


def _trim_leading_startup_tail(dataframe: pd.DataFrame) -> pd.DataFrame:
    if "Voltage" not in dataframe.columns:
        return dataframe

    first_extremum_position = _find_first_extremum_position(
        dataframe["Voltage"]
    )
    if (
        first_extremum_position is None
        or first_extremum_position < STARTUP_TAIL_MIN_POINTS
    ):
        return dataframe

    return dataframe.iloc[first_extremum_position:].copy()


def _prepare_detection_frame(dataframe: pd.DataFrame) -> pd.DataFrame:
    trimmed = _trim_leading_startup_tail(trim_leading_rest_rows(dataframe))
    if not trimmed.empty:
        trimmed = trimmed.iloc[1:].copy()

    if trimmed.empty:
        return pd.DataFrame(columns=["hours", "voltage_mv"], dtype=float)

    if _timestamps_are_usable(trimmed):
        timestamps = pd.to_datetime(
            trimmed["Timestamp"], errors="coerce", format="mixed"
        )
        hours = (timestamps - timestamps.iloc[0]).dt.total_seconds() / 3600
    else:
        hours = trimmed["Time"] / 3600

    detection_frame = pd.DataFrame({
        "hours": hours,
        "voltage_mv": trimmed["Voltage"] * 1000,
    }).dropna()
    return detection_frame.reset_index(drop=True)


def _detect_threshold_event_time_hours(
    detection_frame: pd.DataFrame,
) -> float | None:
    if len(detection_frame) < 3:
        return None

    y_values = detection_frame["voltage_mv"].to_numpy(copy=False)
    candidate_times: list[float] = []
    for position in range(1, len(detection_frame) - 1):
        if _is_local_maximum(y_values, position) and y_values[position] >= 200:
            candidate_times.append(
                float(detection_frame.iloc[position]["hours"])
            )
        elif (
            _is_local_minimum(y_values, position)
            and y_values[position] <= -200
        ):
            candidate_times.append(
                float(detection_frame.iloc[position]["hours"])
            )

    if not candidate_times:
        return None
    return min(candidate_times)


def _detect_collapse_event_time_hours(
    detection_frame: pd.DataFrame,
) -> float | None:
    if detection_frame.empty:
        return None

    bin_frame = detection_frame.assign(
        bin_start=detection_frame["hours"].map(
            lambda value: math.floor(value / 5) * 5
        )
    )
    amplitude_by_bin = (
        bin_frame.groupby("bin_start", sort=True)["voltage_mv"]
        .agg(["min", "max"])
        .rename(columns={"min": "min_y", "max": "max_y"})
    )
    amplitude_by_bin["amp"] = (
        amplitude_by_bin["max_y"] - amplitude_by_bin["min_y"]
    )

    existing_bins = set(amplitude_by_bin.index.tolist())
    for bin_start in amplitude_by_bin.index.tolist():
        required_bins = [
            bin_start - 15,
            bin_start - 10,
            bin_start - 5,
            bin_start,
            bin_start + 5,
            bin_start + 10,
        ]
        if not all(
            required_bin in existing_bins for required_bin in required_bins
        ):
            continue

        baseline = median([
            float(amplitude_by_bin.at[bin_start - 15, "amp"]),
            float(amplitude_by_bin.at[bin_start - 10, "amp"]),
            float(amplitude_by_bin.at[bin_start - 5, "amp"]),
        ])
        if float(amplitude_by_bin.at[bin_start + 5, "amp"]) >= 0.8 * baseline:
            continue
        if float(amplitude_by_bin.at[bin_start + 10, "amp"]) >= 0.5 * baseline:
            continue

        later_amplitudes = amplitude_by_bin.loc[
            amplitude_by_bin.index >= bin_start + 10, "amp"
        ]
        if later_amplitudes.empty:
            continue
        if (later_amplitudes > 0.6 * baseline).any():
            continue
        return float(bin_start)

    return None


def detect_short_circuit_time_hours(dataframe: pd.DataFrame) -> float | None:
    detection_frame = _prepare_detection_frame(dataframe)

    threshold_time = _detect_threshold_event_time_hours(detection_frame)
    collapse_time = _detect_collapse_event_time_hours(detection_frame)

    candidates = [
        value for value in [threshold_time, collapse_time] if value is not None
    ]
    if not candidates:
        return None
    return min(candidates)


def round_short_circuit_hours(value: float | None) -> int | None:
    if value is None:
        return None

    rounded = (Decimal(str(value)) / Decimal("5")).quantize(
        Decimal("1"), rounding=ROUND_HALF_UP
    ) * Decimal("5")
    return int(rounded)
