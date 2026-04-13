from datetime import datetime
from pathlib import Path

import pytest

from table_data_extraction import config as config_module
from table_data_extraction import project_config as project_config_module
from table_data_extraction.config import OUTPUT_DIR
from table_data_extraction.output_paths import (
    default_convert_output_path,
    default_plot_output_path,
    default_separate_plot_output_path,
    default_table_output_path,
    sanitize_name,
)


def test_sanitize_name_applies_stage_1_rules() -> None:
    assert sanitize_name("Voltage") == "voltage"
    assert (
        sanitize_name("Charge/Discharge Capacity")
        == "charge_discharge_capacity"
    )
    assert sanitize_name("Current(mA)") == "current_ma_"


def test_default_plot_output_path_uses_output_dir_and_filename_template() -> (
    None
):
    timestamp = datetime(2026, 3, 28, 12, 34, 56)

    output_path = default_plot_output_path(
        source_paths=["examples/example4_4.ndax"],
        resolved_x_column="Time",
        resolved_y_column="Voltage",
        timestamp=timestamp,
    )

    assert output_path.parent == OUTPUT_DIR
    assert output_path.name == "voltage-time-2026-03-28_12-34-56_example4.jpg"


def test_default_table_output_path_uses_output_dir_and_filename_template() -> (
    None
):
    timestamp = datetime(2026, 3, 29, 16, 7, 22)

    output_path = default_table_output_path(
        source_paths=["examples/example4_4.ndax"],
        resolved_y_column="Voltage",
        timestamp=timestamp,
    )

    assert output_path.parent == OUTPUT_DIR
    assert output_path.name == "table_voltage_2026-03-29_16-07-22_example4.csv"


def test_default_table_output_path_strips_units_from_quantity_name() -> None:
    timestamp = datetime(2026, 3, 29, 16, 7, 22)

    output_path = default_table_output_path(
        source_paths=["examples/example4_4.ndax"],
        resolved_y_column="Current(mA)",
        timestamp=timestamp,
    )

    assert output_path.name == "table_current_2026-03-29_16-07-22_example4.csv"


def test_default_table_output_path_normalizes_snake_case_quantity_name() -> (
    None
):
    timestamp = datetime(2026, 3, 29, 16, 7, 22)

    output_path = default_table_output_path(
        source_paths=["examples/example4_4.ndax"],
        resolved_y_column="Charge_Capacity(mAh)",
        timestamp=timestamp,
    )

    assert (
        output_path.name
        == "table_charge_capacity_2026-03-29_16-07-22_example4.csv"
    )


def test_default_plot_output_path_joins_multiple_instance_prefixes() -> None:
    timestamp = datetime(2026, 3, 28, 12, 34, 56)

    output_path = default_plot_output_path(
        source_paths=["examples/example1_1.ndax", "examples/example2_2.ndax"],
        resolved_x_column="Time",
        resolved_y_column="Voltage",
        timestamp=timestamp,
    )

    assert (
        output_path.name
        == "voltage-time-2026-03-28_12-34-56_example1_example2.jpg"
    )


def test_default_plot_output_path_supports_overridden_output_dir(
    tmp_path: Path,
) -> None:
    timestamp = datetime(2026, 3, 28, 12, 34, 56)
    override_dir = tmp_path / "session-output"

    output_path = default_plot_output_path(
        source_paths=["examples/example1_1.ndax"],
        resolved_x_column="Time",
        resolved_y_column="Voltage",
        timestamp=timestamp,
        output_dir=override_dir,
    )

    assert output_path.parent == override_dir
    assert output_path.name == "voltage-time-2026-03-28_12-34-56_example1.jpg"


def test_default_separate_plot_output_path_uses_source_stem() -> None:
    output_path = default_separate_plot_output_path(
        source_path="examples/example4_4.ndax"
    )

    assert output_path.parent == OUTPUT_DIR
    assert output_path.name == "example4_4.jpg"


def test_default_separate_plot_output_path_supports_overridden_output_dir(
    tmp_path: Path,
) -> None:
    override_dir = tmp_path / "session-output"

    output_path = default_separate_plot_output_path(
        source_path="examples/example4_4.ndax",
        output_dir=override_dir,
    )

    assert output_path.parent == override_dir
    assert output_path.name == "example4_4.jpg"


def test_default_table_output_path_joins_multiple_instance_prefixes() -> None:
    timestamp = datetime(2026, 3, 29, 16, 7, 22)

    output_path = default_table_output_path(
        source_paths=["examples/example1_1.ndax", "examples/example2_2.ndax"],
        resolved_y_column="Voltage",
        timestamp=timestamp,
    )

    assert (
        output_path.name
        == "table_voltage_2026-03-29_16-07-22_example1_example2.csv"
    )


def test_default_table_output_path_supports_overridden_output_dir(
    tmp_path: Path,
) -> None:
    timestamp = datetime(2026, 3, 29, 16, 7, 22)
    override_dir = tmp_path / "session-output"

    output_path = default_table_output_path(
        source_paths=["examples/example4_4.ndax"],
        resolved_y_column="Voltage",
        timestamp=timestamp,
        output_dir=override_dir,
    )

    assert output_path.parent == override_dir
    assert output_path.name == "table_voltage_2026-03-29_16-07-22_example4.csv"


def test_default_convert_output_path_uses_source_stem_in_default_output_dir() -> (
    None
):
    output_path = default_convert_output_path(
        source_path="examples/example4_4.ndax"
    )

    assert output_path.parent == OUTPUT_DIR
    assert output_path.name == "example4_4.csv"


def test_default_convert_output_path_supports_overridden_output_dir(
    tmp_path: Path,
) -> None:
    override_dir = tmp_path / "session-output"

    output_path = default_convert_output_path(
        source_path="examples/example4_4.ndax",
        output_dir=override_dir,
    )

    assert output_path.parent == override_dir
    assert output_path.name == "example4_4.csv"


def test_default_output_paths_use_refreshed_runtime_output_dir(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from table_data_extraction import output_paths as output_paths_module

    config_path = tmp_path / "project_config.yaml"
    config = {
        "paths": {"output_dir": "first-output"},
        "plot": {
            "palette": ["#111111", "#222222", "#333333"],
            "defaults": {
                "x_column": "Time",
                "y_column": "Voltage",
            },
        },
        "csv": {
            "defaults": {
                "columns": [
                    "Time",
                    "Voltage",
                    "Current(mA)",
                ],
            },
        },
        "comparison_table": {
            "extrema_detection": {
                "window_points": 9,
                "zero_threshold": 5.0,
                "min_zone_points": 5,
                "min_extrema_separation_points": 5,
            },
        },
    }
    config_path.write_text(
        """
paths:
  output_dir: first-output
plot:
  palette:
    - "#111111"
    - "#222222"
    - "#333333"
  defaults:
    x_column: Time
    y_column: Voltage
csv:
  defaults:
    columns:
      - Time
      - Voltage
      - Current(mA)
comparison_table:
  extrema_detection:
    window_points: 9
    zero_threshold: 5.0
    min_zone_points: 5
    min_extrema_separation_points: 5
""".strip()
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(project_config_module, "CONFIG_PATH", config_path)
    project_config_module.load_project_config.cache_clear()
    try:
        project_config_module.reload_project_config()

        assert config_module.OUTPUT_DIR == config_module.ROOT_DIR / "first-output"
        first_output = output_paths_module.default_plot_output_path(
            source_paths=["examples/example1_1.ndax"],
            resolved_x_column="Time",
            resolved_y_column="Voltage",
            timestamp=datetime(2026, 3, 28, 12, 34, 56),
        )
        assert first_output.parent == config_module.OUTPUT_DIR

        config["paths"]["output_dir"] = "second-output"
        config["plot"]["palette"] = ["#aaaaaa", "#bbbbbb", "#cccccc"]
        config_path.write_text(
            """
paths:
  output_dir: second-output
plot:
  palette:
    - "#aaaaaa"
    - "#bbbbbb"
    - "#cccccc"
  defaults:
    x_column: Time
    y_column: Voltage
csv:
  defaults:
    columns:
      - Time
      - Voltage
      - Current(mA)
comparison_table:
  extrema_detection:
    window_points: 9
    zero_threshold: 5.0
    min_zone_points: 5
    min_extrema_separation_points: 5
""".strip()
            + "\n",
            encoding="utf-8",
        )

        refreshed = project_config_module.reload_project_config()

        assert refreshed["paths"]["output_dir"] == "second-output"
        assert config_module.OUTPUT_DIR == config_module.ROOT_DIR / "second-output"
        assert config_module.PLOT_X_COLUMN == "Time"
        assert config_module.PLOT_Y_COLUMN == "Voltage"
        assert output_paths_module.default_table_output_path(
            source_paths=["examples/example1_1.ndax"],
            resolved_y_column="Voltage",
            timestamp=datetime(2026, 3, 29, 16, 7, 22),
        ).parent == config_module.OUTPUT_DIR
    finally:
        project_config_module.CONFIG_PATH = (
            Path(__file__).resolve().parents[1] / "project_config.yaml"
        )
        project_config_module.load_project_config.cache_clear()
        project_config_module.reload_project_config()
