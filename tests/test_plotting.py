from pathlib import Path

from table_data_extraction.config import PLOT_X_COLUMN, PLOT_Y_COLUMN, SOURCE_FILE
from table_data_extraction.plotting import (
    prepare_plot_frame,
    resolve_axis_label,
    save_plot,
    trim_leading_rest_rows,
)
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


def test_prepare_plot_frame_uses_cumulative_time_for_time_axis():
    dataframe = load_ndax_dataframe(SOURCE_FILE)
    trimmed_frame = trim_leading_rest_rows(dataframe)

    plot_frame, x_label, y_label = prepare_plot_frame(
        dataframe,
        x_col=PLOT_X_COLUMN,
        y_col=PLOT_Y_COLUMN,
    )

    assert x_label == "Cumulative Time (s)"
    assert y_label == "Voltage (V)"
    assert plot_frame["__plot_x__"].is_monotonic_increasing
    assert plot_frame["__plot_x__"].iloc[0] == 0
    assert plot_frame["__plot_y__"].iloc[0] == trimmed_frame[PLOT_Y_COLUMN].iloc[0]
    assert trimmed_frame["Status"].iloc[0] != "Rest"
    assert len(plot_frame) == len(trimmed_frame.dropna(subset=[PLOT_X_COLUMN, PLOT_Y_COLUMN]))
    assert plot_frame["__plot_x__"].iloc[-1] > trimmed_frame["Time"].max()


def test_trim_leading_rest_rows_drops_only_initial_rest_block():
    dataframe = load_ndax_dataframe(SOURCE_FILE)
    trimmed_frame = trim_leading_rest_rows(dataframe)

    assert len(trimmed_frame) < len(dataframe)
    assert trimmed_frame["Status"].iloc[0] != "Rest"
    assert dataframe["Status"].iloc[0] == "Rest"
