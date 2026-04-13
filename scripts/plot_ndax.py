import argparse
from pathlib import Path
import sys
from typing import Sequence

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from table_data_extraction.output_paths import (
    default_plot_output_path,
    default_separate_plot_output_path,
    sample_name_from_path,
)
from table_data_extraction.plotting import (
    AxisLimits,
    PlotSeries,
    prepare_plot_frame,
    resolve_plot_output_dimensions,
    resolve_shared_initial_cycle_trim_points,
    resolve_plot_columns,
    resolve_shared_startup_tail_trim_points,
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
    parser.add_argument(
        "--separate",
        action="store_true",
        help=(
            "Generate one JPG per input file using source file stems "
            "as output names."
        ),
    )
    parser.add_argument("--output", help="Optional JPG output path.")
    parser.add_argument(
        "--output-width-px",
        type=int,
        help=(
            "Optional JPG width in pixels. Default: 1500. "
            "Valid range: 300 to 6000."
        ),
    )
    parser.add_argument(
        "--output-height-px",
        type=int,
        help=(
            "Optional JPG height in pixels. Default: 900. "
            "Valid range: 300 to 6000."
        ),
    )
    return parser


def _build_limits(minimum: float | None, maximum: float | None) -> AxisLimits:
    if minimum is None and maximum is None:
        return None
    return (minimum, maximum)


def _resolve_labels(
    files: Sequence[str], labels: Sequence[str] | None
) -> list[str]:
    if labels is None:
        return [sample_name_from_path(file_path) for file_path in files]

    if len(labels) != len(files):
        raise ValueError("Number of labels must match number of files.")

    return [str(label) for label in labels]


def _output_collision_key(path: Path) -> str:
    return str(path.absolute()).casefold()


def _resolve_separate_output_paths(
    input_paths: Sequence[Path],
) -> list[Path]:
    outputs = [
        default_separate_plot_output_path(source_path=file_path)
        for file_path in input_paths
    ]
    collisions: dict[str, list[Path]] = {}
    for output_path in outputs:
        collisions.setdefault(_output_collision_key(output_path), []).append(
            output_path
        )

    duplicated = [paths for paths in collisions.values() if len(paths) > 1]
    if duplicated:
        collision_details = ", ".join(str(paths[0]) for paths in duplicated)
        raise ValueError(
            "Output path collision detected in separate plot mode. "
            "Input files must resolve to unique output JPG paths. "
            f"Collisions: {collision_details}"
        )
    return outputs


def _resolve_output_dimensions(args: argparse.Namespace) -> tuple[int, int]:
    return resolve_plot_output_dimensions(
        output_width_px=args.output_width_px,
        output_height_px=args.output_height_px,
    )


def run(argv: Sequence[str] | None = None) -> Path | list[Path]:
    args = _build_parser().parse_args(argv)
    if args.separate and args.output is not None:
        raise ValueError(
            "--separate cannot be used together with --output."
        )

    output_width_px, output_height_px = _resolve_output_dimensions(args)

    labels = _resolve_labels(args.files, args.labels)
    input_paths = [Path(file_path) for file_path in args.files]

    lines: list[PlotSeries] = []
    prepared_inputs = []
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
        prepared_inputs.append((dataframe, label))

        if resolved_x_column is None:
            resolved_x_column = current_resolved_x_column
            resolved_y_column = current_resolved_y_column
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

    shared_startup_tail_trim_points: int | None = None
    if len(prepared_inputs) > 1:
        shared_startup_tail_trim_points = (
            resolve_shared_startup_tail_trim_points(
                [dataframe for dataframe, _ in prepared_inputs],
                y_col=resolved_y_column,
            )
        )

    shared_initial_cycle_trim_points: int | None = None
    if (
        len(prepared_inputs) > 1
        and shared_startup_tail_trim_points is not None
    ):
        shared_initial_cycle_trim_points = (
            resolve_shared_initial_cycle_trim_points(
                [dataframe for dataframe, _ in prepared_inputs],
                startup_tail_trim_points=shared_startup_tail_trim_points,
            )
        )

    for dataframe, label in prepared_inputs:
        plot_frame, current_x_label, current_y_label = prepare_plot_frame(
            dataframe,
            x_col=resolved_x_column,
            y_col=resolved_y_column,
            startup_tail_trim_points=shared_startup_tail_trim_points,
            initial_cycle_trim_points=shared_initial_cycle_trim_points,
        )
        lines.append(PlotSeries(label=label, frame=plot_frame))
        if x_label is None:
            x_label = current_x_label
            y_label = current_y_label

    assert x_label is not None
    assert y_label is not None

    x_limits = _build_limits(args.x_min, args.x_max)
    y_limits = _build_limits(args.y_min, args.y_max)
    if args.separate:
        output_paths = _resolve_separate_output_paths(input_paths)
        written_paths: list[Path] = []
        for line, output_path in zip(lines, output_paths, strict=True):
            written_paths.append(
                save_multi_series_plot(
                    [line],
                    x_label=x_label,
                    y_label=y_label,
                    output_path=output_path,
                    x_limits=x_limits,
                    y_limits=y_limits,
                    output_width_px=output_width_px,
                    output_height_px=output_height_px,
                )
            )
        return written_paths

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
        x_limits=x_limits,
        y_limits=y_limits,
        output_width_px=output_width_px,
        output_height_px=output_height_px,
    )


def main(argv: Sequence[str] | None = None) -> int:
    try:
        output = run(argv)
    except Exception as error:
        print(f"Plot generation failed: {error}", file=sys.stderr)
        return 1

    if isinstance(output, list):
        for output_path in output:
            print(f"Saved plot to {output_path}")
    else:
        print(f"Saved plot to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
