from datetime import datetime

from table_data_extraction.config import OUTPUT_DIR
from table_data_extraction.output_paths import (
    default_plot_output_path,
    default_table_output_path,
    sanitize_name,
)


def test_sanitize_name_applies_stage_1_rules() -> None:
    assert sanitize_name("Voltage") == "voltage"
    assert sanitize_name("Charge/Discharge Capacity") == "charge_discharge_capacity"
    assert sanitize_name("Current(mA)") == "current_ma_"


def test_default_plot_output_path_uses_output_dir_and_filename_template() -> None:
    timestamp = datetime(2026, 3, 28, 12, 34, 56)

    output_path = default_plot_output_path(
        resolved_x_column="Time",
        resolved_y_column="Voltage",
        timestamp=timestamp,
    )

    assert output_path.parent == OUTPUT_DIR
    assert output_path.name == "voltage-time-2026-03-28_12-34-56.jpg"


def test_default_table_output_path_uses_output_dir_and_filename_template() -> None:
    timestamp = datetime(2026, 3, 28, 12, 34, 56)

    output_path = default_table_output_path(
        resolved_y_column="Charge/Discharge Capacity",
        anchor_x=" 10.5 s ",
        timestamp=timestamp,
    )

    assert output_path.parent == OUTPUT_DIR
    assert output_path.name == "table_charge_discharge_capacity_at_10.5_s_20260328_123456.csv"
