from datetime import datetime

from table_data_extraction.config import OUTPUT_DIR
from table_data_extraction.output_paths import (
    default_plot_output_path,
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
