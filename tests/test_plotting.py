from pathlib import Path

from table_data_extraction.config import PLOT_X_COLUMN, PLOT_Y_COLUMN, SOURCE_FILE
from table_data_extraction.plotting import resolve_axis_label, save_plot
from table_data_extraction.reader import load_ndax_dataframe


def test_save_plot_creates_jpg_file(tmp_path: Path):
    dataframe = load_ndax_dataframe(SOURCE_FILE)
    output_dir = tmp_path / "plots with spaces"
    output_path = output_dir / "plot.jpg"

    written_path = save_plot(
        dataframe,
        x_col=PLOT_X_COLUMN,
        y_col=PLOT_Y_COLUMN,
        output_path=output_path,
        series_label=SOURCE_FILE.stem,
        x_limits=None,
        y_limits=None,
    )

    assert written_path.exists()
    assert written_path.suffix == ".jpg"
    assert written_path.stat().st_size > 0


def test_resolve_axis_label_formats_known_columns():
    assert resolve_axis_label("Time") == "Time (s)"
    assert resolve_axis_label("Voltage") == "Voltage (V)"
    assert resolve_axis_label("Current(mA)") == "Current (mA)"
