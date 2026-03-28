import os
import re
from pathlib import Path
from typing import Iterable

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

from .config import AXIS_LABEL_OVERRIDES


def _ensure_required_columns(dataframe: pd.DataFrame, columns: Iterable[str]) -> None:
    missing = [column for column in columns if column not in dataframe.columns]
    if missing:
        raise KeyError(f"Missing required columns: {', '.join(missing)}")


def resolve_axis_label(column: str) -> str:
    if column in AXIS_LABEL_OVERRIDES:
        return AXIS_LABEL_OVERRIDES[column]

    match = re.fullmatch(r"(.+?)\((.+)\)", column)
    if match:
        base_name = match.group(1).replace("_", " ").strip()
        unit = match.group(2).strip()
        return f"{base_name} ({unit})"

    return column.replace("_", " ")


def trim_leading_rest_rows(dataframe: pd.DataFrame) -> pd.DataFrame:
    if "Status" not in dataframe.columns:
        return dataframe.copy()

    non_rest_mask = dataframe["Status"].ne("Rest")
    if not non_rest_mask.any():
        return dataframe.copy()

    first_non_rest_index = non_rest_mask.idxmax()
    return dataframe.loc[first_non_rest_index:].copy()


def prepare_plot_frame(
    dataframe: pd.DataFrame,
    *,
    x_col: str,
    y_col: str,
) -> tuple[pd.DataFrame, str, str]:
    _ensure_required_columns(dataframe, [x_col, y_col])

    source_frame = trim_leading_rest_rows(dataframe)

    x_values = source_frame[x_col]
    x_label = resolve_axis_label(x_col)

    # Neware NDAX stores Time as per-step elapsed time, so use Timestamp to
    # build a continuous experiment timeline for plotting.
    if x_col == "Time" and "Timestamp" in source_frame.columns:
        timestamps = pd.to_datetime(source_frame["Timestamp"], errors="coerce")
        if timestamps.notna().all():
            x_values = (timestamps - timestamps.iloc[0]).dt.total_seconds()
            x_label = "Cumulative Time (s)"

    plot_frame = pd.DataFrame(
        {
            "__plot_x__": x_values,
            "__plot_y__": source_frame[y_col],
        }
    ).dropna()

    return plot_frame, x_label, resolve_axis_label(y_col)


def save_plot(
    dataframe: pd.DataFrame,
    *,
    x_col: str,
    y_col: str,
    output_path: Path,
    series_label: str,
    x_limits: tuple[float, float] | None,
    y_limits: tuple[float, float] | None,
) -> Path:
    plot_frame, x_label, y_label = prepare_plot_frame(
        dataframe,
        x_col=x_col,
        y_col=y_col,
    )
    if x_limits is not None:
        lower, upper = sorted(x_limits)
        plot_frame = plot_frame.loc[plot_frame["__plot_x__"].between(lower, upper)]
    if y_limits is not None:
        lower, upper = sorted(y_limits)
        plot_frame = plot_frame.loc[plot_frame["__plot_y__"].between(lower, upper)]

    if plot_frame.empty:
        raise ValueError("No rows are available for plotting after filtering.")

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    figure, axis = plt.subplots(figsize=(10, 6))
    axis.plot(
        plot_frame["__plot_x__"],
        plot_frame["__plot_y__"],
        label=series_label,
        linewidth=1.4,
    )
    axis.set_xlabel(x_label)
    axis.set_ylabel(y_label)
    axis.legend(loc="upper right")
    axis.grid(True, alpha=0.3)

    if x_limits is not None:
        axis.set_xlim(*sorted(x_limits))
    if y_limits is not None:
        axis.set_ylim(*sorted(y_limits))

    figure.tight_layout()
    figure.savefig(output_file, format="jpg", dpi=150)
    plt.close(figure)
    return output_file
