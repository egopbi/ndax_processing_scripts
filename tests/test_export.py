from pathlib import Path

from table_data_extraction._test_support import sample_ndax_path
from table_data_extraction.config import CSV_COLUMNS
from table_data_extraction.export import (
    resolve_available_columns,
    save_csv_slice,
)
from table_data_extraction.reader import load_ndax_dataframe


def test_save_csv_slice_creates_excel_friendly_csv(tmp_path: Path):
    dataframe = load_ndax_dataframe(sample_ndax_path())
    output_dir = tmp_path / "folder with spaces"
    output_path = output_dir / "export.csv"

    written_path = save_csv_slice(
        dataframe,
        columns=CSV_COLUMNS,
        output_path=output_path,
    )

    file_bytes = written_path.read_bytes()
    first_line = written_path.read_text(encoding="utf-8-sig").splitlines()[0]

    assert written_path.exists()
    assert file_bytes.startswith(b"\xef\xbb\xbf")
    assert ";" in first_line


def test_resolve_available_columns_reports_missing_values():
    dataframe = load_ndax_dataframe(sample_ndax_path())
    available, missing = resolve_available_columns(
        dataframe,
        [*CSV_COLUMNS, "Missing Column"],
    )

    assert available == CSV_COLUMNS
    assert missing == ["Missing Column"]
