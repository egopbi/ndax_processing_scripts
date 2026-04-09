from pathlib import Path
from typing import Any

from .project_config import ROOT_DIR as PROJECT_ROOT_DIR
from .project_config import load_project_config


class _ReadOnlyList(list):
    def _blocked_mutation(self, *args: object, **kwargs: object) -> None:
        raise TypeError("This configuration list is read-only.")

    __delitem__ = _blocked_mutation
    __iadd__ = _blocked_mutation
    __imul__ = _blocked_mutation
    __setitem__ = _blocked_mutation
    append = _blocked_mutation
    clear = _blocked_mutation
    extend = _blocked_mutation
    insert = _blocked_mutation
    pop = _blocked_mutation
    remove = _blocked_mutation
    reverse = _blocked_mutation
    sort = _blocked_mutation


def _apply_runtime_config(config: dict[str, Any]) -> None:
    global _CONFIG, _PATHS, _PLOT_DEFAULTS, _CSV_DEFAULTS
    global _EXTREMA_DETECTION_DEFAULTS, OUTPUT_DIR
    global PLOT_X_COLUMN, PLOT_Y_COLUMN, CSV_COLUMNS
    global EXTREMA_WINDOW_POINTS, EXTREMA_ZERO_THRESHOLD
    global MIN_ZONE_POINTS, MIN_EXTREMA_SEPARATION_POINTS

    _CONFIG = config
    _PATHS = _CONFIG["paths"]
    _PLOT_DEFAULTS = _CONFIG["plot"]["defaults"]
    _CSV_DEFAULTS = _CONFIG["csv"]["defaults"]
    _EXTREMA_DETECTION_DEFAULTS = _CONFIG["comparison_table"][
        "extrema_detection"
    ]

    OUTPUT_DIR = ROOT_DIR / _PATHS["output_dir"]

    PLOT_X_COLUMN = _PLOT_DEFAULTS["x_column"]
    PLOT_Y_COLUMN = _PLOT_DEFAULTS["y_column"]
    CSV_COLUMNS = _ReadOnlyList(_CSV_DEFAULTS["columns"])

    EXTREMA_WINDOW_POINTS = _EXTREMA_DETECTION_DEFAULTS["window_points"]
    EXTREMA_ZERO_THRESHOLD = _EXTREMA_DETECTION_DEFAULTS["zero_threshold"]
    MIN_ZONE_POINTS = _EXTREMA_DETECTION_DEFAULTS["min_zone_points"]
    MIN_EXTREMA_SEPARATION_POINTS = _EXTREMA_DETECTION_DEFAULTS[
        "min_extrema_separation_points"
    ]


_CONFIG: dict[str, Any]
_PATHS: dict[str, Any]
_PLOT_DEFAULTS: dict[str, Any]
_CSV_DEFAULTS: dict[str, Any]
_EXTREMA_DETECTION_DEFAULTS: dict[str, Any]
ROOT_DIR = PROJECT_ROOT_DIR
OUTPUT_DIR: Path
PLOT_X_COLUMN: str
PLOT_Y_COLUMN: str
CSV_COLUMNS: _ReadOnlyList
EXTREMA_WINDOW_POINTS: int
EXTREMA_ZERO_THRESHOLD: float
MIN_ZONE_POINTS: int
MIN_EXTREMA_SEPARATION_POINTS: int

_apply_runtime_config(load_project_config())


def refresh_runtime_config(
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    refreshed = config if config is not None else load_project_config()
    _apply_runtime_config(refreshed)
    return refreshed


def get_output_dir() -> Path:
    return OUTPUT_DIR
