from pathlib import Path

import pandas as pd
import pytest

from table_data_extraction import convert as convert_module


def _sample_dataframe() -> pd.DataFrame:
    return pd.DataFrame({
        "Time": [0.0, 1.0],
        "Voltage": [3.0, 3.1],
        "Current(mA)": [-10.0, -11.0],
    })


def test_resolve_convert_columns_includes_time_and_deduplicates() -> None:
    resolved = convert_module.resolve_convert_columns(
        _sample_dataframe(),
        ["voltage", "TIME", "Current(mA)", "current(mA)"],
    )

    assert resolved == ["Time", "Voltage", "Current(mA)"]


def test_convert_ndax_files_writes_one_csv_per_input_stem(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    captured: list[tuple[list[str], Path]] = []

    def fake_load_ndax_dataframe(_path: Path) -> pd.DataFrame:
        return _sample_dataframe()

    def fake_save_csv_slice(
        dataframe: pd.DataFrame, *, columns, output_path: Path
    ) -> Path:
        assert dataframe is not None
        captured.append((list(columns), output_path))
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("csv", encoding="utf-8")
        return output_path

    monkeypatch.setattr(
        convert_module, "load_ndax_dataframe", fake_load_ndax_dataframe
    )
    monkeypatch.setattr(convert_module, "save_csv_slice", fake_save_csv_slice)

    output_dir = tmp_path / "converted"
    first_file = tmp_path / "sample_a.ndax"
    second_file = tmp_path / "sample_b.ndax"
    outputs = convert_module.convert_ndax_files(
        source_paths=[first_file, second_file],
        columns=["Voltage"],
        output_dir=output_dir,
    )

    assert outputs == [output_dir / "sample_a.csv", output_dir / "sample_b.csv"]
    assert captured == [
        (["Time", "Voltage"], output_dir / "sample_a.csv"),
        (["Time", "Voltage"], output_dir / "sample_b.csv"),
    ]


def test_convert_ndax_files_requires_at_least_one_input_path() -> None:
    with pytest.raises(ValueError, match="At least one NDAX file path"):
        convert_module.convert_ndax_files(source_paths=[], columns=["Voltage"])


def test_convert_ndax_files_fails_fast_on_duplicate_output_stems(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    load_calls = 0
    save_calls = 0

    def fake_load_ndax_dataframe(_path: Path) -> pd.DataFrame:
        nonlocal load_calls
        load_calls += 1
        return _sample_dataframe()

    def fake_save_csv_slice(
        dataframe: pd.DataFrame, *, columns, output_path: Path
    ) -> Path:
        nonlocal save_calls
        assert dataframe is not None
        assert columns is not None
        save_calls += 1
        return output_path

    monkeypatch.setattr(
        convert_module, "load_ndax_dataframe", fake_load_ndax_dataframe
    )
    monkeypatch.setattr(convert_module, "save_csv_slice", fake_save_csv_slice)

    first_file = tmp_path / "first" / "sample.ndax"
    second_file = tmp_path / "second" / "sample.ndax"

    with pytest.raises(ValueError, match="Output path collision detected"):
        convert_module.convert_ndax_files(
            source_paths=[first_file, second_file],
            columns=["Voltage"],
            output_dir=tmp_path / "converted",
        )

    assert load_calls == 0
    assert save_calls == 0
