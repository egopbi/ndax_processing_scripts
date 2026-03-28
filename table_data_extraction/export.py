from pathlib import Path
from typing import Sequence

import pandas as pd


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
