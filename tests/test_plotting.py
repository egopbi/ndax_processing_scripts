from pathlib import Path

import pandas as pd
import pytest

from table_data_extraction._test_support import sample_ndax_path
from table_data_extraction.config import PLOT_X_COLUMN, PLOT_Y_COLUMN
from table_data_extraction.extrema import _is_local_maximum, _is_local_minimum
import table_data_extraction.plotting as plotting_module
from table_data_extraction.plotting import (
    DEFAULT_PLOT_OUTPUT_HEIGHT_PX,
    DEFAULT_PLOT_OUTPUT_WIDTH_PX,
    MAX_PLOT_OUTPUT_DIMENSION_PX,
    MIN_PLOT_OUTPUT_DIMENSION_PX,
    PLOT_OUTPUT_DPI,
    prepare_plot_frame,
    resolve_axis_label,
    resolve_shared_initial_cycle_trim_points,
    resolve_shared_startup_tail_trim_points,
    save_plot,
    trim_leading_rest_rows,
)
from table_data_extraction.reader import load_ndax_dataframe


def _sample_dataframe_with_first_extremum_at(position: int) -> pd.DataFrame:
    working_voltage = [float(index) for index in range(position + 1)]
    working_voltage.extend([
        float(position - 1),
        float(position - 2),
        float(position - 3),
        float(position - 4),
    ])
    working_length = len(working_voltage)
    timestamps = pd.date_range(
        "2026-03-28 10:00:00", periods=working_length + 1, freq="h"
    )
    return pd.DataFrame({
        "Status": ["Rest", *(["CC_DChg"] * working_length)],
        "Timestamp": timestamps.strftime("%Y-%m-%d %H:%M:%S"),
        "Time": [float(index * 3600) for index in range(working_length + 1)],
        "Voltage": [0.0, *working_voltage],
    })


def test_save_plot_uses_default_dimensions(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    captured: dict[str, object] = {}
    original_subplots = plotting_module.plt.subplots

    def wrapped_subplots(*args, **kwargs):
        figure, axis = original_subplots(*args, **kwargs)
        captured["figsize"] = kwargs.get("figsize")
        original_savefig = figure.savefig

        def wrapped_savefig(*savefig_args, **savefig_kwargs):
            captured["savefig_kwargs"] = dict(savefig_kwargs)
            return original_savefig(*savefig_args, **savefig_kwargs)

        figure.savefig = wrapped_savefig
        return figure, axis

    monkeypatch.setattr(plotting_module.plt, "subplots", wrapped_subplots)

    dataframe = load_ndax_dataframe(sample_ndax_path())
    output_dir = tmp_path / "plots with spaces"
    output_path = output_dir / "plot.jpg"

    written_path = save_plot(
        dataframe,
        x_col=PLOT_X_COLUMN,
        y_col=PLOT_Y_COLUMN,
        output_path=output_path,
        series_label=sample_ndax_path().stem,
        x_limits=None,
        y_limits=None,
    )

    assert captured["figsize"] == (
        DEFAULT_PLOT_OUTPUT_WIDTH_PX / PLOT_OUTPUT_DPI,
        DEFAULT_PLOT_OUTPUT_HEIGHT_PX / PLOT_OUTPUT_DPI,
    )
    assert captured["savefig_kwargs"] == {
        "format": "jpg",
        "dpi": PLOT_OUTPUT_DPI,
    }
    assert written_path.exists()
    assert written_path.suffix == ".jpg"
    assert written_path.stat().st_size > 0


def test_save_plot_uses_custom_dimensions(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    captured: dict[str, object] = {}
    original_subplots = plotting_module.plt.subplots

    def wrapped_subplots(*args, **kwargs):
        figure, axis = original_subplots(*args, **kwargs)
        captured["figsize"] = kwargs.get("figsize")
        original_savefig = figure.savefig

        def wrapped_savefig(*savefig_args, **savefig_kwargs):
            captured["savefig_kwargs"] = dict(savefig_kwargs)
            return original_savefig(*savefig_args, **savefig_kwargs)

        figure.savefig = wrapped_savefig
        return figure, axis

    monkeypatch.setattr(plotting_module.plt, "subplots", wrapped_subplots)

    dataframe = load_ndax_dataframe(sample_ndax_path())
    output_path = tmp_path / "custom_plot.jpg"

    save_plot(
        dataframe,
        x_col=PLOT_X_COLUMN,
        y_col=PLOT_Y_COLUMN,
        output_path=output_path,
        series_label=sample_ndax_path().stem,
        x_limits=None,
        y_limits=None,
        output_width_px=1800,
        output_height_px=1200,
    )

    assert captured["figsize"] == (12.0, 8.0)
    assert captured["savefig_kwargs"] == {
        "format": "jpg",
        "dpi": PLOT_OUTPUT_DPI,
    }


@pytest.mark.parametrize(
    ("output_width_px", "output_height_px", "match"),
    [
        (
            MIN_PLOT_OUTPUT_DIMENSION_PX - 1,
            DEFAULT_PLOT_OUTPUT_HEIGHT_PX,
            rf"^Output width must be between {MIN_PLOT_OUTPUT_DIMENSION_PX} and {MAX_PLOT_OUTPUT_DIMENSION_PX} pixels\.$",
        ),
        (
            DEFAULT_PLOT_OUTPUT_WIDTH_PX,
            MAX_PLOT_OUTPUT_DIMENSION_PX + 1,
            rf"^Output height must be between {MIN_PLOT_OUTPUT_DIMENSION_PX} and {MAX_PLOT_OUTPUT_DIMENSION_PX} pixels\.$",
        ),
    ],
)
def test_save_plot_rejects_unreasonable_dimensions(
    output_width_px: int,
    output_height_px: int,
    match: str,
    tmp_path: Path,
):
    dataframe = load_ndax_dataframe(sample_ndax_path())

    with pytest.raises(ValueError, match=match):
        save_plot(
            dataframe,
            x_col=PLOT_X_COLUMN,
            y_col=PLOT_Y_COLUMN,
            output_path=tmp_path / "plot.jpg",
            series_label=sample_ndax_path().stem,
            x_limits=None,
            y_limits=None,
            output_width_px=output_width_px,
            output_height_px=output_height_px,
        )


def test_resolve_axis_label_formats_known_columns():
    assert resolve_axis_label("Time") == "Total Time (h)"
    assert resolve_axis_label("Voltage") == "Voltage (mV)"
    assert resolve_axis_label("Current(mA)") == "Current (mA)"
    assert (
        resolve_axis_label("Charge_Capacity(mAh)") == "Charge Capacity (mAh)"
    )
    assert resolve_axis_label("Cycle") == "Cycle"


def test_prepare_plot_frame_uses_cumulative_time_for_time_axis():
    dataframe = load_ndax_dataframe(sample_ndax_path())
    trimmed_frame = trim_leading_rest_rows(dataframe)
    y_values = trimmed_frame[PLOT_Y_COLUMN].to_numpy(copy=False)
    first_extremum_position = next(
        position
        for position in range(1, len(y_values) - 1)
        if _is_local_maximum(y_values, position)
        or _is_local_minimum(y_values, position)
    )

    plot_frame, x_label, y_label = prepare_plot_frame(
        dataframe,
        x_col=PLOT_X_COLUMN,
        y_col=PLOT_Y_COLUMN,
    )

    assert x_label == "Total Time (h)"
    assert y_label == "Voltage (mV)"
    assert plot_frame["__plot_x__"].is_monotonic_increasing
    assert plot_frame["__plot_x__"].iloc[0] > 0
    assert (
        plot_frame["__plot_y__"].iloc[0]
        == trimmed_frame[PLOT_Y_COLUMN].iloc[first_extremum_position + 1]
        * 1000
    )
    assert trimmed_frame["Status"].iloc[0] != "Rest"
    assert (
        len(plot_frame)
        == len(trimmed_frame.dropna(subset=[PLOT_X_COLUMN, PLOT_Y_COLUMN]))
        - first_extremum_position
        - 1
    )
    assert plot_frame["__plot_x__"].iloc[-1] > plot_frame["__plot_x__"].iloc[0]


def test_prepare_plot_frame_drops_first_working_row_after_rest_block():
    dataframe = pd.DataFrame({
        "Status": ["Rest", "CC_DChg", "CC_DChg", "CC_DChg"],
        "Time": [0.0, 3600.0, 7200.0, 10800.0],
        "Voltage": [2.9, 3.2, 3.4, 3.6],
    })

    plot_frame, x_label, y_label = prepare_plot_frame(
        dataframe,
        x_col="Time",
        y_col="Voltage",
    )

    assert x_label == "Total Time (h)"
    assert y_label == "Voltage (mV)"
    assert plot_frame["__plot_x__"].tolist() == [2.0, 3.0]
    assert plot_frame["__plot_y__"].tolist() == [3400.0, 3600.0]


def test_prepare_plot_frame_trims_long_startup_tail_before_plotting() -> None:
    dataframe = pd.DataFrame({
        "Status": ["Rest", *(["CC_DChg"] * 10)],
        "Timestamp": [
            "2026-03-28 10:00:00",
            "2026-03-28 11:00:00",
            "2026-03-28 12:00:00",
            "2026-03-28 13:00:00",
            "2026-03-28 14:00:00",
            "2026-03-28 15:00:00",
            "2026-03-28 16:00:00",
            "2026-03-28 17:00:00",
            "2026-03-28 18:00:00",
            "2026-03-28 19:00:00",
            "2026-03-28 20:00:00",
        ],
        "Time": [
            0.0,
            3600.0,
            7200.0,
            10800.0,
            14400.0,
            18000.0,
            21600.0,
            25200.0,
            28800.0,
            32400.0,
            36000.0,
        ],
        "Voltage": [
            0.0,
            -0.3,
            -0.25,
            -0.2,
            -0.15,
            -0.1,
            -0.05,
            -0.06,
            0.22,
            0.0,
            0.1,
        ],
    })

    plot_frame, x_label, y_label = prepare_plot_frame(
        dataframe,
        x_col="Time",
        y_col="Voltage",
    )

    assert x_label == "Total Time (h)"
    assert y_label == "Voltage (mV)"
    assert plot_frame["__plot_x__"].tolist() == [1.0, 2.0, 3.0, 4.0]
    assert plot_frame["__plot_y__"].tolist() == [-60.0, 220.0, 0.0, 100.0]


def test_trim_leading_rest_rows_drops_only_initial_rest_block():
    dataframe = load_ndax_dataframe(sample_ndax_path())
    trimmed_frame = trim_leading_rest_rows(dataframe)

    assert len(trimmed_frame) < len(dataframe)
    assert trimmed_frame["Status"].iloc[0] != "Rest"
    assert dataframe["Status"].iloc[0] == "Rest"


def test_prepare_plot_frame_keeps_non_time_and_non_voltage_series_unchanged():
    dataframe = pd.DataFrame({
        "Status": ["CC_DChg", "CC_DChg"],
        "Cycle": [1.0, 2.0],
        "Current(mA)": [-10.0, -20.0],
    })

    plot_frame, x_label, y_label = prepare_plot_frame(
        dataframe,
        x_col="Cycle",
        y_col="Current(mA)",
    )

    assert x_label == "Cycle"
    assert y_label == "Current (mA)"
    assert plot_frame["__plot_x__"].tolist() == [2.0]
    assert plot_frame["__plot_y__"].tolist() == [-20.0]


def test_prepare_plot_frame_time_falls_back_to_raw_seconds_when_timestamp_missing():
    dataframe = pd.DataFrame({
        "Status": ["CC_DChg", "CC_DChg", "CC_DChg"],
        "Time": [0.0, 3600.0, 7200.0],
        "Voltage": [3.2, 3.3, 3.4],
    })

    plot_frame, x_label, y_label = prepare_plot_frame(
        dataframe,
        x_col="Time",
        y_col="Voltage",
    )

    assert x_label == "Total Time (h)"
    assert y_label == "Voltage (mV)"
    assert plot_frame["__plot_x__"].tolist() == [1.0, 2.0]
    assert plot_frame["__plot_y__"].tolist() == [3300.0, 3400.0]


def test_prepare_plot_frame_time_falls_back_to_raw_seconds_when_timestamp_malformed():
    dataframe = pd.DataFrame({
        "Status": ["CC_DChg", "CC_DChg", "CC_DChg"],
        "Timestamp": ["2026-03-28 10:00:00", "bad-ts", "2026-03-28 12:00:00"],
        "Time": [0.0, 3600.0, 7200.0],
        "Voltage": [3.2, 3.3, 3.4],
    })

    plot_frame, x_label, y_label = prepare_plot_frame(
        dataframe,
        x_col="Time",
        y_col="Voltage",
    )

    assert x_label == "Total Time (h)"
    assert y_label == "Voltage (mV)"
    assert plot_frame["__plot_x__"].tolist() == [1.0, 2.0]
    assert plot_frame["__plot_y__"].tolist() == [3300.0, 3400.0]


def test_resolve_shared_startup_tail_trim_points_uses_majority_value() -> None:
    candidates = [
        _sample_dataframe_with_first_extremum_at(5),
        _sample_dataframe_with_first_extremum_at(5),
        _sample_dataframe_with_first_extremum_at(7),
    ]

    assert (
        resolve_shared_startup_tail_trim_points(candidates, y_col="Voltage")
        == 5
    )


def test_resolve_shared_startup_tail_trim_points_uses_maximum_on_tie() -> None:
    candidates = [
        _sample_dataframe_with_first_extremum_at(5),
        _sample_dataframe_with_first_extremum_at(6),
        _sample_dataframe_with_first_extremum_at(7),
    ]

    assert (
        resolve_shared_startup_tail_trim_points(candidates, y_col="Voltage")
        == 7
    )


def test_resolve_shared_initial_cycle_trim_points_uses_majority_value() -> None:
    candidates = [
        pd.DataFrame({
            "Status": [
                "Rest",
                "CC_DChg",
                "CC_DChg",
                "CC_DChg",
                "Rest",
                "Rest",
                "CC_Chg",
            ]
        }),
        pd.DataFrame({
            "Status": [
                "Rest",
                "CC_DChg",
                "CC_DChg",
                "CC_DChg",
                "Rest",
                "Rest",
                "CC_Chg",
            ]
        }),
        pd.DataFrame({
            "Status": [
                "Rest",
                "CC_DChg",
                "CC_DChg",
                "CC_DChg",
                "CC_DChg",
                "Rest",
                "Rest",
                "CC_Chg",
            ]
        }),
    ]

    assert (
        resolve_shared_initial_cycle_trim_points(
            candidates, startup_tail_trim_points=1
        )
        == 3
    )


def test_resolve_shared_initial_cycle_trim_points_handles_zero_startup_trim() -> None:
    candidates = [
        pd.DataFrame({
            "Status": [
                "CC_DChg",
                "CC_DChg",
                "CC_DChg",
                "Rest",
                "Rest",
                "CC_Chg",
            ]
        }),
        pd.DataFrame({
            "Status": [
                "CC_DChg",
                "CC_DChg",
                "CC_DChg",
                "Rest",
                "Rest",
                "CC_Chg",
            ]
        }),
        pd.DataFrame({
            "Status": [
                "CC_DChg",
                "CC_DChg",
                "CC_DChg",
                "Rest",
                "Rest",
                "CC_Chg",
            ]
        }),
    ]

    assert (
        resolve_shared_initial_cycle_trim_points(
            candidates, startup_tail_trim_points=0
        )
        == 4
    )
