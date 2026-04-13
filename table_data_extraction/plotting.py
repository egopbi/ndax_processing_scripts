import os
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

MPL_CONFIG_DIR = Path(__file__).resolve().parents[1] / ".mplconfig"
MPL_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR = Path(__file__).resolve().parents[1] / ".cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(MPL_CONFIG_DIR))
os.environ.setdefault("XDG_CACHE_HOME", str(CACHE_DIR))

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd

from .columns import resolve_column_name
from .extrema import _is_local_maximum, _is_local_minimum
from .plot_dimensions import (
    DEFAULT_PLOT_OUTPUT_HEIGHT_PX,
    DEFAULT_PLOT_OUTPUT_WIDTH_PX,
    MAX_PLOT_OUTPUT_DIMENSION_PX,
    MIN_PLOT_OUTPUT_DIMENSION_PX,
    resolve_plot_output_dimensions,
)
from .preprocess import (
    trim_leading_rest_rows as trim_leading_rest_rows_stage_1,
)
from .plot_style import resolve_plot_colors
from .time_utils import (
    cumulative_time_from_timestamp_series,
    timestamps_are_usable,
)

AxisLimits = tuple[float | None, float | None] | None
STARTUP_TAIL_MIN_POINTS = 5
PLOT_OUTPUT_DPI = 150


@dataclass(frozen=True)
class PlotSeries:
    label: str
    frame: pd.DataFrame


def _ensure_required_columns(
    dataframe: pd.DataFrame, columns: Iterable[str]
) -> None:
    missing = [column for column in columns if column not in dataframe.columns]
    if missing:
        raise KeyError(f"Missing required columns: {', '.join(missing)}")


def resolve_plot_columns(
    dataframe: pd.DataFrame,
    *,
    x_column: str,
    y_column: str,
) -> tuple[str, str]:
    resolved_x_column = resolve_column_name(dataframe, x_column)
    resolved_y_column = resolve_column_name(dataframe, y_column)
    return resolved_x_column, resolved_y_column


def resolve_axis_label(column: str) -> str:
    if column == "Time":
        return "Total Time (h)"
    if column == "Voltage":
        return "Voltage (mV)"

    match = re.fullmatch(r"(.+?)\((.+)\)", column)
    if match:
        base_name = match.group(1).replace("_", " ").strip()
        unit = match.group(2).strip()
        return f"{base_name} ({unit})"

    return column.replace("_", " ").strip()


def trim_leading_rest_rows(dataframe: pd.DataFrame) -> pd.DataFrame:
    return trim_leading_rest_rows_stage_1(dataframe)


def _find_first_extremum_position(values: pd.Series) -> int | None:
    y_values = values.to_numpy(copy=False)
    for position in range(1, len(y_values) - 1):
        if _is_local_maximum(y_values, position) or _is_local_minimum(
            y_values, position
        ):
            return position
    return None


def _resolve_startup_tail_trim_points(
    dataframe: pd.DataFrame, *, y_col: str
) -> int:
    if y_col != "Voltage" or y_col not in dataframe.columns:
        return 0

    first_extremum_position = _find_first_extremum_position(dataframe[y_col])
    if (
        first_extremum_position is None
        or first_extremum_position < STARTUP_TAIL_MIN_POINTS
    ):
        return 0

    return first_extremum_position


def resolve_shared_startup_tail_trim_points(
    dataframes: Sequence[pd.DataFrame], *, y_col: str
) -> int:
    candidates = [
        _resolve_startup_tail_trim_points(
            trim_leading_rest_rows(dataframe), y_col=y_col
        )
        for dataframe in dataframes
    ]
    if not candidates:
        return 0

    counts = Counter(candidates)
    highest_frequency = max(counts.values())
    most_likely_candidates = [
        points
        for points, frequency in counts.items()
        if frequency == highest_frequency
    ]
    if len(most_likely_candidates) == 1:
        return most_likely_candidates[0]

    return max(most_likely_candidates)


def _resolve_initial_cycle_trim_points(
    dataframe: pd.DataFrame, *, startup_tail_trim_points: int
) -> int:
    if "Status" not in dataframe.columns:
        return 0

    trimmed_frame = trim_leading_rest_rows(dataframe)
    if startup_tail_trim_points >= len(trimmed_frame):
        return 0

    statuses = (
        trimmed_frame.iloc[startup_tail_trim_points:]["Status"].to_numpy(
            copy=False
        )
    )
    position = 0
    while position < len(statuses):
        if statuses[position] != "Rest":
            position += 1
            continue

        rest_block_end = position
        while (
            rest_block_end + 1 < len(statuses)
            and statuses[rest_block_end + 1] == "Rest"
        ):
            rest_block_end += 1

        if rest_block_end + 1 < len(statuses):
            return rest_block_end

        return 0

    return 0


def resolve_shared_initial_cycle_trim_points(
    dataframes: Sequence[pd.DataFrame], *, startup_tail_trim_points: int
) -> int:
    candidates = [
        _resolve_initial_cycle_trim_points(
            dataframe, startup_tail_trim_points=startup_tail_trim_points
        )
        for dataframe in dataframes
    ]
    if not candidates:
        return 0

    counts = Counter(candidates)
    highest_frequency = max(counts.values())
    most_likely_candidates = [
        points
        for points, frequency in counts.items()
        if frequency == highest_frequency
    ]
    if len(most_likely_candidates) == 1:
        return most_likely_candidates[0]

    return max(most_likely_candidates)


def _trim_leading_startup_tail(
    dataframe: pd.DataFrame,
    *,
    y_col: str,
    trim_points: int | None = None,
) -> pd.DataFrame:
    effective_trim_points = (
        _resolve_startup_tail_trim_points(dataframe, y_col=y_col)
        if trim_points is None
        else max(trim_points, 0)
    )
    if effective_trim_points == 0:
        return dataframe

    return dataframe.iloc[effective_trim_points:].copy()


def _prepare_cumulative_time_hours(
    trimmed_frame: pd.DataFrame, source_frame: pd.DataFrame
) -> pd.Series:
    cumulative_hours = cumulative_time_from_timestamp_series(
        trimmed_frame["Timestamp"], divisor=3600
    )
    return cumulative_hours.loc[source_frame.index]


def prepare_plot_frame(
    dataframe: pd.DataFrame,
    *,
    x_col: str,
    y_col: str,
    startup_tail_trim_points: int | None = None,
    initial_cycle_trim_points: int | None = None,
) -> tuple[pd.DataFrame, str, str]:
    _ensure_required_columns(dataframe, [x_col, y_col])

    trimmed_frame = _trim_leading_startup_tail(
        trim_leading_rest_rows(dataframe),
        y_col=y_col,
        trim_points=startup_tail_trim_points,
    )
    if initial_cycle_trim_points is not None and initial_cycle_trim_points > 0:
        trimmed_frame = trimmed_frame.iloc[initial_cycle_trim_points:].copy()
    has_usable_timestamps = timestamps_are_usable(trimmed_frame)
    source_frame = trimmed_frame
    if not source_frame.empty:
        source_frame = source_frame.iloc[1:].copy()
    if x_col == "Time":
        if has_usable_timestamps:
            x_values = _prepare_cumulative_time_hours(
                trimmed_frame, source_frame
            )
        else:
            x_values = source_frame[x_col] / 3600
        x_label = resolve_axis_label(x_col)
    else:
        x_values = source_frame[x_col]
        x_label = resolve_axis_label(x_col)

    y_values = source_frame[y_col]
    if y_col == "Voltage":
        y_values = y_values * 1000

    plot_frame = pd.DataFrame({
        "__plot_x__": x_values,
        "__plot_y__": y_values,
    }).dropna()

    return plot_frame, x_label, resolve_axis_label(y_col)


def _normalize_limits(limits: AxisLimits) -> AxisLimits:
    if limits is None:
        return None

    lower, upper = limits
    if lower is not None and upper is not None and lower > upper:
        return (upper, lower)
    return limits


def _apply_limits(
    plot_frame: pd.DataFrame, x_limits: AxisLimits, y_limits: AxisLimits
) -> pd.DataFrame:
    limited_frame = plot_frame

    if x_limits is not None:
        x_lower, x_upper = x_limits
        if x_lower is not None:
            limited_frame = limited_frame.loc[
                limited_frame["__plot_x__"] >= x_lower
            ]
        if x_upper is not None:
            limited_frame = limited_frame.loc[
                limited_frame["__plot_x__"] <= x_upper
            ]

    if y_limits is not None:
        y_lower, y_upper = y_limits
        if y_lower is not None:
            limited_frame = limited_frame.loc[
                limited_frame["__plot_y__"] >= y_lower
            ]
        if y_upper is not None:
            limited_frame = limited_frame.loc[
                limited_frame["__plot_y__"] <= y_upper
            ]

    return limited_frame


def _set_axis_limits(axis, x_limits: AxisLimits, y_limits: AxisLimits) -> None:
    if x_limits is not None:
        x_lower, x_upper = x_limits
        axis.set_xlim(left=x_lower, right=x_upper)
    if y_limits is not None:
        y_lower, y_upper = y_limits
        axis.set_ylim(bottom=y_lower, top=y_upper)


def save_multi_series_plot(
    series: Sequence[PlotSeries],
    *,
    x_label: str,
    y_label: str,
    output_path: Path,
    x_limits: AxisLimits,
    y_limits: AxisLimits,
    output_width_px: int | None = None,
    output_height_px: int | None = None,
) -> Path:
    all_series = list(series)
    if not all_series:
        raise ValueError("No rows are available for plotting after filtering.")

    normalized_x_limits = _normalize_limits(x_limits)
    normalized_y_limits = _normalize_limits(y_limits)
    palette = resolve_plot_colors(len(all_series))
    resolved_width_px, resolved_height_px = resolve_plot_output_dimensions(
        output_width_px=output_width_px,
        output_height_px=output_height_px,
    )

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    figure, axis = plt.subplots(
        figsize=(
            resolved_width_px / PLOT_OUTPUT_DPI,
            resolved_height_px / PLOT_OUTPUT_DPI,
        )
    )
    plotted_series_count = 0
    for index, line in enumerate(all_series):
        limited_frame = _apply_limits(
            line.frame, normalized_x_limits, normalized_y_limits
        )
        if limited_frame.empty:
            continue

        axis.plot(
            limited_frame["__plot_x__"],
            limited_frame["__plot_y__"],
            label=line.label,
            linewidth=1.4,
            color=palette[index],
        )
        plotted_series_count += 1

    if plotted_series_count == 0:
        plt.close(figure)
        raise ValueError("No rows are available for plotting after filtering.")

    axis.set_xlabel(x_label)
    axis.set_ylabel(y_label)
    axis.legend(loc="upper right")
    _set_axis_limits(axis, normalized_x_limits, normalized_y_limits)
    axis.grid(True, which="major", alpha=0.3, linewidth=0.6)

    figure.tight_layout()
    figure.savefig(output_file, format="jpg", dpi=PLOT_OUTPUT_DPI)
    plt.close(figure)
    return output_file


def save_plot(
    dataframe: pd.DataFrame,
    *,
    x_col: str,
    y_col: str,
    output_path: Path,
    series_label: str,
    x_limits: AxisLimits,
    y_limits: AxisLimits,
    output_width_px: int | None = None,
    output_height_px: int | None = None,
) -> Path:
    plot_frame, x_label, y_label = prepare_plot_frame(
        dataframe,
        x_col=x_col,
        y_col=y_col,
    )
    return save_multi_series_plot(
        [PlotSeries(label=series_label, frame=plot_frame)],
        x_label=x_label,
        y_label=y_label,
        output_path=output_path,
        x_limits=x_limits,
        y_limits=y_limits,
        output_width_px=output_width_px,
        output_height_px=output_height_px,
    )
