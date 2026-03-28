from table_data_extraction.config import CSV_COLUMNS, PLOT_X_COLUMN, PLOT_Y_COLUMN, SOURCE_FILE
from table_data_extraction.health import run_health_check


def test_run_health_check_passes_for_example_ndax():
    result = run_health_check(
        SOURCE_FILE,
        required_columns=[PLOT_X_COLUMN, PLOT_Y_COLUMN, *CSV_COLUMNS],
    )

    assert result.row_count > 0
    assert not result.missing_columns


def test_run_health_check_reports_missing_column():
    result = run_health_check(
        SOURCE_FILE,
        required_columns=["Column That Does Not Exist"],
    )

    assert result.missing_columns == ["Column That Does Not Exist"]
