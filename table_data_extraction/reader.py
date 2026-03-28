from pathlib import Path

import pandas as pd
from NewareNDA import read as read_neware_file


def load_ndax_dataframe(path: Path) -> pd.DataFrame:
    source_path = Path(path)
    if not source_path.is_file():
        raise FileNotFoundError(f"NDAX file not found: {source_path}")

    dataframe = read_neware_file(str(source_path))
    if not isinstance(dataframe, pd.DataFrame):
        raise TypeError("NewareNDA.read() did not return a pandas DataFrame.")

    return dataframe


def list_columns(path: Path) -> list[str]:
    return [str(column) for column in load_ndax_dataframe(path).columns.tolist()]
