from table_data_extraction.config import SOURCE_FILE
from table_data_extraction.reader import list_columns, load_ndax_dataframe


def test_load_ndax_dataframe_returns_non_empty_dataframe():
    dataframe = load_ndax_dataframe(SOURCE_FILE)

    assert not dataframe.empty
    assert len(dataframe.index) > 0
    assert "Time" in dataframe.columns
    assert "Voltage" in dataframe.columns


def test_list_columns_returns_expected_column_names():
    columns = list_columns(SOURCE_FILE)

    assert columns
    assert "Current(mA)" in columns
