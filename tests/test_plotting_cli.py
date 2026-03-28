import importlib.util
from pathlib import Path

import pandas as pd

from table_data_extraction.plotting import PlotSeries, save_multi_series_plot


ROOT_DIR = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT_DIR / "scripts" / "plot_ndax.py"


def _load_plot_ndax_module():
    spec = importlib.util.spec_from_file_location("plot_ndax_cli", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sample_dataframe() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Status": ["Rest", "CC_DChg", "CC_DChg"],
            "Timestamp": [
                "2026-03-28 10:00:00",
                "2026-03-28 10:00:05",
                "2026-03-28 10:00:09",
            ],
            "Time": [0.0, 0.0, 4.0],
            "Voltage": [2.9, 3.2, 3.4],
            "Current(mA)": [0.0, -100.0, -120.0],
        }
    )


def _sample_dataframe_without_timestamp() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Status": ["Rest", "CC_DChg", "CC_DChg"],
            "Time": [0.0, 0.0, 4.0],
            "Voltage": [2.9, 3.2, 3.4],
            "Current(mA)": [0.0, -100.0, -120.0],
        }
    )


def _sample_dataframe_with_malformed_timestamp() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Status": ["Rest", "CC_DChg", "CC_DChg"],
            "Timestamp": ["2026-03-28 10:00:00", "bad-ts", "2026-03-28 10:00:09"],
            "Time": [0.0, 0.0, 4.0],
            "Voltage": [2.9, 3.2, 3.4],
            "Current(mA)": [0.0, -100.0, -120.0],
        }
    )


def test_cli_errors_when_label_count_does_not_match_files(capsys) -> None:
    module = _load_plot_ndax_module()

    exit_code = module.main(
        [
            "--files",
            "first.ndax",
            "second.ndax",
            "--labels",
            "one_label_only",
            "--y-column",
            "voltage",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "labels" in captured.err.casefold()
    assert "must match" in captured.err.casefold()


def test_cli_defaults_labels_and_output_path(monkeypatch, tmp_path: Path, capsys) -> None:
    module = _load_plot_ndax_module()
    captured: dict[str, object] = {}

    def fake_load_ndax_dataframe(_path: Path) -> pd.DataFrame:
        return _sample_dataframe()

    def fake_default_plot_output_path(*, resolved_x_column: str, resolved_y_column: str) -> Path:
        captured["default_path_args"] = (resolved_x_column, resolved_y_column)
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

    monkeypatch.setattr(module, "load_ndax_dataframe", fake_load_ndax_dataframe)
    monkeypatch.setattr(module, "default_plot_output_path", fake_default_plot_output_path)
    monkeypatch.setattr(module, "save_multi_series_plot", fake_save_multi_series_plot)

    first_file = tmp_path / "sample_a.ndax"
    second_file = tmp_path / "sample_b.ndax"
    exit_code = module.main(
        [
            "--files",
            str(first_file),
            str(second_file),
            "--y-column",
            "voltage",
        ]
    )

    assert exit_code == 0
    assert captured["default_path_args"] == ("Time", "Voltage")
    assert captured["x_label"] == "Total Time (h)"
    assert captured["y_label"] == "Voltage (mV)"
    assert captured["x_limits"] is None
    assert captured["y_limits"] is None
    assert captured["output_path"] == tmp_path / "auto_plot.jpg"

    series = captured["series"]
    assert series is not None
    assert [line.label for line in series] == ["sample_a", "sample_b"]
    assert all(len(line.frame) == 2 for line in series)
    assert all(line.frame["__plot_x__"].tolist() == [0.0, 4.0 / 3600] for line in series)
    assert all(line.frame["__plot_y__"].tolist() == [3200.0, 3400.0] for line in series)

    captured_stdout = capsys.readouterr().out
    assert "Saved plot to" in captured_stdout


def test_cli_supports_case_insensitive_x_column_and_limits(monkeypatch, tmp_path: Path) -> None:
    module = _load_plot_ndax_module()
    captured: dict[str, object] = {}

    def fake_load_ndax_dataframe(_path: Path) -> pd.DataFrame:
        return _sample_dataframe()

    def fail_if_called(**_kwargs):
        raise AssertionError("default_plot_output_path should not be called when --output is provided")

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

    monkeypatch.setattr(module, "load_ndax_dataframe", fake_load_ndax_dataframe)
    monkeypatch.setattr(module, "default_plot_output_path", fail_if_called)
    monkeypatch.setattr(module, "save_multi_series_plot", fake_save_multi_series_plot)

    explicit_output = tmp_path / "custom" / "my_plot.jpg"
    exit_code = module.main(
        [
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
        ]
    )

    assert exit_code == 0
    assert captured["x_label"] == "Current (mA)"
    assert captured["y_label"] == "Voltage (mV)"
    assert captured["x_limits"] == (-120.0, -90.0)
    assert captured["y_limits"] == (3000.0, 3500.0)
    assert captured["output_path"] == explicit_output

    series = captured["series"]
    assert series is not None
    assert len(series) == 1
    assert series[0].frame["__plot_x__"].tolist() == [-100.0, -120.0]
    assert series[0].frame["__plot_y__"].tolist() == [3200.0, 3400.0]


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
            frame=pd.DataFrame({"__plot_x__": [0.0, 1.0, 2.0], "__plot_y__": [1.0, 2.0, 3.0]}),
        ),
        PlotSeries(
            label="line_b",
            frame=pd.DataFrame({"__plot_x__": [0.0, 1.0, 2.0], "__plot_y__": [1.5, 2.5, 3.5]}),
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
    assert len(axis.xaxis.get_minorticklocs()) > 0
    assert len(axis.yaxis.get_minorticklocs()) > 0
    assert axis.xaxis.get_minor_formatter().__class__.__name__ == "NullFormatter"
    assert axis.yaxis.get_minor_formatter().__class__.__name__ == "NullFormatter"
    assert any(tick.gridline.get_visible() for tick in axis.xaxis.get_minor_ticks())
    assert any(tick.gridline.get_visible() for tick in axis.yaxis.get_minor_ticks())
    major_x_linewidth = next(
        tick.gridline.get_linewidth() for tick in axis.xaxis.get_major_ticks() if tick.gridline.get_visible()
    )
    minor_x_linewidth = next(
        tick.gridline.get_linewidth() for tick in axis.xaxis.get_minor_ticks() if tick.gridline.get_visible()
    )
    assert minor_x_linewidth > major_x_linewidth


def test_cli_time_falls_back_to_raw_seconds_when_timestamp_missing(monkeypatch, tmp_path: Path) -> None:
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

    monkeypatch.setattr(module, "load_ndax_dataframe", fake_load_ndax_dataframe)
    monkeypatch.setattr(module, "save_multi_series_plot", fake_save_multi_series_plot)

    output_file = tmp_path / "plot.jpg"
    exit_code = module.main(
        [
            "--files",
            str(tmp_path / "sample.ndax"),
            "--y-column",
            "voltage",
            "--output",
            str(output_file),
        ]
    )

    assert exit_code == 0
    assert captured["x_label"] == "Total Time (h)"
    assert captured["y_label"] == "Voltage (mV)"
    series = captured["series"]
    assert series is not None
    assert len(series) == 1
    assert series[0].frame["__plot_x__"].tolist() == [0.0, 4.0 / 3600]
    assert series[0].frame["__plot_y__"].tolist() == [3200.0, 3400.0]


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

    monkeypatch.setattr(module, "load_ndax_dataframe", fake_load_ndax_dataframe)
    monkeypatch.setattr(module, "save_multi_series_plot", fake_save_multi_series_plot)

    output_file = tmp_path / "plot.jpg"
    exit_code = module.main(
        [
            "--files",
            str(tmp_path / "sample.ndax"),
            "--y-column",
            "voltage",
            "--output",
            str(output_file),
        ]
    )

    assert exit_code == 0
    assert captured["x_label"] == "Total Time (h)"
    assert captured["y_label"] == "Voltage (mV)"
    series = captured["series"]
    assert series is not None
    assert len(series) == 1
    assert series[0].frame["__plot_x__"].tolist() == [0.0, 4.0 / 3600]
    assert series[0].frame["__plot_y__"].tolist() == [3200.0, 3400.0]
