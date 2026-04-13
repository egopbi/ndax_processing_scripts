from __future__ import annotations

from pathlib import Path
import sys
from typing import Iterable, Sequence

from table_data_extraction.output_paths import (
    default_plot_output_path,
    default_table_output_path,
)

from .models import (
    ConvertRunConfig,
    HealthCheckRunConfig,
    PlotRunConfig,
    SubprocessCommand,
    TableRunConfig,
)

ROOT_DIR = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = ROOT_DIR / "scripts"
PLOT_SCRIPT = Path("scripts/plot_ndax.py")
TABLE_SCRIPT = Path("scripts/build_comparison_table.py")
CONVERT_SCRIPT = Path("scripts/convert_ndax.py")
HEALTH_SCRIPT = Path("scripts/health_check_ndax.py")


def _normalize_paths(paths: Sequence[Path]) -> tuple[Path, ...]:
    normalized = tuple(Path(path) for path in paths)
    if not normalized:
        raise ValueError("At least one NDAX file is required.")
    return normalized


def _normalize_labels(
    files: Sequence[Path], labels: Sequence[str] | None
) -> tuple[str, ...] | None:
    if labels is None:
        return None

    normalized = tuple(str(label) for label in labels)
    if len(normalized) != len(files):
        raise ValueError("Number of labels must match number of files.")
    return normalized


def _normalize_anchor_x(anchor_x: Sequence[float]) -> tuple[float, ...]:
    normalized = tuple(float(value) for value in anchor_x)
    if not normalized:
        raise ValueError("At least one anchor-x value is required.")
    return normalized


def _python_executable(python_executable: str | Path | None) -> str:
    return str(python_executable or sys.executable)


def _python_argv(python_executable: str | Path | None) -> list[str]:
    return [_python_executable(python_executable), "-u"]


def _append_values(argv: list[str], flag: str, values: Iterable[object]) -> None:
    argv.append(flag)
    argv.extend(str(value) for value in values)


def _normalize_columns(columns: Sequence[str]) -> tuple[str, ...]:
    unique_columns: list[str] = []
    seen: set[str] = set()
    for value in columns:
        column = str(value).strip()
        if not column or column in seen:
            continue
        seen.add(column)
        unique_columns.append(column)

    normalized = tuple(unique_columns)
    if not normalized:
        raise ValueError("At least one column is required.")
    return normalized


def build_plot_command(
    config: PlotRunConfig,
    *,
    output_dir: str | Path | None = None,
    python_executable: str | Path | None = None,
) -> SubprocessCommand:
    files = _normalize_paths(config.files)
    labels = _normalize_labels(files, config.labels)
    output_path = config.output_path
    if config.separate:
        output_path = None
    elif output_path is None and output_dir is not None:
        output_path = default_plot_output_path(
            source_paths=files,
            resolved_x_column=config.x_column,
            resolved_y_column=config.y_column,
            output_dir=output_dir,
        )

    argv = [
        *_python_argv(python_executable),
        str(PLOT_SCRIPT),
    ]
    _append_values(argv, "--files", files)
    argv.extend(["--y-column", config.y_column])
    argv.extend(["--x-column", config.x_column])

    if labels is not None:
        _append_values(argv, "--labels", labels)
    if config.x_min is not None:
        argv.extend(["--x-min", str(config.x_min)])
    if config.x_max is not None:
        argv.extend(["--x-max", str(config.x_max)])
    if config.y_min is not None:
        argv.extend(["--y-min", str(config.y_min)])
    if config.y_max is not None:
        argv.extend(["--y-max", str(config.y_max)])
    if config.separate:
        argv.append("--separate")
    if output_path is not None:
        argv.extend(["--output", str(output_path)])

    return SubprocessCommand(
        mode="plot",
        argv=tuple(argv),
        cwd=ROOT_DIR,
        output_path=Path(output_path) if output_path is not None else None,
    )


def build_table_command(
    config: TableRunConfig,
    *,
    output_dir: str | Path | None = None,
    python_executable: str | Path | None = None,
) -> SubprocessCommand:
    files = _normalize_paths(config.files)
    labels = _normalize_labels(files, config.labels)
    anchors = _normalize_anchor_x(config.anchor_x)
    output_path = config.output_path
    if output_path is None and output_dir is not None:
        output_path = default_table_output_path(
            source_paths=files,
            resolved_y_column=config.y_column,
            output_dir=output_dir,
        )

    argv = [
        *_python_argv(python_executable),
        str(TABLE_SCRIPT),
    ]
    _append_values(argv, "--files", files)
    argv.extend(["--y-column", config.y_column])
    _append_values(argv, "--anchor-x", anchors)
    argv.extend(["--x-column", config.x_column])

    if labels is not None:
        _append_values(argv, "--labels", labels)
    if output_path is not None:
        argv.extend(["--output", str(output_path)])

    return SubprocessCommand(
        mode="table",
        argv=tuple(argv),
        cwd=ROOT_DIR,
        output_path=Path(output_path) if output_path is not None else None,
    )


def build_health_check_command(
    config: HealthCheckRunConfig,
    *,
    python_executable: str | Path | None = None,
) -> SubprocessCommand:
    argv = [
        *_python_argv(python_executable),
        str(HEALTH_SCRIPT),
        str(Path(config.file)),
    ]
    return SubprocessCommand(
        mode="health-check",
        argv=tuple(argv),
        cwd=ROOT_DIR,
    )


def build_convert_command(
    config: ConvertRunConfig,
    *,
    output_dir: str | Path | None = None,
    python_executable: str | Path | None = None,
) -> SubprocessCommand:
    files = _normalize_paths(config.files)
    columns = _normalize_columns(config.columns)

    argv = [
        *_python_argv(python_executable),
        str(CONVERT_SCRIPT),
    ]
    _append_values(argv, "--files", files)
    _append_values(argv, "--columns", columns)

    if output_dir is not None:
        argv.extend(["--output-dir", str(Path(output_dir))])

    return SubprocessCommand(
        mode="convert",
        argv=tuple(argv),
        cwd=ROOT_DIR,
    )
