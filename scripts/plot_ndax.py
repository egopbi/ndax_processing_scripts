import argparse
from pathlib import Path
import sys
from typing import Sequence

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from table_data_extraction.output_paths import default_plot_output_path
from table_data_extraction.plotting import (
    AxisLimits,
    PlotSeries,
    prepare_plot_frame,
    resolve_plot_columns,
    save_multi_series_plot,
)
from table_data_extraction.reader import load_ndax_dataframe


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a combined plot for one or more NDAX files."
    )
    parser.add_argument(
        "--files",
        nargs="+",
        required=True,
        help="One or more .ndax file paths.",
    )
    parser.add_argument(
        "--y-column", required=True, help="Y axis column name."
    )
    parser.add_argument(
        "--x-column", default="Time", help="X axis column name. Default: Time."
    )
    parser.add_argument(
        "--labels",
        nargs="+",
        help="Optional labels. Count must match --files.",
    )
    parser.add_argument(
        "--x-min",
        type=float,
        help="Optional lower bound for X axis. If --x-column Time, units are hours.",
    )
    parser.add_argument(
        "--x-max",
        type=float,
        help="Optional upper bound for X axis. If --x-column Time, units are hours.",
    )
    parser.add_argument(
        "--y-min",
        type=float,
        help="Optional lower bound for Y axis. If --y-column Voltage, units are mV.",
    )
    parser.add_argument(
        "--y-max",
        type=float,
        help="Optional upper bound for Y axis. If --y-column Voltage, units are mV.",
    )
    parser.add_argument("--output", help="Optional JPG output path.")
    return parser


def _build_limits(minimum: float | None, maximum: float | None) -> AxisLimits:
    if minimum is None and maximum is None:
        return None
    return (minimum, maximum)


def _resolve_labels(
    files: Sequence[str], labels: Sequence[str] | None
) -> list[str]:
    if labels is None:
        return [Path(file_path).stem for file_path in files]

    if len(labels) != len(files):
        raise ValueError("Number of labels must match number of files.")

    return [str(label) for label in labels]


def run(argv: Sequence[str] | None = None) -> Path:
    args = _build_parser().parse_args(argv)

    labels = _resolve_labels(args.files, args.labels)
    input_paths = [Path(file_path) for file_path in args.files]

    lines: list[PlotSeries] = []
    x_label: str | None = None
    y_label: str | None = None
    resolved_x_column: str | None = None
    resolved_y_column: str | None = None

    for file_path, label in zip(input_paths, labels, strict=True):
        dataframe = load_ndax_dataframe(file_path)
        current_resolved_x_column, current_resolved_y_column = (
            resolve_plot_columns(
                dataframe,
                x_column=args.x_column,
                y_column=args.y_column,
            )
        )
        plot_frame, current_x_label, current_y_label = prepare_plot_frame(
            dataframe,
            x_col=current_resolved_x_column,
            y_col=current_resolved_y_column,
        )
        lines.append(PlotSeries(label=label, frame=plot_frame))

        if resolved_x_column is None:
            resolved_x_column = current_resolved_x_column
            resolved_y_column = current_resolved_y_column
            x_label = current_x_label
            y_label = current_y_label
            continue

        if (
            current_resolved_x_column != resolved_x_column
            or current_resolved_y_column != resolved_y_column
        ):
            raise ValueError(
                "Resolved axis columns differ across input files."
            )

    assert resolved_x_column is not None
    assert resolved_y_column is not None
    assert x_label is not None
    assert y_label is not None

    if args.output is None:
        output_path = default_plot_output_path(
            source_paths=input_paths,
            resolved_x_column=resolved_x_column,
            resolved_y_column=resolved_y_column,
        )
    else:
        output_path = Path(args.output)

    return save_multi_series_plot(
        lines,
        x_label=x_label,
        y_label=y_label,
        output_path=output_path,
        x_limits=_build_limits(args.x_min, args.x_max),
        y_limits=_build_limits(args.y_min, args.y_max),
    )


def main(argv: Sequence[str] | None = None) -> int:
    try:
        output_path = run(argv)
    except Exception as error:
        print(f"Plot generation failed: {error}", file=sys.stderr)
        return 1

    print(f"Saved plot to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
