import importlib.util
from pathlib import Path

import pandas as pd
import pytest


ROOT_DIR = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT_DIR / "scripts" / "build_comparison_table.py"


def _load_table_cli_module():
    spec = importlib.util.spec_from_file_location(
        "build_comparison_table_cli", SCRIPT_PATH
    )
    assert spec is not None
    assert spec.loader is not None

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sample_dataframe() -> pd.DataFrame:
    return pd.DataFrame({
        "Status": ["Rest", "CC_DChg", "CC_DChg", "CC_DChg"],
        "Timestamp": [
            "2026-03-28 10:00:00",
            "2026-03-28 10:00:05",
            "2026-03-28 10:00:09",
            "2026-03-28 10:00:14",
        ],
        "Time": [0.0, 0.0, 4.0, 9.0],
        "Voltage": [2.9, 3.2, 3.4, 3.3],
        "Current(mA)": [0.0, -100.0, -120.0, -110.0],
    })


def _sample_dataframe_without_timestamp() -> pd.DataFrame:
    return pd.DataFrame({
        "Status": ["Rest", "CC_DChg", "CC_DChg", "CC_DChg"],
        "Time": [0.0, 0.0, 4.0, 9.0],
        "Voltage": [2.9, 3.2, 3.4, 3.3],
        "Current(mA)": [0.0, -100.0, -120.0, -110.0],
    })


def _sample_dataframe_with_malformed_timestamp() -> pd.DataFrame:
    return pd.DataFrame({
        "Status": ["Rest", "CC_DChg", "CC_DChg", "CC_DChg"],
        "Timestamp": [
            "2026-03-28 10:00:00",
            "2026-03-28 10:00:05",
            "bad-ts",
            "2026-03-28 10:00:14",
        ],
        "Time": [0.0, 0.0, 4.0, 9.0],
        "Voltage": [2.9, 3.2, 3.4, 3.3],
        "Current(mA)": [0.0, -100.0, -120.0, -110.0],
    })


def _sample_dataframe_with_time_values_that_differ_from_timestamp_deltas() -> (
    pd.DataFrame
):
    return pd.DataFrame({
        "Status": ["Rest", "CC_DChg", "CC_DChg", "CC_DChg"],
        "Timestamp": [
            "2026-03-28 10:00:00",
            "2026-03-28 10:00:05",
            "2026-03-28 10:00:09",
            "2026-03-28 10:00:14",
        ],
        "Time": [1000.0, 1100.0, 1200.0, 1300.0],
        "Voltage": [2.9, 3.2, 3.4, 3.3],
        "Current(mA)": [0.0, -100.0, -120.0, -110.0],
    })


def _empty_extrema_indices() -> dict[str, int | None]:
    return {
        "+U_l": None,
        "+U_m": None,
        "+U_r": None,
        "-U_l": None,
        "-U_m": None,
        "-U_r": None,
    }


def test_cli_errors_when_label_count_does_not_match_files(capsys) -> None:
    module = _load_table_cli_module()

    exit_code = module.main([
        "--files",
        "first.ndax",
        "second.ndax",
        "--labels",
        "one_label_only",
        "--y-column",
        "voltage",
        "--anchor-x",
        "10",
    ])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "labels" in captured.err.casefold()
    assert "must match" in captured.err.casefold()


def test_cli_defaults_labels_uses_default_output_and_warns_for_missing_extrema(
    monkeypatch, tmp_path: Path, capsys
) -> None:
    module = _load_table_cli_module()
    captured: dict[str, object] = {}

    def fake_load_ndax_dataframe(_path: Path) -> pd.DataFrame:
        return _sample_dataframe()

    def fake_default_table_output_path(
        *, resolved_y_column: str, anchor_x: float
    ) -> Path:
        captured["default_path_args"] = (resolved_y_column, anchor_x)
        return tmp_path / "auto_table.csv"

    def fake_find_six_extrema_indices(x_series, y_series, anchor_x: float):
        captured["first_x_series"] = x_series.tolist()
        captured["first_y_series"] = y_series.tolist()
        captured["first_anchor_x"] = anchor_x
        return {
            "+U_l": None,
            "+U_m": 1,
            "+U_r": None,
            "-U_l": 2,
            "-U_m": None,
            "-U_r": None,
        }

    def fake_detect_short_circuit_time_hours(
        dataframe: pd.DataFrame,
    ) -> float | None:
        captured["short_circuit_dataframe"] = dataframe.copy()
        return 183.0

    def fake_round_short_circuit_hours(value: float | None) -> int | None:
        captured["short_circuit_raw"] = value
        return 185

    def fake_save_comparison_table(
        *, rows, anchor_x: float, output_path: Path, extrema_header_labels=None
    ) -> Path:
        captured["rows"] = list(rows)
        captured["saved_anchor_x"] = anchor_x
        captured["output_path"] = output_path
        captured["extrema_header_labels"] = extrema_header_labels
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            "name;10;;;;;;Короткое замыкание\n;+U_l;+U_m;+U_r;-U_l;-U_m;-U_r;\n",
            encoding="utf-8",
        )
        return output_path

    monkeypatch.setattr(
        module, "load_ndax_dataframe", fake_load_ndax_dataframe
    )
    monkeypatch.setattr(
        module, "default_table_output_path", fake_default_table_output_path
    )
    monkeypatch.setattr(
        module, "find_six_extrema_indices", fake_find_six_extrema_indices
    )
    monkeypatch.setattr(
        module,
        "detect_short_circuit_time_hours",
        fake_detect_short_circuit_time_hours,
    )
    monkeypatch.setattr(
        module, "round_short_circuit_hours", fake_round_short_circuit_hours
    )
    monkeypatch.setattr(
        module, "save_comparison_table", fake_save_comparison_table
    )

    first_file = tmp_path / "sample_a.ndax"
    second_file = tmp_path / "sample_b.ndax"
    exit_code = module.main([
        "--files",
        str(first_file),
        str(second_file),
        "--y-column",
        "voltage",
        "--anchor-x",
        "4",
    ])

    assert exit_code == 0
    assert captured["default_path_args"] == ("Voltage", 4.0)
    assert captured["first_x_series"] == [0.0, 4.0, 9.0]
    assert captured["first_y_series"] == [3200.0, 3400.0, 3300.0]
    assert captured["first_anchor_x"] == 4.0 * 3600
    assert isinstance(captured["short_circuit_dataframe"], pd.DataFrame)
    assert captured["short_circuit_raw"] == 183.0
    assert captured["saved_anchor_x"] == 4.0
    assert captured["output_path"] == tmp_path / "auto_table.csv"
    assert captured["extrema_header_labels"] == (
        "+U_l(mV)",
        "+U_m(mV)",
        "+U_r(mV)",
        "-U_l(mV)",
        "-U_m(mV)",
        "-U_r(mV)",
    )

    rows = captured["rows"]
    assert rows is not None
    assert [row["name"] for row in rows] == ["sample_a", "sample_b"]
    assert all(row["+U_l"] == "" for row in rows)
    assert all(row["+U_m"] == 3400.0 for row in rows)
    assert all(row["+U_r"] == "" for row in rows)
    assert all(row["-U_l"] == 3300.0 for row in rows)
    assert all(row["-U_m"] == "" for row in rows)
    assert all(row["-U_r"] == "" for row in rows)
    assert all(row["Короткое замыкание"] == 185 for row in rows)

    output = capsys.readouterr()
    assert "Saved table to" in output.out
    assert "warning" in output.err.casefold()
    assert "+u_l" in output.err.casefold()


def test_cli_uses_public_y_label_units_for_time_extrema_headers(
    monkeypatch, tmp_path: Path
) -> None:
    module = _load_table_cli_module()
    captured: dict[str, object] = {}

    def fake_load_ndax_dataframe(_path: Path) -> pd.DataFrame:
        return _sample_dataframe_with_time_values_that_differ_from_timestamp_deltas()

    def fake_default_table_output_path(
        *, resolved_y_column: str, anchor_x: float
    ) -> Path:
        captured["default_path_args"] = (resolved_y_column, anchor_x)
        return tmp_path / "time_table.csv"

    def fake_find_six_extrema_indices(x_series, y_series, anchor_x: float):
        captured["x_series"] = x_series.tolist()
        captured["y_series"] = y_series.tolist()
        captured["anchor_x"] = anchor_x
        return {
            "+U_l": 0,
            "+U_m": 1,
            "+U_r": 2,
            "-U_l": 0,
            "-U_m": 1,
            "-U_r": 2,
        }

    def fake_save_comparison_table(
        *, rows, anchor_x: float, output_path: Path, extrema_header_labels=None
    ) -> Path:
        captured["rows"] = list(rows)
        captured["saved_anchor_x"] = anchor_x
        captured["output_path"] = output_path
        captured["extrema_header_labels"] = extrema_header_labels
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("ok\n", encoding="utf-8")
        return output_path

    monkeypatch.setattr(
        module, "load_ndax_dataframe", fake_load_ndax_dataframe
    )
    monkeypatch.setattr(
        module, "default_table_output_path", fake_default_table_output_path
    )
    monkeypatch.setattr(
        module, "find_six_extrema_indices", fake_find_six_extrema_indices
    )
    monkeypatch.setattr(
        module, "save_comparison_table", fake_save_comparison_table
    )

    exit_code = module.main([
        "--files",
        str(tmp_path / "sample_a.ndax"),
        "--y-column",
        "time",
        "--anchor-x",
        "4",
    ])

    assert exit_code == 0
    assert captured["default_path_args"] == ("Time", 4.0)
    assert captured["y_series"] == pytest.approx([
        0.0,
        4.0 / 3600.0,
        9.0 / 3600.0,
    ])
    assert captured["extrema_header_labels"] == (
        "+U_l(h)",
        "+U_m(h)",
        "+U_r(h)",
        "-U_l(h)",
        "-U_m(h)",
        "-U_r(h)",
    )
    rows = captured["rows"]
    assert rows is not None
    assert rows[0]["+U_l"] == 0.0
    assert rows[0]["+U_m"] == pytest.approx(4.0 / 3600.0)
    assert rows[0]["+U_r"] == pytest.approx(9.0 / 3600.0)


def test_cli_writes_empty_short_circuit_cell_when_detector_returns_none(
    monkeypatch, tmp_path: Path
) -> None:
    module = _load_table_cli_module()
    captured: dict[str, object] = {}

    def fake_load_ndax_dataframe(_path: Path) -> pd.DataFrame:
        return _sample_dataframe()

    def fake_find_six_extrema_indices(x_series, y_series, anchor_x: float):
        captured["x_series"] = x_series.tolist()
        captured["y_series"] = y_series.tolist()
        captured["anchor_x"] = anchor_x
        return _empty_extrema_indices()

    def fake_detect_short_circuit_time_hours(
        dataframe: pd.DataFrame,
    ) -> float | None:
        captured["detector_dataframe"] = dataframe.copy()
        return None

    def fake_round_short_circuit_hours(value: float | None) -> int | None:
        captured["rounded_input"] = value
        return None

    def fake_save_comparison_table(
        *, rows, anchor_x: float, output_path: Path, extrema_header_labels=None
    ) -> Path:
        captured["rows"] = list(rows)
        captured["saved_anchor_x"] = anchor_x
        captured["output_path"] = output_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("ok\n", encoding="utf-8")
        return output_path

    monkeypatch.setattr(
        module, "load_ndax_dataframe", fake_load_ndax_dataframe
    )
    monkeypatch.setattr(
        module, "find_six_extrema_indices", fake_find_six_extrema_indices
    )
    monkeypatch.setattr(
        module,
        "detect_short_circuit_time_hours",
        fake_detect_short_circuit_time_hours,
    )
    monkeypatch.setattr(
        module, "round_short_circuit_hours", fake_round_short_circuit_hours
    )
    monkeypatch.setattr(
        module, "save_comparison_table", fake_save_comparison_table
    )

    explicit_output = tmp_path / "custom" / "table.csv"
    exit_code = module.main([
        "--files",
        str(tmp_path / "sample.ndax"),
        "--y-column",
        "voltage",
        "--anchor-x",
        "4",
        "--output",
        str(explicit_output),
    ])

    assert exit_code == 0
    assert isinstance(captured["detector_dataframe"], pd.DataFrame)
    assert captured["rounded_input"] is None
    rows = captured["rows"]
    assert rows is not None
    assert rows[0]["Короткое замыкание"] == ""


def test_cli_uses_non_time_x_column_as_is_without_cumulative_transform(
    monkeypatch, tmp_path: Path
) -> None:
    module = _load_table_cli_module()
    captured: dict[str, object] = {}

    def fake_load_ndax_dataframe(_path: Path) -> pd.DataFrame:
        return _sample_dataframe()

    def fail_if_called(**_kwargs):
        raise AssertionError(
            "default_table_output_path should not be called when --output is provided"
        )

    def fake_find_six_extrema_indices(x_series, y_series, anchor_x: float):
        captured["x_series"] = x_series.tolist()
        captured["y_series"] = y_series.tolist()
        captured["anchor_x"] = anchor_x
        return _empty_extrema_indices()

    def fake_save_comparison_table(
        *, rows, anchor_x: float, output_path: Path, extrema_header_labels=None
    ) -> Path:
        captured["rows"] = list(rows)
        captured["saved_anchor_x"] = anchor_x
        captured["output_path"] = output_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("ok\n", encoding="utf-8")
        return output_path

    monkeypatch.setattr(
        module, "load_ndax_dataframe", fake_load_ndax_dataframe
    )
    monkeypatch.setattr(module, "default_table_output_path", fail_if_called)
    monkeypatch.setattr(
        module, "find_six_extrema_indices", fake_find_six_extrema_indices
    )
    monkeypatch.setattr(
        module, "save_comparison_table", fake_save_comparison_table
    )

    explicit_output = tmp_path / "custom" / "table.csv"
    exit_code = module.main([
        "--files",
        str(tmp_path / "sample.ndax"),
        "--y-column",
        "voltage",
        "--x-column",
        "current(ma)",
        "--anchor-x",
        "-110",
        "--output",
        str(explicit_output),
    ])

    assert exit_code == 0
    assert captured["x_series"] == [-100.0, -120.0, -110.0]
    assert captured["y_series"] == [3200.0, 3400.0, 3300.0]
    assert captured["anchor_x"] == -110.0
    assert captured["saved_anchor_x"] == -110.0
    assert captured["output_path"] == explicit_output
    rows = captured["rows"]
    assert rows is not None
    assert rows[0]["name"] == "sample"


def test_cli_time_falls_back_to_raw_seconds_when_timestamp_missing(
    monkeypatch, tmp_path: Path
) -> None:
    module = _load_table_cli_module()
    captured: dict[str, object] = {}

    def fake_load_ndax_dataframe(_path: Path) -> pd.DataFrame:
        return _sample_dataframe_without_timestamp()

    def fake_find_six_extrema_indices(x_series, y_series, anchor_x: float):
        captured["x_series"] = x_series.tolist()
        captured["y_series"] = y_series.tolist()
        captured["anchor_x"] = anchor_x
        return _empty_extrema_indices()

    def fake_save_comparison_table(
        *, rows, anchor_x: float, output_path: Path, extrema_header_labels=None
    ) -> Path:
        captured["rows"] = list(rows)
        captured["saved_anchor_x"] = anchor_x
        captured["output_path"] = output_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("ok\n", encoding="utf-8")
        return output_path

    monkeypatch.setattr(
        module, "load_ndax_dataframe", fake_load_ndax_dataframe
    )
    monkeypatch.setattr(
        module, "find_six_extrema_indices", fake_find_six_extrema_indices
    )
    monkeypatch.setattr(
        module, "save_comparison_table", fake_save_comparison_table
    )

    explicit_output = tmp_path / "custom" / "table.csv"
    exit_code = module.main([
        "--files",
        str(tmp_path / "sample.ndax"),
        "--y-column",
        "voltage",
        "--anchor-x",
        "4",
        "--output",
        str(explicit_output),
    ])

    assert exit_code == 0
    assert captured["x_series"] == [0.0, 4.0, 9.0]
    assert captured["y_series"] == [3200.0, 3400.0, 3300.0]
    assert captured["anchor_x"] == 4.0 * 3600
    assert captured["saved_anchor_x"] == 4.0


def test_cli_help_mentions_time_anchor_hours() -> None:
    module = _load_table_cli_module()
    help_text = module._build_parser().format_help()

    assert "value is in" in help_text
    assert "hours" in help_text


def test_cli_time_falls_back_to_raw_seconds_when_timestamp_malformed(
    monkeypatch, tmp_path: Path
) -> None:
    module = _load_table_cli_module()
    captured: dict[str, object] = {}

    def fake_load_ndax_dataframe(_path: Path) -> pd.DataFrame:
        return _sample_dataframe_with_malformed_timestamp()

    def fake_find_six_extrema_indices(x_series, y_series, anchor_x: float):
        captured["x_series"] = x_series.tolist()
        captured["y_series"] = y_series.tolist()
        captured["anchor_x"] = anchor_x
        return _empty_extrema_indices()

    def fake_save_comparison_table(
        *, rows, anchor_x: float, output_path: Path, extrema_header_labels=None
    ) -> Path:
        captured["rows"] = list(rows)
        captured["saved_anchor_x"] = anchor_x
        captured["output_path"] = output_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("ok\n", encoding="utf-8")
        return output_path

    monkeypatch.setattr(
        module, "load_ndax_dataframe", fake_load_ndax_dataframe
    )
    monkeypatch.setattr(
        module, "find_six_extrema_indices", fake_find_six_extrema_indices
    )
    monkeypatch.setattr(
        module, "save_comparison_table", fake_save_comparison_table
    )

    explicit_output = tmp_path / "custom" / "table.csv"
    exit_code = module.main([
        "--files",
        str(tmp_path / "sample.ndax"),
        "--y-column",
        "voltage",
        "--anchor-x",
        "4",
        "--output",
        str(explicit_output),
    ])

    assert exit_code == 0
    assert captured["x_series"] == [0.0, 4.0, 9.0]
    assert captured["y_series"] == [3200.0, 3400.0, 3300.0]
    assert captured["anchor_x"] == 4.0 * 3600
    assert captured["saved_anchor_x"] == 4.0
