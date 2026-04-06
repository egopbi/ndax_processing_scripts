from __future__ import annotations

import pandas as pd

TIMESTAMP_COLUMN = "Timestamp"


def parse_mixed_timestamp_series(values: pd.Series) -> pd.Series:
    return pd.to_datetime(values, errors="coerce", format="mixed")


def timestamps_are_usable(
    dataframe: pd.DataFrame, *, column: str = TIMESTAMP_COLUMN
) -> bool:
    if column not in dataframe.columns:
        return False

    parsed_timestamps = parse_mixed_timestamp_series(dataframe[column])
    return parsed_timestamps.notna().all()


def cumulative_time_from_timestamp_series(
    values: pd.Series,
    *,
    divisor: float = 1.0,
    name: str | None = None,
) -> pd.Series:
    parsed_timestamps = parse_mixed_timestamp_series(values)
    if parsed_timestamps.empty:
        return pd.Series(dtype=float, index=values.index, name=name)

    cumulative_time = (
        parsed_timestamps - parsed_timestamps.iloc[0]
    ).dt.total_seconds()
    if divisor != 1.0:
        cumulative_time = cumulative_time / divisor
    if name is not None:
        cumulative_time.name = name
    return cumulative_time
