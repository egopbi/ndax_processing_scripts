from pathlib import Path

from textual import events

from table_data_extraction.tui.path_drop import parse_dropped_paths
from table_data_extraction.tui.widgets.file_list import FileList


def test_parse_dropped_paths_supports_quoted_windows_payload() -> None:
    payload = '"C:\\Data\\sample 1.ndax" "D:\\More\\sample_2.ndax"'

    parsed = parse_dropped_paths(payload)

    assert parsed == (
        Path("C:\\Data\\sample 1.ndax"),
        Path("D:\\More\\sample_2.ndax"),
    )


def test_parse_dropped_paths_deduplicates_and_ignores_non_ndax() -> None:
    payload = "\n".join([
        "C:\\Data\\sample_1.ndax",
        "C:\\Data\\notes.txt",
        "C:\\Data\\sample_1.ndax",
        "C:\\Data\\sample_2.NDAX",
    ])

    parsed = parse_dropped_paths(payload)

    assert parsed == (
        Path("C:\\Data\\sample_1.ndax"),
        Path("C:\\Data\\sample_2.NDAX"),
    )


def test_parse_dropped_paths_supports_file_urls() -> None:
    payload = "file:///C:/Data/example_1.ndax"

    parsed = parse_dropped_paths(payload)

    assert parsed == (Path("C:/Data/example_1.ndax"),)


def test_file_list_appends_paths_from_paste_event() -> None:
    file_list = FileList()

    file_list.on_paste(events.Paste('"C:\\Data\\one.ndax"'))
    file_list.on_paste(events.Paste('"C:\\Data\\two.ndax"'))

    assert file_list.paths == (
        Path("C:\\Data\\one.ndax"),
        Path("C:\\Data\\two.ndax"),
    )
