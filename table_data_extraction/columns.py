from collections import defaultdict
from typing import Iterable, Sequence

import pandas as pd


def normalize_column_name(column_name: str) -> str:
    return str(column_name).strip().casefold()


def _available_columns(
    columns_source: pd.DataFrame | Iterable[str],
) -> list[str]:
    if isinstance(columns_source, pd.DataFrame):
        return [str(column) for column in columns_source.columns.tolist()]
    return [str(column) for column in columns_source]


def resolve_column_name(
    columns_source: pd.DataFrame | Iterable[str], user_column_name: str
) -> str:
    available_columns = _available_columns(columns_source)
    normalized_to_columns: dict[str, list[str]] = defaultdict(list)
    for available_column in available_columns:
        normalized_to_columns[normalize_column_name(available_column)].append(
            available_column
        )

    normalized_input = normalize_column_name(user_column_name)
    matches = normalized_to_columns.get(normalized_input, [])

    if not matches:
        available = ", ".join(available_columns)
        raise ValueError(
            f"Column '{user_column_name}' was not found. Available columns: {available}"
        )
    if len(matches) > 1:
        matched = ", ".join(matches)
        raise ValueError(
            f"Ambiguous column '{user_column_name}'. Matching columns: {matched}"
        )

    return matches[0]


def resolve_column_names(
    columns_source: pd.DataFrame | Iterable[str],
    user_column_names: Sequence[str],
) -> list[str]:
    return [
        resolve_column_name(columns_source, user_column_name)
        for user_column_name in user_column_names
    ]
