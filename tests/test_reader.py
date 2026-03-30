from table_data_extraction.reader import list_columns, load_ndax_dataframe
from table_data_extraction._test_support import sample_ndax_path


def test_load_ndax_dataframe_returns_non_empty_dataframe():
    dataframe = load_ndax_dataframe(sample_ndax_path())

    assert not dataframe.empty
    assert len(dataframe.index) > 0
    assert "Time" in dataframe.columns
    assert "Voltage" in dataframe.columns


def test_list_columns_returns_expected_column_names():
    columns = list_columns(sample_ndax_path())

    assert columns
    assert "Current(mA)" in columns
