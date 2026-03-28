import pandas as pd
import pytest

from table_data_extraction.columns import resolve_column_name


@pytest.mark.parametrize("user_input", ["voltage", "Voltage", " VOLTAGE "])
def test_resolve_column_name_is_case_insensitive(user_input: str) -> None:
    dataframe = pd.DataFrame(columns=["Time", "Voltage", "Current(mA)"])

    resolved = resolve_column_name(dataframe, user_input)

    assert resolved == "Voltage"


def test_resolve_column_name_lists_available_columns_when_missing() -> None:
    dataframe = pd.DataFrame(columns=["Time", "Voltage", "Current(mA)"])

    with pytest.raises(ValueError) as error_info:
        resolve_column_name(dataframe, "missing")

    message = str(error_info.value)
    assert "Available columns" in message
    assert "Time" in message
    assert "Voltage" in message
    assert "Current(mA)" in message


def test_resolve_column_name_raises_ambiguity_error() -> None:
    dataframe = pd.DataFrame(columns=["Voltage", " voltage ", "Current(mA)"])

    with pytest.raises(ValueError) as error_info:
        resolve_column_name(dataframe, "voltage")

    message = str(error_info.value)
    assert "Ambiguous" in message
    assert "Voltage" in message
    assert " voltage " in message
