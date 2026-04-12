import importlib.util
from pathlib import Path

import pandas as pd
import pytest

from table_data_extraction.plot_style import resolve_plot_colors
from table_data_extraction.plotting import PlotSeries, save_multi_series_plot


ROOT_DIR = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT_DIR / "scripts" / "plot_ndax.py"
EXAMPLES_DIR = ROOT_DIR / "examples"


def _load_plot_ndax_module():
    spec = importlib.util.spec_from_file_location("plot_ndax_cli", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sample_dataframe() -> pd.DataFrame:
    return pd.DataFrame({
        "Status": ["Rest", "CC_DChg", "CC_DChg"],
        "Timestamp": [
            "2026-03-28 10:00:00",
            "2026-03-28 10:00:05",
            "2026-03-28 10:00:09",
        ],
        "Time": [0.0, 0.0, 4.0],
        "Voltage": [2.9, 3.2, 3.4],
        "Current(mA)": [0.0, -100.0, -120.0],
    })


def _sample_dataframe_without_timestamp() -> pd.DataFrame:
    return pd.DataFrame({
        "Status": ["Rest", "CC_DChg", "CC_DChg"],
        "Time": [0.0, 0.0, 4.0],
        "Voltage": [2.9, 3.2, 3.4],
        "Current(mA)": [0.0, -100.0, -120.0],
    })


def _sample_dataframe_with_malformed_timestamp() -> pd.DataFrame:
    return pd.DataFrame({
        "Status": ["Rest", "CC_DChg", "CC_DChg"],
        "Timestamp": ["2026-03-28 10:00:00", "bad-ts", "2026-03-28 10:00:09"],
        "Time": [0.0, 0.0, 4.0],
        "Voltage": [2.9, 3.2, 3.4],
        "Current(mA)": [0.0, -100.0, -120.0],
    })


def _sample_dataframe_with_startup_tail() -> pd.DataFrame:
    return pd.DataFrame({
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
        "Current(mA)": [
            0.0,
            -1.0,
            -1.0,
            -1.0,
            -1.0,
            -1.0,
            -1.0,
            -1.0,
            -1.0,
            -1.0,
            -1.0,
        ],
    })


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
        "Current(mA)": [0.0, *([-1.0] * working_length)],
    })


def test_cli_errors_when_label_count_does_not_match_files(capsys) -> None:
    module = _load_plot_ndax_module()

    exit_code = module.main([
        "--files",
        "first.ndax",
        "second.ndax",
        "--labels",
        "one_label_only",
        "--y-column",
        "voltage",
    ])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "labels" in captured.err.casefold()
    assert "must match" in captured.err.casefold()


def test_cli_defaults_labels_and_output_path(
    monkeypatch, tmp_path: Path, capsys
) -> None:
    module = _load_plot_ndax_module()
    captured: dict[str, object] = {}

    def fake_load_ndax_dataframe(_path: Path) -> pd.DataFrame:
        return _sample_dataframe()

    def fake_default_plot_output_path(
        *,
        resolved_x_column: str,
        resolved_y_column: str,
        source_paths,
    ) -> Path:
        captured["default_path_args"] = (
            resolved_x_column,
            resolved_y_column,
            list(source_paths),
        )
        return tmp_path / "auto_plot.jpg"

    def fake_save_multi_series_plot(
        series: list[PlotSeries],
        *,
        x_label: str,
        y_label: str,
        output_path: Path,
        x_limits,
        y_limits,
    ) -> Path:
        captured["series"] = list(series)
        captured["x_label"] = x_label
        captured["y_label"] = y_label
        captured["x_limits"] = x_limits
        captured["y_limits"] = y_limits
        captured["output_path"] = output_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"jpg")
        return output_path

    monkeypatch.setattr(
        module, "load_ndax_dataframe", fake_load_ndax_dataframe
    )
    monkeypatch.setattr(
        module, "default_plot_output_path", fake_default_plot_output_path
    )
    monkeypatch.setattr(
        module, "save_multi_series_plot", fake_save_multi_series_plot
    )

    first_file = tmp_path / "sample_a.ndax"
    second_file = tmp_path / "sample_b.ndax"
    exit_code = module.main([
        "--files",
        str(first_file),
        str(second_file),
        "--y-column",
        "voltage",
    ])

    assert exit_code == 0
    assert captured["default_path_args"] == (
        "Time",
        "Voltage",
        [first_file, second_file],
    )
    assert captured["x_label"] == "Total Time (h)"
    assert captured["y_label"] == "Voltage (mV)"
    assert captured["x_limits"] is None
    assert captured["y_limits"] is None
    assert captured["output_path"] == tmp_path / "auto_plot.jpg"

    series = captured["series"]
    assert series is not None
    assert [line.label for line in series] == ["sample", "sample"]
    assert all(len(line.frame) == 1 for line in series)
    assert all(
        line.frame["__plot_x__"].tolist() == [4.0 / 3600] for line in series
    )
    assert all(
        line.frame["__plot_y__"].tolist() == [3400.0] for line in series
    )

    captured_stdout = capsys.readouterr().out
    assert "Saved plot to" in captured_stdout


def test_cli_trims_initial_partial_cycle_for_shared_multi_file_plot(
    monkeypatch, tmp_path: Path
) -> None:
    module = _load_plot_ndax_module()
    captured: dict[str, object] = {}

    def fake_save_multi_series_plot(
        series: list[PlotSeries],
        *,
        x_label: str,
        y_label: str,
        output_path: Path,
        x_limits,
        y_limits,
    ) -> Path:
        captured["series"] = list(series)
        captured["x_label"] = x_label
        captured["y_label"] = y_label
        captured["output_path"] = output_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"jpg")
        return output_path

    def fake_default_plot_output_path(
        *,
        resolved_x_column: str,
        resolved_y_column: str,
        source_paths,
    ) -> Path:
        return tmp_path / "shared_trim_plot.jpg"

    monkeypatch.setattr(
        module, "save_multi_series_plot", fake_save_multi_series_plot
    )
    monkeypatch.setattr(
        module, "default_plot_output_path", fake_default_plot_output_path
    )

    exit_code = module.main([
        "--files",
        str(EXAMPLES_DIR / "example5_5.ndax"),
        str(EXAMPLES_DIR / "example6_6.ndax"),
        str(EXAMPLES_DIR / "example7_7.ndax"),
        "--y-column",
        "voltage",
    ])

    assert exit_code == 0
    series = captured["series"]
    assert series is not None
    first_y_values = [round(line.frame["__plot_y__"].iloc[0], 1) for line in series]
    first_x_values = [round(line.frame["__plot_x__"].iloc[0], 6) for line in series]
    assert first_y_values == [54.4, 46.6, 53.8]
    assert first_x_values[0] == first_x_values[1] == first_x_values[2]


def test_cli_calls_initial_cycle_trim_resolution_when_startup_trim_is_zero(
    monkeypatch, tmp_path: Path
) -> None:
    module = _load_plot_ndax_module()
    captured: dict[str, object] = {}

    def fake_load_ndax_dataframe(_path: Path) -> pd.DataFrame:
        return _sample_dataframe()

    def fake_resolve_shared_startup_tail_trim_points(*_args, **_kwargs) -> int:
        return 0

    def fake_resolve_shared_initial_cycle_trim_points(
        _dataframes, *, startup_tail_trim_points: int
    ) -> int:
        captured["startup_tail_trim_points"] = startup_tail_trim_points
        return 0

    def fake_save_multi_series_plot(
        series: list[PlotSeries],
        *,
        x_label: str,
        y_label: str,
        output_path: Path,
        x_limits,
        y_limits,
    ) -> Path:
        captured["series"] = list(series)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"jpg")
        return output_path

    monkeypatch.setattr(
        module, "load_ndax_dataframe", fake_load_ndax_dataframe
    )
    monkeypatch.setattr(
        module,
        "resolve_shared_startup_tail_trim_points",
        fake_resolve_shared_startup_tail_trim_points,
    )
    monkeypatch.setattr(
        module,
        "resolve_shared_initial_cycle_trim_points",
        fake_resolve_shared_initial_cycle_trim_points,
    )
    monkeypatch.setattr(
        module, "save_multi_series_plot", fake_save_multi_series_plot
    )
    monkeypatch.setattr(
        module,
        "default_plot_output_path",
        lambda **_kwargs: tmp_path / "zero_startup_trim.jpg",
    )

    exit_code = module.main([
        "--files",
        str(tmp_path / "sample_a.ndax"),
        str(tmp_path / "sample_b.ndax"),
        "--y-column",
        "voltage",
    ])

    assert exit_code == 0
    assert captured["startup_tail_trim_points"] == 0


def test_cli_supports_case_insensitive_x_column_and_limits(
    monkeypatch, tmp_path: Path
) -> None:
    module = _load_plot_ndax_module()
    captured: dict[str, object] = {}

    def fake_load_ndax_dataframe(_path: Path) -> pd.DataFrame:
        return _sample_dataframe()

    def fail_if_called(**_kwargs):
        raise AssertionError(
            "default_plot_output_path should not be called when --output is provided"
        )

    def fake_save_multi_series_plot(
        series: list[PlotSeries],
        *,
        x_label: str,
        y_label: str,
        output_path: Path,
        x_limits,
        y_limits,
    ) -> Path:
        captured["series"] = list(series)
        captured["x_label"] = x_label
        captured["y_label"] = y_label
        captured["output_path"] = output_path
        captured["x_limits"] = x_limits
        captured["y_limits"] = y_limits
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"jpg")
        return output_path

    monkeypatch.setattr(
        module, "load_ndax_dataframe", fake_load_ndax_dataframe
    )
    monkeypatch.setattr(module, "default_plot_output_path", fail_if_called)
    monkeypatch.setattr(
        module, "save_multi_series_plot", fake_save_multi_series_plot
    )

    explicit_output = tmp_path / "custom" / "my_plot.jpg"
    exit_code = module.main([
        "--files",
        str(tmp_path / "sample.ndax"),
        "--y-column",
        "voltage",
        "--x-column",
        "current(ma)",
        "--x-min",
        "-120",
        "--x-max",
        "-90",
        "--y-min",
        "3000",
        "--y-max",
        "3500",
        "--output",
        str(explicit_output),
    ])

    assert exit_code == 0
    assert captured["x_label"] == "Current (mA)"
    assert captured["y_label"] == "Voltage (mV)"
    assert captured["x_limits"] == (-120.0, -90.0)
    assert captured["y_limits"] == (3000.0, 3500.0)
    assert captured["output_path"] == explicit_output

    series = captured["series"]
    assert series is not None
    assert len(series) == 1
    assert series[0].frame["__plot_x__"].tolist() == [-120.0]
    assert series[0].frame["__plot_y__"].tolist() == [3400.0]


def test_save_multi_series_plot_uses_upper_right_legend_and_axis_limits(
    monkeypatch, tmp_path: Path
) -> None:
    import table_data_extraction.plotting as plotting_module

    captured: dict[str, object] = {}
    original_subplots = plotting_module.plt.subplots

    def wrapped_subplots(*args, **kwargs):
        figure, axis = original_subplots(*args, **kwargs)
        captured["axis"] = axis
        return figure, axis

    monkeypatch.setattr(plotting_module.plt, "subplots", wrapped_subplots)

    plot_series = [
        PlotSeries(
            label="line_a",
            frame=pd.DataFrame({
                "__plot_x__": [0.0, 1.0, 2.0],
                "__plot_y__": [1.0, 2.0, 3.0],
            }),
        ),
        PlotSeries(
            label="line_b",
            frame=pd.DataFrame({
                "__plot_x__": [0.0, 1.0, 2.0],
                "__plot_y__": [1.5, 2.5, 3.5],
            }),
        ),
    ]
    output_path = tmp_path / "multi.jpg"

    written_path = save_multi_series_plot(
        plot_series,
        x_label="Voltage (V)",
        y_label="Current (mA)",
        output_path=output_path,
        x_limits=(0.5, 1.5),
        y_limits=(1.2, 3.2),
    )

    assert written_path == output_path
    assert output_path.exists()
    axis = captured["axis"]
    assert axis is not None
    assert tuple(axis.get_xlim()) == (0.5, 1.5)
    assert tuple(axis.get_ylim()) == (1.2, 3.2)
    assert axis.get_legend() is not None
    assert axis.get_legend()._loc == 1
    assert len(axis.xaxis.get_minorticklocs()) == 0
    assert len(axis.yaxis.get_minorticklocs()) == 0
    assert any(line.get_visible() for line in axis.get_xgridlines())
    assert any(line.get_visible() for line in axis.get_ygridlines())
    assert not any(
        tick.gridline.get_visible() for tick in axis.xaxis.get_minor_ticks()
    )
    assert not any(
        tick.gridline.get_visible() for tick in axis.yaxis.get_minor_ticks()
    )


def test_cli_time_falls_back_to_raw_seconds_when_timestamp_missing(
    monkeypatch, tmp_path: Path
) -> None:
    module = _load_plot_ndax_module()
    captured: dict[str, object] = {}

    def fake_load_ndax_dataframe(_path: Path) -> pd.DataFrame:
        return _sample_dataframe_without_timestamp()

    def fake_save_multi_series_plot(
        series: list[PlotSeries],
        *,
        x_label: str,
        y_label: str,
        output_path: Path,
        x_limits,
        y_limits,
    ) -> Path:
        captured["series"] = list(series)
        captured["x_label"] = x_label
        captured["y_label"] = y_label
        captured["output_path"] = output_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"jpg")
        return output_path

    monkeypatch.setattr(
        module, "load_ndax_dataframe", fake_load_ndax_dataframe
    )
    monkeypatch.setattr(
        module, "save_multi_series_plot", fake_save_multi_series_plot
    )

    output_file = tmp_path / "plot.jpg"
    exit_code = module.main([
        "--files",
        str(tmp_path / "sample.ndax"),
        "--y-column",
        "voltage",
        "--output",
        str(output_file),
    ])

    assert exit_code == 0
    assert captured["x_label"] == "Total Time (h)"
    assert captured["y_label"] == "Voltage (mV)"
    series = captured["series"]
    assert series is not None
    assert len(series) == 1
    assert series[0].frame["__plot_x__"].tolist() == [4.0 / 3600]
    assert series[0].frame["__plot_y__"].tolist() == [3400.0]


def test_cli_help_mentions_time_hours_and_voltage_millivolts() -> None:
    module = _load_plot_ndax_module()
    help_text = module._build_parser().format_help()

    assert "units are hours" in help_text
    assert "units are mV" in help_text


def test_cli_time_falls_back_to_raw_seconds_when_timestamp_malformed(
    monkeypatch, tmp_path: Path
) -> None:
    module = _load_plot_ndax_module()
    captured: dict[str, object] = {}

    def fake_load_ndax_dataframe(_path: Path) -> pd.DataFrame:
        return _sample_dataframe_with_malformed_timestamp()

    def fake_save_multi_series_plot(
        series: list[PlotSeries],
        *,
        x_label: str,
        y_label: str,
        output_path: Path,
        x_limits,
        y_limits,
    ) -> Path:
        captured["series"] = list(series)
        captured["x_label"] = x_label
        captured["y_label"] = y_label
        captured["output_path"] = output_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"jpg")
        return output_path

    monkeypatch.setattr(
        module, "load_ndax_dataframe", fake_load_ndax_dataframe
    )
    monkeypatch.setattr(
        module, "save_multi_series_plot", fake_save_multi_series_plot
    )

    output_file = tmp_path / "plot.jpg"
    exit_code = module.main([
        "--files",
        str(tmp_path / "sample.ndax"),
        "--y-column",
        "voltage",
        "--output",
        str(output_file),
    ])

    assert exit_code == 0
    assert captured["x_label"] == "Total Time (h)"
    assert captured["y_label"] == "Voltage (mV)"
    series = captured["series"]
    assert series is not None
    assert len(series) == 1
    assert series[0].frame["__plot_x__"].tolist() == [4.0 / 3600]
    assert series[0].frame["__plot_y__"].tolist() == [3400.0]


def test_cli_trims_long_startup_tail_before_plotting(
    monkeypatch, tmp_path: Path
) -> None:
    module = _load_plot_ndax_module()
    captured: dict[str, object] = {}

    def fake_load_ndax_dataframe(_path: Path) -> pd.DataFrame:
        return _sample_dataframe_with_startup_tail()

    def fake_save_multi_series_plot(
        series: list[PlotSeries],
        *,
        x_label: str,
        y_label: str,
        output_path: Path,
        x_limits,
        y_limits,
    ) -> Path:
        captured["series"] = list(series)
        captured["x_label"] = x_label
        captured["y_label"] = y_label
        captured["output_path"] = output_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"jpg")
        return output_path

    monkeypatch.setattr(
        module, "load_ndax_dataframe", fake_load_ndax_dataframe
    )
    monkeypatch.setattr(
        module, "save_multi_series_plot", fake_save_multi_series_plot
    )

    output_file = tmp_path / "plot.jpg"
    exit_code = module.main([
        "--files",
        str(tmp_path / "sample.ndax"),
        "--y-column",
        "voltage",
        "--output",
        str(output_file),
    ])

    assert exit_code == 0
    assert captured["x_label"] == "Total Time (h)"
    assert captured["y_label"] == "Voltage (mV)"
    series = captured["series"]
    assert series is not None
    assert len(series) == 1
    assert series[0].frame["__plot_x__"].tolist() == [1.0, 2.0, 3.0, 4.0]
    assert series[0].frame["__plot_y__"].tolist() == [-60.0, 220.0, 0.0, 100.0]


def test_cli_applies_shared_majority_startup_trim_for_multi_file_plot(
    monkeypatch, tmp_path: Path
) -> None:
    module = _load_plot_ndax_module()
    captured: dict[str, object] = {}
    frames = {
        "sample_a.ndax": _sample_dataframe_with_first_extremum_at(5),
        "sample_b.ndax": _sample_dataframe_with_first_extremum_at(5),
        "sample_c.ndax": _sample_dataframe_with_first_extremum_at(7),
    }

    def fake_load_ndax_dataframe(path: Path) -> pd.DataFrame:
        return frames[path.name]

    def fake_save_multi_series_plot(
        series: list[PlotSeries],
        *,
        x_label: str,
        y_label: str,
        output_path: Path,
        x_limits,
        y_limits,
    ) -> Path:
        captured["series"] = list(series)
        captured["x_label"] = x_label
        captured["y_label"] = y_label
        captured["output_path"] = output_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"jpg")
        return output_path

    monkeypatch.setattr(
        module, "load_ndax_dataframe", fake_load_ndax_dataframe
    )
    monkeypatch.setattr(
        module, "save_multi_series_plot", fake_save_multi_series_plot
    )

    output_file = tmp_path / "plot.jpg"
    exit_code = module.main([
        "--files",
        str(tmp_path / "sample_a.ndax"),
        str(tmp_path / "sample_b.ndax"),
        str(tmp_path / "sample_c.ndax"),
        "--y-column",
        "voltage",
        "--output",
        str(output_file),
    ])

    assert exit_code == 0
    series = captured["series"]
    assert series is not None
    assert [len(line.frame) for line in series] == [4, 4, 6]
    assert series[2].frame["__plot_y__"].tolist() == [
        6000.0,
        7000.0,
        6000.0,
        5000.0,
        4000.0,
        3000.0,
    ]


def test_cli_applies_largest_startup_trim_when_candidates_tie(
    monkeypatch, tmp_path: Path
) -> None:
    module = _load_plot_ndax_module()
    captured: dict[str, object] = {}
    frames = {
        "sample_a.ndax": _sample_dataframe_with_first_extremum_at(5),
        "sample_b.ndax": _sample_dataframe_with_first_extremum_at(6),
        "sample_c.ndax": _sample_dataframe_with_first_extremum_at(7),
    }

    def fake_load_ndax_dataframe(path: Path) -> pd.DataFrame:
        return frames[path.name]

    def fake_save_multi_series_plot(
        series: list[PlotSeries],
        *,
        x_label: str,
        y_label: str,
        output_path: Path,
        x_limits,
        y_limits,
    ) -> Path:
        captured["series"] = list(series)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"jpg")
        return output_path

    monkeypatch.setattr(
        module, "load_ndax_dataframe", fake_load_ndax_dataframe
    )
    monkeypatch.setattr(
        module, "save_multi_series_plot", fake_save_multi_series_plot
    )

    output_file = tmp_path / "plot.jpg"
    exit_code = module.main([
        "--files",
        str(tmp_path / "sample_a.ndax"),
        str(tmp_path / "sample_b.ndax"),
        str(tmp_path / "sample_c.ndax"),
        "--y-column",
        "voltage",
        "--output",
        str(output_file),
    ])

    assert exit_code == 0
    series = captured["series"]
    assert series is not None
    assert [len(line.frame) for line in series] == [2, 3, 4]


def test_resolve_plot_colors_returns_expected_prefixes_and_order() -> None:
    assert resolve_plot_colors(1) == ["#1718FE"]
    assert resolve_plot_colors(2) == ["#1718FE", "#D35400"]
    assert resolve_plot_colors(3) == ["#1718FE", "#D35400", "#128A0C"]
    assert resolve_plot_colors(8) == [
        "#1718FE",
        "#D35400",
        "#128A0C",
        "#7A44F6",
        "#C0392B",
        "#008AA6",
        "#1B1F28",
        "#A61E4D",
    ]


def test_cli_uses_first_two_palette_colors_for_first_two_series(
    monkeypatch, tmp_path: Path
) -> None:
    module = _load_plot_ndax_module()
    import table_data_extraction.plotting as plotting_module

    captured: dict[str, object] = {}

    def fake_load_ndax_dataframe(_path: Path) -> pd.DataFrame:
        return _sample_dataframe()

    original_subplots = plotting_module.plt.subplots

    def wrapped_subplots(*args, **kwargs):
        figure, axis = original_subplots(*args, **kwargs)
        captured["axis"] = axis
        return figure, axis

    monkeypatch.setattr(
        module, "load_ndax_dataframe", fake_load_ndax_dataframe
    )
    monkeypatch.setattr(plotting_module.plt, "subplots", wrapped_subplots)

    output_file = tmp_path / "palette.jpg"
    exit_code = module.main([
        "--files",
        str(tmp_path / "first.ndax"),
        str(tmp_path / "second.ndax"),
        "--y-column",
        "voltage",
        "--output",
        str(output_file),
    ])

    assert exit_code == 0
    axis = captured["axis"]
    assert axis is not None
    assert [line.get_color() for line in axis.lines[:2]] == [
        "#1718FE",
        "#D35400",
    ]


def test_resolve_plot_colors_rejects_more_than_eight_series() -> None:
    with pytest.raises(
        ValueError,
        match=r"^At most 8 input files are supported for plotting\.$",
    ):
        resolve_plot_colors(9)


def test_resolve_plot_colors_error_uses_palette_length(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import table_data_extraction.plot_style as plot_style_module

    monkeypatch.setattr(
        plot_style_module,
        "PLOT_COLOR_PALETTE",
        ("#111111", "#222222", "#333333"),
    )

    with pytest.raises(
        ValueError,
        match=r"^At most 3 input files are supported for plotting\.$",
    ):
        plot_style_module.resolve_plot_colors(4)


def test_cli_rejects_more_than_eight_input_files(
    monkeypatch, tmp_path: Path
) -> None:
    module = _load_plot_ndax_module()

    def fake_load_ndax_dataframe(_path: Path) -> pd.DataFrame:
        return _sample_dataframe()

    monkeypatch.setattr(
        module, "load_ndax_dataframe", fake_load_ndax_dataframe
    )

    with pytest.raises(
        ValueError,
        match=r"^At most 8 input files are supported for plotting\.$",
    ):
        module.run([
            "--files",
            *(str(tmp_path / f"sample_{index}.ndax") for index in range(9)),
            "--y-column",
            "voltage",
            "--output",
            str(tmp_path / "plot.jpg"),
        ])
