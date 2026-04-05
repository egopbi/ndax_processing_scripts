from pathlib import Path

import pandas as pd

from table_data_extraction.export import save_comparison_table
from table_data_extraction.table_builder import (
    build_comparison_row,
    comparison_table_columns_for_anchors,
)


def test_comparison_table_columns_include_short_circuit_last() -> None:
    assert (
        comparison_table_columns_for_anchors([0.5, 1.0])[-1]
        == "Короткое замыкание"
    )


def test_comparison_table_columns_for_anchors_builds_unique_block_keys() -> (
    None
):
    assert comparison_table_columns_for_anchors([0.5, 1.0]) == (
        "name",
        "anchor_0__+U_l",
        "anchor_0__+U_m",
        "anchor_0__+U_r",
        "anchor_0__-U_l",
        "anchor_0__-U_m",
        "anchor_0__-U_r",
        "anchor_1__+U_l",
        "anchor_1__+U_m",
        "anchor_1__+U_r",
        "anchor_1__-U_l",
        "anchor_1__-U_m",
        "anchor_1__-U_r",
        "Короткое замыкание",
    )


def test_build_comparison_row_maps_extrema_indices_to_y_values() -> None:
    y_series = pd.Series([10.0, 20.0, 30.0, 40.0, 50.0, 60.0], dtype=float)

    row = build_comparison_row(
        label="sample_a",
        y_series=y_series,
        anchors=[2.5],
        short_circuit_hours=185,
        extrema_indices_by_anchor=[
            {
                "+U_l": 0,
                "+U_m": 1,
                "+U_r": 2,
                "-U_l": 3,
                "-U_m": 4,
                "-U_r": 5,
            }
        ],
    )

    assert row == {
        "name": "sample_a",
        "anchor_0__+U_l": 10.0,
        "anchor_0__+U_m": 20.0,
        "anchor_0__+U_r": 30.0,
        "anchor_0__-U_l": 40.0,
        "anchor_0__-U_m": 50.0,
        "anchor_0__-U_r": 60.0,
        "Короткое замыкание": 185,
    }


def test_build_comparison_row_uses_empty_cell_for_missing_extrema() -> None:
    y_series = pd.Series([11.0, 22.0, 33.0, 44.0], dtype=float)

    row = build_comparison_row(
        label="sample_b",
        y_series=y_series,
        anchors=[1.0],
        short_circuit_hours=None,
        extrema_indices_by_anchor=[
            {
                "+U_l": None,
                "+U_m": 1,
                "+U_r": None,
                "-U_l": 2,
                "-U_m": None,
                "-U_r": None,
            }
        ],
    )

    assert row == {
        "name": "sample_b",
        "anchor_0__+U_l": "",
        "anchor_0__+U_m": 22.0,
        "anchor_0__+U_r": "",
        "anchor_0__-U_l": 33.0,
        "anchor_0__-U_m": "",
        "anchor_0__-U_r": "",
        "Короткое замыкание": "",
    }


def test_build_comparison_row_keeps_anchor_blocks_isolated() -> None:
    y_series = pd.Series([10.0, 20.0, 30.0, 40.0, 50.0, 60.0], dtype=float)

    row = build_comparison_row(
        label="sample_c",
        y_series=y_series,
        anchors=[0.5, 1.0],
        short_circuit_hours=185,
        extrema_indices_by_anchor=[
            {
                "+U_l": 0,
                "+U_m": 1,
                "+U_r": 2,
                "-U_l": 3,
                "-U_m": 4,
                "-U_r": 5,
            },
            {
                "+U_l": None,
                "+U_m": 1,
                "+U_r": None,
                "-U_l": 3,
                "-U_m": None,
                "-U_r": None,
            },
        ],
    )

    assert row["anchor_0__+U_l"] == 10.0
    assert row["anchor_0__-U_r"] == 60.0
    assert row["anchor_1__+U_l"] == ""
    assert row["anchor_1__+U_m"] == 20.0
    assert row["anchor_1__-U_l"] == 40.0
    assert row["anchor_1__-U_r"] == ""
    assert row["Короткое замыкание"] == 185


def test_save_comparison_table_writes_two_header_rows_and_no_index(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "comparison.csv"
    rows = [
        {
            "name": "sample_a",
            "anchor_0__+U_l": 10.14,
            "anchor_0__+U_m": 20.25,
            "anchor_0__+U_r": 30.36,
            "anchor_0__-U_l": 40.47,
            "anchor_0__-U_m": 50.58,
            "anchor_0__-U_r": 60.69,
            "Короткое замыкание": 185,
        },
        {
            "name": "sample_b",
            "anchor_0__+U_l": "",
            "anchor_0__+U_m": 12.04,
            "anchor_0__+U_r": "",
            "anchor_0__-U_l": -10.05,
            "anchor_0__-U_m": "",
            "anchor_0__-U_r": -20.06,
            "Короткое замыкание": "",
        },
    ]

    written_path = save_comparison_table(
        rows=rows, anchors=[25], output_path=output_path
    )

    file_bytes = written_path.read_bytes()
    lines = written_path.read_text(encoding="utf-8-sig").splitlines()

    assert written_path.exists()
    assert file_bytes.startswith(b"\xef\xbb\xbf")
    assert lines[0] == "name;25.0;;;;;;Короткое замыкание"
    assert lines[1] == ";+U_l;+U_m;+U_r;-U_l;-U_m;-U_r;"
    assert lines[2] == "sample_a;10.1;20.2;30.4;40.5;50.6;60.7;185"
    assert lines[3] == "sample_b;;12.0;;-10.1;;-20.1;"
    assert not lines[2].startswith("0;")


def test_save_comparison_table_writes_unit_bearing_extrema_headers(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "comparison.csv"
    rows = [
        {
            "name": "sample_a",
            "anchor_0__+U_l": 10.14,
            "anchor_0__+U_m": 20.25,
            "anchor_0__+U_r": 30.36,
            "anchor_0__-U_l": 40.47,
            "anchor_0__-U_m": 50.58,
            "anchor_0__-U_r": 60.69,
            "Короткое замыкание": 185,
        }
    ]

    written_path = save_comparison_table(
        rows=rows,
        anchors=[25],
        output_path=output_path,
        extrema_header_labels=(
            "+U_l(mV)",
            "+U_m(mV)",
            "+U_r(mV)",
            "-U_l(mV)",
            "-U_m(mV)",
            "-U_r(mV)",
        ),
    )

    lines = written_path.read_text(encoding="utf-8-sig").splitlines()

    assert lines[0] == "name;25.0;;;;;;Короткое замыкание"
    assert (
        lines[1] == ";+U_l(mV);+U_m(mV);+U_r(mV);-U_l(mV);-U_m(mV);-U_r(mV);"
    )
    assert lines[2] == "sample_a;10.1;20.2;30.4;40.5;50.6;60.7;185"


def test_save_comparison_table_writes_grouped_headers_for_multiple_anchors(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "comparison.csv"
    rows = [
        {
            "name": "sample_a",
            "anchor_0__+U_l": 10.14,
            "anchor_0__+U_m": 20.25,
            "anchor_0__+U_r": 30.36,
            "anchor_0__-U_l": 40.47,
            "anchor_0__-U_m": 50.58,
            "anchor_0__-U_r": 60.69,
            "anchor_1__+U_l": "",
            "anchor_1__+U_m": 12.04,
            "anchor_1__+U_r": "",
            "anchor_1__-U_l": -10.05,
            "anchor_1__-U_m": "",
            "anchor_1__-U_r": -20.06,
            "Короткое замыкание": 185,
        }
    ]

    save_comparison_table(
        rows=rows,
        anchors=[0.5, 1.0],
        output_path=output_path,
    )

    lines = output_path.read_text(encoding="utf-8-sig").splitlines()

    assert lines[0] == "name;0.5;;;;;;1.0;;;;;;Короткое замыкание"
    assert (
        lines[1]
        == ";+U_l;+U_m;+U_r;-U_l;-U_m;-U_r;+U_l;+U_m;+U_r;-U_l;-U_m;-U_r;"
    )
    assert (
        lines[2]
        == "sample_a;10.1;20.2;30.4;40.5;50.6;60.7;;12.0;;-10.1;;-20.1;185"
    )


def test_save_comparison_table_keeps_missing_extrema_cells_empty(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "comparison.csv"
    rows = [
        {
            "name": "sample_a",
            "anchor_0__+U_l": 1.24,
            "anchor_0__+U_m": "",
            "anchor_0__+U_r": "",
            "anchor_0__-U_l": -1.26,
            "anchor_0__-U_m": "",
            "anchor_0__-U_r": "",
            "Короткое замыкание": "",
        }
    ]

    save_comparison_table(rows=rows, anchors=[10], output_path=output_path)
    lines = output_path.read_text(encoding="utf-8-sig").splitlines()

    assert lines[0] == "name;10.0;;;;;;Короткое замыкание"
    assert lines[2] == "sample_a;1.2;;;-1.3;;;"
