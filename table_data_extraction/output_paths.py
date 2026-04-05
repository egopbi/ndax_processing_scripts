import re
from datetime import datetime
from pathlib import Path

from .config import OUTPUT_DIR


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


def default_plot_output_path(
    *,
    resolved_x_column: str,
    resolved_y_column: str,
    timestamp: datetime | None = None,
) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{sanitize_name(resolved_y_column)}-{sanitize_name(resolved_x_column)}-{_plot_timestamp_suffix(timestamp)}.jpg"
    return OUTPUT_DIR / filename


def default_table_output_path(
    *,
    resolved_y_column: str,
    timestamp: datetime | None = None,
) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"table_{_quantity_slug(resolved_y_column)}_{_table_timestamp_suffix(timestamp)}.csv"
    return OUTPUT_DIR / filename
