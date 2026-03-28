from pathlib import Path
from numbers import Real
import re
from typing import Mapping, Sequence

import pandas as pd

from table_data_extraction.table_builder import COMPARISON_TABLE_COLUMNS, EXTREMA_COLUMNS


def resolve_available_columns(
    dataframe: pd.DataFrame,
    columns: Sequence[str],
) -> tuple[list[str], list[str]]:
    requested = list(dict.fromkeys(columns))
    available = [column for column in requested if column in dataframe.columns]
    missing = [column for column in requested if column not in dataframe.columns]

    if not available:
        raise ValueError("None of the requested CSV columns are present in the DataFrame.")

    return available, missing


def save_csv_slice(
    dataframe: pd.DataFrame,
    *,
    columns: Sequence[str],
    output_path: Path,
) -> Path:
    available_columns, _ = resolve_available_columns(dataframe, columns)
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    dataframe.loc[:, available_columns].to_csv(
        output_file,
        sep=";",
        encoding="utf-8-sig",
        index=False,
    )
    return output_file


def save_comparison_table(
    *,
    rows: Sequence[Mapping[str, object]],
    anchor_x: float | str,
    output_path: Path,
    extrema_header_labels: Sequence[str] | None = None,
) -> Path:
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    header_labels = tuple(extrema_header_labels) if extrema_header_labels is not None else EXTREMA_COLUMNS
    if len(header_labels) != len(EXTREMA_COLUMNS):
        raise ValueError("extrema_header_labels must contain six labels.")

    header_rows = pd.DataFrame(
        [
            {"name": "name", EXTREMA_COLUMNS[0]: _format_comparison_cell(anchor_x)},
            {"name": "", **dict(zip(EXTREMA_COLUMNS, header_labels, strict=True))},
        ],
        columns=COMPARISON_TABLE_COLUMNS,
    ).fillna("")

    body_rows = pd.DataFrame(rows, columns=COMPARISON_TABLE_COLUMNS).fillna("")
    body_rows = body_rows.apply(lambda column: column.map(_format_comparison_cell))
    comparison_table = pd.concat([header_rows, body_rows], ignore_index=True)
    comparison_table.to_csv(
        output_file,
        sep=";",
        encoding="utf-8-sig",
        index=False,
        header=False,
    )
    return output_file


def _format_comparison_cell(value: object) -> object:
    if value == "" or value is None:
        return ""

    if isinstance(value, Real) and not isinstance(value, bool):
        return f"{float(value):.1f}"

    return value


def format_extrema_header_labels(public_y_label: str) -> tuple[str, ...]:
    match = re.fullmatch(r"(.+?)\((.+)\)", public_y_label)
    if not match:
        return EXTREMA_COLUMNS

    unit = match.group(2).strip()
    return tuple(f"{extrema_label}({unit})" for extrema_label in EXTREMA_COLUMNS)
