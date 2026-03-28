import pandas as pd

from table_data_extraction.config import SOURCE_FILE
from table_data_extraction.preprocess import prepare_x_series, trim_leading_rest_rows
from table_data_extraction.reader import load_ndax_dataframe


def test_trim_leading_rest_rows_removes_only_initial_contiguous_block() -> None:
    dataframe = pd.DataFrame(
        {
            "Status": ["Rest", "Rest", "CC_DChg", "Rest", "CC_DChg"],
            "Time": [0.0, 10.0, 0.0, 5.0, 10.0],
        }
    )

    trimmed = trim_leading_rest_rows(dataframe)

    assert trimmed["Status"].tolist() == ["CC_DChg", "Rest", "CC_DChg"]
    assert trimmed.index.tolist() == [2, 3, 4]


def test_prepare_x_series_builds_cumulative_time_from_first_non_rest() -> None:
    dataframe = pd.DataFrame(
        {
            "Status": ["Rest", "Rest", "CC_DChg", "CC_DChg"],
            "Time": [0.0, 10.0, 0.0, 30.0],
            "Timestamp": [
                "2026-01-01 00:00:00",
                "2026-01-01 00:00:10",
                "2026-01-01 00:00:15",
                "2026-01-01 00:00:45",
            ],
        }
    )

    prepared = prepare_x_series(dataframe, "Time")

    assert prepared.index.tolist() == [2, 3]
    assert prepared.tolist() == [0.0, 30.0]
    assert prepared.is_monotonic_increasing


def test_prepare_x_series_uses_non_time_columns_as_is() -> None:
    dataframe = pd.DataFrame(
        {
            "Status": ["Rest", "CC_DChg", "CC_DChg"],
            "Timestamp": [
                "2026-01-01 00:00:00",
                "2026-01-01 00:00:10",
                "2026-01-01 00:00:20",
            ],
            "Voltage": [0.2, 0.3, 0.4],
            "Current(mA)": [0.0, -4.0, -4.2],
            "Charge/Discharge Capacity": [0.0, 1.2, 1.4],
            "time": [1.0, 2.0, 3.0],
        }
    )

    assert prepare_x_series(dataframe, "Voltage").equals(dataframe["Voltage"])
    assert prepare_x_series(dataframe, "Current(mA)").equals(dataframe["Current(mA)"])
    assert prepare_x_series(dataframe, "Charge/Discharge Capacity").equals(
        dataframe["Charge/Discharge Capacity"]
    )
    assert prepare_x_series(dataframe, "time").equals(dataframe["time"])


def test_prepare_x_series_for_real_ndax_time_is_monotonic_and_starts_at_zero() -> None:
    dataframe = load_ndax_dataframe(SOURCE_FILE)

    prepared = prepare_x_series(dataframe, "Time")

    assert prepared.iloc[0] == 0
    assert prepared.is_monotonic_increasing


def test_prepare_x_series_returns_empty_for_all_rest_rows() -> None:
    dataframe = pd.DataFrame(
        {
            "Status": ["Rest", "Rest"],
            "Time": [0.0, 10.0],
            "Timestamp": ["2026-01-01 00:00:00", "2026-01-01 00:00:10"],
        }
    )

    prepared = prepare_x_series(dataframe, "Time")

    assert prepared.empty
