from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Sequence

from table_data_extraction.project_config import ROOT_DIR
from table_data_extraction.project_config import (
    load_project_config,
    reload_project_config,
    save_project_config,
)


def resolve_runtime_output_dir(config: dict[str, object]) -> Path:
    output_dir = Path(str(config["paths"]["output_dir"]))
    if output_dir.is_absolute():
        return output_dir
    return ROOT_DIR / output_dir


def parse_csv_columns(value: str) -> list[str]:
    columns = [item.strip() for item in value.split(",")]
    normalized = [item for item in columns if item]
    if not normalized:
        raise ValueError("CSV columns must not be empty.")
    return normalized


def parse_palette(values: Sequence[str]) -> list[str]:
    normalized = [value.strip() for value in values if value.strip()]
    if not normalized:
        raise ValueError("Palette must contain at least one color.")
    return normalized


def build_updated_config(
    *,
    current_config: dict[str, object] | None = None,
    output_dir: str | Path,
    palette: Sequence[str],
    plot_x_column: str,
    plot_y_column: str,
    csv_columns: str,
    window_points: str,
    zero_threshold: str,
    min_zone_points: str,
    min_extrema_separation_points: str,
) -> dict[str, object]:
    config = deepcopy(current_config or load_project_config())
    config["paths"]["output_dir"] = str(Path(output_dir))
    config["plot"]["palette"] = parse_palette(palette)
    config["plot"]["defaults"] = {
        "x_column": plot_x_column.strip(),
        "y_column": plot_y_column.strip(),
    }
    config["csv"]["defaults"] = {
        "columns": parse_csv_columns(csv_columns),
    }
    config["comparison_table"]["extrema_detection"] = {
        "window_points": int(window_points.strip()),
        "zero_threshold": float(zero_threshold.strip()),
        "min_zone_points": int(min_zone_points.strip()),
        "min_extrema_separation_points": int(
            min_extrema_separation_points.strip()
        ),
    }
    return config


def save_updated_config(config: dict[str, object]) -> dict[str, object]:
    save_project_config(config)
    return reload_project_config()
