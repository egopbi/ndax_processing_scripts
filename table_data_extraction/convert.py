from pathlib import Path
from typing import Sequence

import pandas as pd

from .columns import normalize_column_name, resolve_column_name
from .export import save_csv_slice
from .output_paths import default_convert_output_path
from .reader import load_ndax_dataframe

TIME_COLUMN = "Time"


def _output_collision_key(path: Path) -> str:
    return str(path.absolute()).casefold()


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


def _build_convert_jobs(
    *,
    source_paths: Sequence[str | Path],
    output_dir: str | Path | None = None,
) -> list[tuple[Path, Path]]:
    jobs: list[tuple[Path, Path]] = []
    for source_path in source_paths:
        source = Path(source_path)
        jobs.append(
            (
                source,
                default_convert_output_path(
                    source_path=source,
                    output_dir=output_dir,
                ),
            )
        )
    return jobs


def _validate_unique_output_paths(jobs: Sequence[tuple[Path, Path]]) -> None:
    collisions: dict[str, list[tuple[Path, Path]]] = {}
    for source_path, output_path in jobs:
        key = _output_collision_key(output_path)
        collisions.setdefault(key, []).append((source_path, output_path))

    duplicated = [entries for entries in collisions.values() if len(entries) > 1]
    if not duplicated:
        return

    collision_details = []
    for entries in duplicated:
        output_path = entries[0][1]
        sources = ", ".join(str(source_path) for source_path, _ in entries)
        collision_details.append(
            f"{output_path}: {sources}"
        )
    raise ValueError(
        "Output path collision detected in convert mode. "
        "Input files must resolve to unique output CSV paths. "
        f"Collisions: {'; '.join(collision_details)}"
    )


def _convert_single_file(
    *,
    source_path: Path,
    output_path: Path,
    columns: Sequence[str],
) -> Path:
    dataframe = load_ndax_dataframe(source_path)
    resolved_columns = resolve_convert_columns(dataframe, columns)
    return save_csv_slice(
        dataframe,
        columns=resolved_columns,
        output_path=output_path,
    )


def convert_ndax_file(
    *,
    source_path: str | Path,
    columns: Sequence[str],
    output_dir: str | Path | None = None,
) -> Path:
    jobs = _build_convert_jobs(
        source_paths=[source_path],
        output_dir=output_dir,
    )
    source, output = jobs[0]
    return _convert_single_file(
        source_path=source,
        output_path=output,
        columns=columns,
    )


def convert_ndax_files(
    *,
    source_paths: Sequence[str | Path],
    columns: Sequence[str],
    output_dir: str | Path | None = None,
) -> list[Path]:
    if not source_paths:
        raise ValueError("At least one NDAX file path must be provided.")

    jobs = _build_convert_jobs(
        source_paths=source_paths,
        output_dir=output_dir,
    )
    _validate_unique_output_paths(jobs)

    outputs: list[Path] = []
    for source_path, output_path in jobs:
        outputs.append(
            _convert_single_file(
                source_path=source_path,
                output_path=output_path,
                columns=columns,
            )
        )
    return outputs
