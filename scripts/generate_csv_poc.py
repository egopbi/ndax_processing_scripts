import argparse
from pathlib import Path
import sys
from typing import Sequence

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from table_data_extraction.config import CSV_COLUMNS, CSV_OUTPUT
from table_data_extraction.export import (
    resolve_available_columns,
    save_csv_slice,
)
from table_data_extraction.reader import load_ndax_dataframe


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a demo CSV slice for a single NDAX file."
    )
    parser.add_argument("file", help="Path to the NDAX file.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    try:
        source_file = Path(args.file)
        dataframe = load_ndax_dataframe(source_file)
        available_columns, missing_columns = resolve_available_columns(
            dataframe, CSV_COLUMNS
        )
        output_path = save_csv_slice(
            dataframe,
            columns=available_columns,
            output_path=CSV_OUTPUT,
        )
    except Exception as error:
        print(f"CSV generation failed: {error}", file=sys.stderr)
        return 1

    print(f"Saved demo CSV to {output_path}")
    if missing_columns:
        print(f"Skipped missing columns: {', '.join(missing_columns)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
