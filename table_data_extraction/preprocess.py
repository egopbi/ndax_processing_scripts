import pandas as pd

from .time_utils import cumulative_time_from_timestamp_series


def trim_leading_rest_rows(dataframe: pd.DataFrame) -> pd.DataFrame:
    if "Status" not in dataframe.columns:
        return dataframe.copy()

    is_non_rest = dataframe["Status"].ne("Rest")
    if not is_non_rest.any():
        return dataframe.iloc[0:0].copy()

    first_non_rest_position = int(is_non_rest.to_numpy().argmax())
    return dataframe.iloc[first_non_rest_position:].copy()


def prepare_x_series(
    dataframe: pd.DataFrame, resolved_x_column: str
) -> pd.Series:
    if resolved_x_column != "Time":
        return dataframe[resolved_x_column]

    trimmed = trim_leading_rest_rows(dataframe)
    if trimmed.empty:
        return pd.Series(
            dtype=float, name=resolved_x_column, index=trimmed.index
        )

    return cumulative_time_from_timestamp_series(
        trimmed["Timestamp"], name=resolved_x_column
    )
