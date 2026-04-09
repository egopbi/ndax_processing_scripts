import re
from datetime import datetime
from pathlib import Path
from typing import Sequence

from .config import get_output_dir


def sanitize_name(value: str) -> str:
    normalized = str(value).strip().casefold().replace(" ", "_")
    return re.sub(r"[^a-z0-9._-]", "_", normalized)


def _quantity_slug(resolved_y_column: str) -> str:
    base_name = re.sub(r"\s*[\(\[].*?[\)\]]\s*$", "", resolved_y_column).strip()
    return sanitize_name(base_name or resolved_y_column)


def _table_timestamp_suffix(timestamp: datetime | None) -> str:
    point_in_time = timestamp or datetime.now()
    return point_in_time.strftime("%Y-%m-%d_%H-%M-%S")


def _plot_timestamp_suffix(timestamp: datetime | None) -> str:
    point_in_time = timestamp or datetime.now()
    return point_in_time.strftime("%Y-%m-%d_%H-%M-%S")


def sample_name_from_path(source_path: str | Path) -> str:
    return sanitize_name(Path(source_path).stem.split("_")[0])


def _instance_suffix(source_paths: Sequence[str | Path]) -> str:
    parts = [sample_name_from_path(source_path) for source_path in source_paths]
    return "_".join(part for part in parts if part)


def _resolve_output_dir(output_dir: str | Path | None) -> Path:
    return Path(output_dir) if output_dir is not None else get_output_dir()


def default_plot_output_path(
    *,
    source_paths: Sequence[str | Path],
    resolved_x_column: str,
    resolved_y_column: str,
    timestamp: datetime | None = None,
    output_dir: str | Path | None = None,
) -> Path:
    resolved_output_dir = _resolve_output_dir(output_dir)
    resolved_output_dir.mkdir(parents=True, exist_ok=True)
    instance_suffix = _instance_suffix(source_paths)
    filename = (
        f"{sanitize_name(resolved_y_column)}-"
        f"{sanitize_name(resolved_x_column)}-"
        f"{_plot_timestamp_suffix(timestamp)}"
        f"{f'_{instance_suffix}' if instance_suffix else ''}.jpg"
    )
    return resolved_output_dir / filename


def default_table_output_path(
    *,
    source_paths: Sequence[str | Path],
    resolved_y_column: str,
    timestamp: datetime | None = None,
    output_dir: str | Path | None = None,
) -> Path:
    resolved_output_dir = _resolve_output_dir(output_dir)
    resolved_output_dir.mkdir(parents=True, exist_ok=True)
    instance_suffix = _instance_suffix(source_paths)
    filename = (
        f"table_{_quantity_slug(resolved_y_column)}_"
        f"{_table_timestamp_suffix(timestamp)}"
        f"{f'_{instance_suffix}' if instance_suffix else ''}.csv"
    )
    return resolved_output_dir / filename
