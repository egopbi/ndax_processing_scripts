import importlib.util
from pathlib import Path

import pandas as pd
import pytest

from table_data_extraction.health import HealthCheckResult


ROOT_DIR = Path(__file__).resolve().parents[1]
PLOT_SCRIPT_PATH = ROOT_DIR / "scripts" / "generate_plot_poc.py"
CSV_SCRIPT_PATH = ROOT_DIR / "scripts" / "generate_csv_poc.py"
HEALTH_SCRIPT_PATH = ROOT_DIR / "scripts" / "health_check_ndax.py"


def _load_module(script_path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    assert spec is not None
    assert spec.loader is not None

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sample_dataframe() -> pd.DataFrame:
    return pd.DataFrame({
        "Status": ["Rest", "CC_DChg"],
        "Time": [0.0, 4.0],
        "Voltage": [2.9, 3.4],
        "Current(mA)": [0.0, -100.0],
    })


@pytest.mark.parametrize(
    ("script_path", "module_name"),
    [
        (PLOT_SCRIPT_PATH, "generate_plot_poc_cli"),
        (CSV_SCRIPT_PATH, "generate_csv_poc_cli"),
        (HEALTH_SCRIPT_PATH, "health_check_ndax_cli"),
    ],
)
def test_poc_scripts_require_an_explicit_ndax_path(
    script_path: Path, module_name: str
):
    module = _load_module(script_path, module_name)

    with pytest.raises(SystemExit) as exc_info:
        module.main([])

    assert exc_info.value.code == 2


def test_generate_plot_poc_succeeds_with_explicit_path(
    monkeypatch, tmp_path: Path, capsys
):
    module = _load_module(PLOT_SCRIPT_PATH, "generate_plot_poc_cli_success")
    captured: dict[str, object] = {}

    def fake_load_ndax_dataframe(path: Path) -> pd.DataFrame:
        captured["path"] = path
        return _sample_dataframe()

    def fake_save_plot(
        dataframe: pd.DataFrame,
        *,
        x_col: str,
        y_col: str,
        output_path: Path,
        series_label: str,
        x_limits,
        y_limits,
    ) -> Path:
        captured["x_col"] = x_col
        captured["y_col"] = y_col
        captured["output_path"] = output_path
        captured["series_label"] = series_label
        captured["x_limits"] = x_limits
        captured["y_limits"] = y_limits
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"plot")
        return output_path

    monkeypatch.setattr(
        module, "load_ndax_dataframe", fake_load_ndax_dataframe
    )
    monkeypatch.setattr(module, "save_plot", fake_save_plot)

    explicit_path = tmp_path / "sample.ndax"
    exit_code = module.main([str(explicit_path)])

    assert exit_code == 0
    assert captured["path"] == explicit_path
    assert captured["series_label"] == "sample"
    assert captured["x_col"] == "Time"
    assert captured["y_col"] == "Voltage"
    assert captured["output_path"].name == "poc_plot.jpg"
    assert captured["x_limits"] is None
    assert captured["y_limits"] is None
    assert "Saved demo plot to" in capsys.readouterr().out


def test_generate_csv_poc_succeeds_with_explicit_path(
    monkeypatch, tmp_path: Path, capsys
):
    module = _load_module(CSV_SCRIPT_PATH, "generate_csv_poc_cli_success")
    captured: dict[str, object] = {}

    def fake_load_ndax_dataframe(path: Path) -> pd.DataFrame:
        captured["path"] = path
        return _sample_dataframe()

    def fake_save_csv_slice(
        dataframe: pd.DataFrame,
        *,
        columns,
        output_path: Path,
    ) -> Path:
        captured["columns"] = list(columns)
        captured["output_path"] = output_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("csv", encoding="utf-8")
        return output_path

    monkeypatch.setattr(
        module, "load_ndax_dataframe", fake_load_ndax_dataframe
    )
    monkeypatch.setattr(module, "save_csv_slice", fake_save_csv_slice)

    explicit_path = tmp_path / "sample.ndax"
    exit_code = module.main([str(explicit_path)])

    assert exit_code == 0
    assert captured["path"] == explicit_path
    assert captured["columns"] == ["Time", "Voltage", "Current(mA)"]
    assert captured["output_path"].name == "poc_table.csv"
    output = capsys.readouterr()
    assert "Saved demo CSV to" in output.out
    assert "Skipped missing columns" in output.out


def test_health_check_ndax_succeeds_with_explicit_path(
    monkeypatch, tmp_path: Path, capsys
):
    module = _load_module(HEALTH_SCRIPT_PATH, "health_check_ndax_cli_success")
    captured: dict[str, object] = {}

    def fake_run_health_check(
        path: Path, required_columns
    ) -> HealthCheckResult:
        captured["path"] = path
        captured["required_columns"] = list(required_columns)
        return HealthCheckResult(
            path=path,
            row_count=2,
            columns=["Time", "Voltage", "Current(mA)"],
            required_columns=list(required_columns),
            missing_columns=[],
        )

    def fake_format_health_check_report(
        result, *, plot_columns, csv_columns
    ) -> str:
        captured["plot_columns"] = list(plot_columns)
        captured["csv_columns"] = list(csv_columns)
        return "ok"

    monkeypatch.setattr(module, "run_health_check", fake_run_health_check)
    monkeypatch.setattr(
        module, "format_health_check_report", fake_format_health_check_report
    )

    explicit_path = tmp_path / "sample.ndax"
    exit_code = module.main([str(explicit_path)])

    assert exit_code == 0
    assert captured["path"] == explicit_path
    assert captured["required_columns"] == [
        "Time",
        "Voltage",
        "Time",
        "Voltage",
        "Current(mA)",
        "Charge_Capacity(mAh)",
        "Discharge_Capacity(mAh)",
    ]
    assert captured["plot_columns"] == ["Time", "Voltage"]
    assert captured["csv_columns"] == [
        "Time",
        "Voltage",
        "Current(mA)",
        "Charge_Capacity(mAh)",
        "Discharge_Capacity(mAh)",
    ]
    assert "ok" in capsys.readouterr().out
