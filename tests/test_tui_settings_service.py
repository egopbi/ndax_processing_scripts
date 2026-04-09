from pathlib import Path

import pytest

from table_data_extraction.project_config import ROOT_DIR
from table_data_extraction.tui.settings_service import (
    build_updated_config,
    parse_csv_columns,
    parse_palette,
    resolve_runtime_output_dir,
)


def test_resolve_runtime_output_dir_resolves_relative_paths() -> None:
    config = {
        "paths": {"output_dir": "output"},
    }

    resolved = resolve_runtime_output_dir(config)

    assert resolved == ROOT_DIR / "output"


def test_build_updated_config_updates_expected_sections() -> None:
    config = build_updated_config(
        output_dir=Path("/tmp/ndax-out"),
        palette=("#111111", "#222222"),
        plot_x_column="Time",
        plot_y_column="Voltage",
        csv_columns="Time, Voltage, Current(mA)",
        window_points="9",
        zero_threshold="5.0",
        min_zone_points="5",
        min_extrema_separation_points="7",
    )

    assert config["paths"]["output_dir"] == "/tmp/ndax-out"
    assert config["plot"]["palette"] == ["#111111", "#222222"]
    assert config["csv"]["defaults"]["columns"] == [
        "Time",
        "Voltage",
        "Current(mA)",
    ]
    assert config["comparison_table"]["extrema_detection"] == {
        "window_points": 9,
        "zero_threshold": 5.0,
        "min_zone_points": 5,
        "min_extrema_separation_points": 7,
    }


def test_parse_csv_columns_rejects_empty_values() -> None:
    with pytest.raises(ValueError):
        parse_csv_columns(" , ")


def test_parse_palette_rejects_empty_values() -> None:
    with pytest.raises(ValueError):
        parse_palette(["", " "])
