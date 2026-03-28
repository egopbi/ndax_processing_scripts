from pathlib import Path

import pandas as pd

from table_data_extraction.export import save_comparison_table
from table_data_extraction.table_builder import build_comparison_row


def test_build_comparison_row_maps_extrema_indices_to_y_values() -> None:
    x_series = pd.Series([0, 1, 2, 3, 4, 5], dtype=float)
    y_series = pd.Series([10.0, 20.0, 30.0, 40.0, 50.0, 60.0], dtype=float)

    row = build_comparison_row(
        label="sample_a",
        x_series=x_series,
        y_series=y_series,
        anchor_x=2.5,
        extrema_indices={
            "+U_l": 0,
            "+U_m": 1,
            "+U_r": 2,
            "-U_l": 3,
            "-U_m": 4,
            "-U_r": 5,
        },
    )

    assert row == {
        "name": "sample_a",
        "+U_l": 10.0,
        "+U_m": 20.0,
        "+U_r": 30.0,
        "-U_l": 40.0,
        "-U_m": 50.0,
        "-U_r": 60.0,
    }


def test_build_comparison_row_uses_empty_cell_for_missing_extrema() -> None:
    x_series = pd.Series([0, 1, 2, 3], dtype=float)
    y_series = pd.Series([11.0, 22.0, 33.0, 44.0], dtype=float)

    row = build_comparison_row(
        label="sample_b",
        x_series=x_series,
        y_series=y_series,
        anchor_x=1.0,
        extrema_indices={
            "+U_l": None,
            "+U_m": 1,
            "+U_r": None,
            "-U_l": 2,
            "-U_m": None,
            "-U_r": None,
        },
    )

    assert row == {
        "name": "sample_b",
        "+U_l": "",
        "+U_m": 22.0,
        "+U_r": "",
        "-U_l": 33.0,
        "-U_m": "",
        "-U_r": "",
    }


def test_save_comparison_table_writes_two_header_rows_and_no_index(tmp_path: Path) -> None:
    output_path = tmp_path / "comparison.csv"
    rows = [
        {
            "name": "sample_a",
            "+U_l": 10.14,
            "+U_m": 20.25,
            "+U_r": 30.36,
            "-U_l": 40.47,
            "-U_m": 50.58,
            "-U_r": 60.69,
        },
        {
            "name": "sample_b",
            "+U_l": "",
            "+U_m": 12.04,
            "+U_r": "",
            "-U_l": -10.05,
            "-U_m": "",
            "-U_r": -20.06,
        },
    ]

    written_path = save_comparison_table(rows=rows, anchor_x=25, output_path=output_path)

    file_bytes = written_path.read_bytes()
    lines = written_path.read_text(encoding="utf-8-sig").splitlines()

    assert written_path.exists()
    assert file_bytes.startswith(b"\xef\xbb\xbf")
    assert lines[0] == "name;25.0;;;;;"
    assert lines[1] == ";+U_l;+U_m;+U_r;-U_l;-U_m;-U_r"
    assert lines[2] == "sample_a;10.1;20.2;30.4;40.5;50.6;60.7"
    assert lines[3] == "sample_b;;12.0;;-10.1;;-20.1"
    assert not lines[2].startswith("0;")


def test_save_comparison_table_writes_unit_bearing_extrema_headers(tmp_path: Path) -> None:
    output_path = tmp_path / "comparison.csv"
    rows = [
        {
            "name": "sample_a",
            "+U_l": 10.14,
            "+U_m": 20.25,
            "+U_r": 30.36,
            "-U_l": 40.47,
            "-U_m": 50.58,
            "-U_r": 60.69,
        }
    ]

    written_path = save_comparison_table(
        rows=rows,
        anchor_x=25,
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

    assert lines[0] == "name;25.0;;;;;"
    assert lines[1] == ";+U_l(mV);+U_m(mV);+U_r(mV);-U_l(mV);-U_m(mV);-U_r(mV)"
    assert lines[2] == "sample_a;10.1;20.2;30.4;40.5;50.6;60.7"


def test_save_comparison_table_keeps_missing_extrema_cells_empty(tmp_path: Path) -> None:
    output_path = tmp_path / "comparison.csv"
    rows = [
        {
            "name": "sample_a",
            "+U_l": 1.24,
            "+U_m": "",
            "+U_r": "",
            "-U_l": -1.26,
            "-U_m": "",
            "-U_r": "",
        }
    ]

    save_comparison_table(rows=rows, anchor_x=10, output_path=output_path)
    lines = output_path.read_text(encoding="utf-8-sig").splitlines()

    assert lines[0] == "name;10.0;;;;;"
    assert lines[2] == "sample_a;1.2;;;-1.3;;"
