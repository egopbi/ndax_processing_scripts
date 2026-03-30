import argparse
from pathlib import Path
import sys
from typing import Sequence

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from table_data_extraction.config import (
    PLOT_OUTPUT,
    PLOT_X_COLUMN,
    PLOT_Y_COLUMN,
    X_LIMITS,
    Y_LIMITS,
)
from table_data_extraction.plotting import save_plot
from table_data_extraction.reader import load_ndax_dataframe


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a demo plot for a single NDAX file."
    )
    parser.add_argument("file", help="Path to the NDAX file.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    try:
        source_file = Path(args.file)
        dataframe = load_ndax_dataframe(source_file)
        output_path = save_plot(
            dataframe,
            x_col=PLOT_X_COLUMN,
            y_col=PLOT_Y_COLUMN,
            output_path=PLOT_OUTPUT,
            series_label=source_file.stem,
            x_limits=X_LIMITS,
            y_limits=Y_LIMITS,
        )
    except Exception as error:
        print(f"Plot generation failed: {error}", file=sys.stderr)
        return 1

    print(f"Saved demo plot to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
