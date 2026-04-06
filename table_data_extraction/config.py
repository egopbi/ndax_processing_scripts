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


_CONFIG = load_project_config()
_PATHS = _CONFIG["paths"]
_PLOT_DEFAULTS = _CONFIG["plot"]["defaults"]
_CSV_DEFAULTS = _CONFIG["csv"]["defaults"]
_EXTREMA_DETECTION_DEFAULTS = _CONFIG["comparison_table"]["extrema_detection"]

ROOT_DIR = PROJECT_ROOT_DIR
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
