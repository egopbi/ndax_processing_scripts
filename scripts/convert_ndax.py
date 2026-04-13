import argparse
from pathlib import Path
import sys
from typing import Sequence

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from table_data_extraction.convert import convert_ndax_files


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert one or more NDAX files to CSV slices."
    )
    parser.add_argument(
        "--files",
        nargs="+",
        required=True,
        help="One or more .ndax file paths.",
    )
    parser.add_argument(
        "--columns",
        nargs="+",
        required=True,
        help="One or more columns to include in CSV output.",
    )
    parser.add_argument(
        "--output-dir",
        help="Optional directory where CSV files will be written.",
    )
    return parser


def run(argv: Sequence[str] | None = None) -> list[Path]:
    args = _build_parser().parse_args(argv)
    output_dir = Path(args.output_dir) if args.output_dir else None
    return convert_ndax_files(
        source_paths=[Path(file_path) for file_path in args.files],
        columns=args.columns,
        output_dir=output_dir,
    )


def main(argv: Sequence[str] | None = None) -> int:
    try:
        output_paths = run(argv)
    except Exception as error:
        print(f"Convert failed: {error}", file=sys.stderr)
        return 1

    for output_path in output_paths:
        print(f"Saved CSV to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
