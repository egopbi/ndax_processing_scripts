import argparse
from pathlib import Path
import sys
from typing import Sequence

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from table_data_extraction.columns import resolve_column_name
from table_data_extraction.export import (
    format_extrema_header_labels,
    save_comparison_table,
)
from table_data_extraction.extrema import (
    ExtremaIndices,
    find_six_extrema_indices,
)
from table_data_extraction.output_paths import (
    default_table_output_path,
    sample_name_from_path,
)
from table_data_extraction.preprocess import (
    prepare_x_series,
    trim_leading_rest_rows,
)
from table_data_extraction.reader import load_ndax_dataframe
from table_data_extraction.short_circuit import (
    detect_short_circuit_time_hours,
    round_short_circuit_hours,
)
from table_data_extraction.table_builder import build_comparison_row
from table_data_extraction.time_utils import timestamps_are_usable
from table_data_extraction.plotting import resolve_axis_label


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a comparison extrema table for one or more NDAX files."
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
        "--anchor-x",
        nargs="+",
        type=float,
        required=True,
        help=(
            "One or more anchor X values. "
            "If --x-column Time, values are in hours."
        ),
    )
    parser.add_argument(
        "--x-column", default="Time", help="X axis column name. Default: Time."
    )
    parser.add_argument(
        "--labels",
        nargs="+",
        help="Optional labels. Count must match --files.",
    )
    parser.add_argument("--output", help="Optional CSV output path.")
    return parser


def _resolve_labels(
    files: Sequence[str], labels: Sequence[str] | None
) -> list[str]:
    if labels is None:
        return [sample_name_from_path(file_path) for file_path in files]

    if len(labels) != len(files):
        raise ValueError("Number of labels must match number of files.")

    return [str(label) for label in labels]


def _normalize_anchor_x_values(anchor_x_values: Sequence[float]) -> list[float]:
    normalized: list[float] = []
    seen: set[float] = set()
    for anchor_x in anchor_x_values:
        normalized_anchor_x = float(anchor_x)
        if normalized_anchor_x in seen:
            continue
        seen.add(normalized_anchor_x)
        normalized.append(normalized_anchor_x)
    return normalized


def _warn_for_missing_extrema(
    *,
    file_path: str,
    label: str,
    anchor_x: float,
    extrema_indices: ExtremaIndices,
) -> None:
    missing_labels = [
        extrema_label
        for extrema_label, index in extrema_indices.items()
        if index is None
    ]
    if not missing_labels:
        return

    missing = ", ".join(missing_labels)
    print(
        (
            f"Warning: missing extrema for '{label}' ({file_path}) "
            f"at anchor-x {anchor_x}: {missing}"
        ),
        file=sys.stderr,
    )


def run(argv: Sequence[str] | None = None) -> Path:
    args = _build_parser().parse_args(argv)
    labels = _resolve_labels(args.files, args.labels)
    anchors = _normalize_anchor_x_values(args.anchor_x)
    input_paths = [Path(file_path) for file_path in args.files]

    rows: list[dict[str, object]] = []
    resolved_y_column_for_output: str | None = None

    for file_path, label in zip(input_paths, labels, strict=True):
        dataframe = load_ndax_dataframe(file_path)
        resolved_x_column = resolve_column_name(dataframe, args.x_column)
        resolved_y_column = resolve_column_name(dataframe, args.y_column)
        trimmed = trim_leading_rest_rows(dataframe)
        short_circuit_raw = detect_short_circuit_time_hours(dataframe)
        short_circuit_rounded = round_short_circuit_hours(short_circuit_raw)

        if resolved_x_column == "Time" and not timestamps_are_usable(trimmed):
            x_series = trimmed[resolved_x_column]
        else:
            x_series = prepare_x_series(trimmed, resolved_x_column)
        y_series = trimmed[resolved_y_column]
        if resolved_y_column == "Time":
            if timestamps_are_usable(trimmed):
                y_series = prepare_x_series(trimmed, resolved_y_column) / 3600
            else:
                y_series = y_series / 3600
        elif resolved_y_column == "Voltage":
            y_series = y_series * 1000

        extrema_indices_by_anchor: list[ExtremaIndices] = []
        for anchor_x in anchors:
            anchor_x_for_search = anchor_x
            if resolved_x_column == "Time":
                anchor_x_for_search = anchor_x * 3600

            extrema_indices = find_six_extrema_indices(
                x_series=x_series,
                y_series=y_series,
                anchor_x=anchor_x_for_search,
            )
            _warn_for_missing_extrema(
                file_path=file_path,
                label=label,
                anchor_x=anchor_x,
                extrema_indices=extrema_indices,
            )
            extrema_indices_by_anchor.append(extrema_indices)

        row = build_comparison_row(
            label=label,
            y_series=y_series,
            anchors=anchors,
            short_circuit_hours=short_circuit_rounded,
            extrema_indices_by_anchor=extrema_indices_by_anchor,
        )
        rows.append(row)

        if resolved_y_column_for_output is None:
            resolved_y_column_for_output = resolved_y_column

    assert resolved_y_column_for_output is not None
    extrema_header_labels = format_extrema_header_labels(
        resolve_axis_label(resolved_y_column_for_output)
    )
    output_path = (
        default_table_output_path(
            source_paths=input_paths,
            resolved_y_column=resolved_y_column_for_output,
        )
        if args.output is None
        else Path(args.output)
    )

    return save_comparison_table(
        rows=rows,
        anchors=anchors,
        output_path=output_path,
        extrema_header_labels=extrema_header_labels,
    )


def main(argv: Sequence[str] | None = None) -> int:
    try:
        output_path = run(argv)
    except Exception as error:
        print(f"Table generation failed: {error}", file=sys.stderr)
        return 1

    print(f"Saved table to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
