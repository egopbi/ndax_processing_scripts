from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from .reader import load_ndax_dataframe


@dataclass(frozen=True)
class HealthCheckResult:
    path: Path
    row_count: int
    columns: list[str]
    required_columns: list[str]
    missing_columns: list[str]


def run_health_check(
    path: Path, required_columns: Sequence[str]
) -> HealthCheckResult:
    dataframe = load_ndax_dataframe(path)
    if dataframe.empty:
        raise ValueError(f"NDAX file contains no rows: {path}")

    columns = [str(column) for column in dataframe.columns.tolist()]
    required = list(dict.fromkeys(required_columns))
    missing = [column for column in required if column not in columns]

    return HealthCheckResult(
        path=Path(path),
        row_count=len(dataframe.index),
        columns=columns,
        required_columns=required,
        missing_columns=missing,
    )


def format_health_check_report(
    result: HealthCheckResult,
    *,
    plot_columns: Sequence[str],
    csv_columns: Sequence[str],
) -> str:
    plot_missing = [
        column for column in plot_columns if column not in result.columns
    ]
    csv_missing = [
        column for column in csv_columns if column not in result.columns
    ]

    lines = [
        f"NDAX health check: {result.path}",
        f"Rows: {result.row_count}",
        f"Columns found: {len(result.columns)}",
        (
            "Plot columns: OK"
            if not plot_missing
            else f"Plot columns: MISSING -> {', '.join(plot_missing)}"
        ),
        (
            "CSV columns: OK"
            if not csv_missing
            else f"CSV columns: MISSING -> {', '.join(csv_missing)}"
        ),
        "",
        "Available columns:",
    ]
    lines.extend(f"- {column}" for column in result.columns)
    return "\n".join(lines)
