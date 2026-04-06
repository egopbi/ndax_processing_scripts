import importlib.util
from pathlib import Path

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


def test_poc_scripts_are_removed_from_repo() -> None:
    assert not PLOT_SCRIPT_PATH.exists()
    assert not CSV_SCRIPT_PATH.exists()


def test_health_check_ndax_requires_an_explicit_ndax_path() -> None:
    module = _load_module(HEALTH_SCRIPT_PATH, "health_check_ndax_cli")

    with pytest.raises(SystemExit) as exc_info:
        module.main([])

    assert exc_info.value.code == 2


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
