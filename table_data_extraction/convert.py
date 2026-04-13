from pathlib import Path
from typing import Sequence

import pandas as pd

from .columns import normalize_column_name, resolve_column_name
from .export import save_csv_slice
from .output_paths import default_convert_output_path
from .reader import load_ndax_dataframe

TIME_COLUMN = "Time"


def _requested_columns_with_time(columns: Sequence[str]) -> list[str]:
    requested = [str(column) for column in columns]
    if not requested:
        raise ValueError("At least one column must be provided.")

    ordered: list[str] = []
    seen: set[str] = set()
    for column in [TIME_COLUMN, *requested]:
        normalized = normalize_column_name(column)
        if normalized in seen:
            continue
        seen.add(normalized)
        ordered.append(column)
    return ordered


def resolve_convert_columns(
    dataframe: pd.DataFrame, columns: Sequence[str]
) -> list[str]:
    resolved: list[str] = []
    seen: set[str] = set()
    for column in _requested_columns_with_time(columns):
        resolved_column = resolve_column_name(dataframe, column)
        normalized = normalize_column_name(resolved_column)
        if normalized in seen:
            continue
        seen.add(normalized)
        resolved.append(resolved_column)
    return resolved


def convert_ndax_file(
    *,
    source_path: str | Path,
    columns: Sequence[str],
    output_dir: str | Path | None = None,
) -> Path:
    source = Path(source_path)
    dataframe = load_ndax_dataframe(source)
    resolved_columns = resolve_convert_columns(dataframe, columns)
    output_path = default_convert_output_path(
        source_path=source,
        output_dir=output_dir,
    )
    return save_csv_slice(
        dataframe,
        columns=resolved_columns,
        output_path=output_path,
    )


def convert_ndax_files(
    *,
    source_paths: Sequence[str | Path],
    columns: Sequence[str],
    output_dir: str | Path | None = None,
) -> list[Path]:
    if not source_paths:
        raise ValueError("At least one NDAX file path must be provided.")

    outputs: list[Path] = []
    for source_path in source_paths:
        outputs.append(
            convert_ndax_file(
                source_path=source_path,
                columns=columns,
                output_dir=output_dir,
            )
        )
    return outputs
