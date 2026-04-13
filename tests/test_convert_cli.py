import importlib.util
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT_DIR / "scripts" / "convert_ndax.py"


def _load_convert_cli_module():
    spec = importlib.util.spec_from_file_location("convert_ndax_cli", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_cli_passes_files_columns_and_output_dir_to_domain(
    tmp_path: Path, capsys
) -> None:
    module = _load_convert_cli_module()
    captured: dict[str, object] = {}

    def fake_convert_ndax_files(*, source_paths, columns, output_dir=None):
        captured["source_paths"] = list(source_paths)
        captured["columns"] = list(columns)
        captured["output_dir"] = output_dir
        return [tmp_path / "first.csv", tmp_path / "second.csv"]

    module.convert_ndax_files = fake_convert_ndax_files

    first_file = tmp_path / "first.ndax"
    second_file = tmp_path / "second.ndax"
    output_dir = tmp_path / "export"
    exit_code = module.main([
        "--files",
        str(first_file),
        str(second_file),
        "--columns",
        "Voltage",
        "Current(mA)",
        "--output-dir",
        str(output_dir),
    ])

    assert exit_code == 0
    assert captured["source_paths"] == [first_file, second_file]
    assert captured["columns"] == ["Voltage", "Current(mA)"]
    assert captured["output_dir"] == output_dir
    stdout = capsys.readouterr().out
    assert "Saved CSV to" in stdout
    assert "first.csv" in stdout
    assert "second.csv" in stdout


def test_cli_returns_non_zero_on_domain_error(capsys) -> None:
    module = _load_convert_cli_module()

    def fake_convert_ndax_files(*, source_paths, columns, output_dir=None):
        raise ValueError("boom")

    module.convert_ndax_files = fake_convert_ndax_files
    exit_code = module.main([
        "--files",
        "sample.ndax",
        "--columns",
        "Voltage",
    ])

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "Convert failed" in captured.err
    assert "boom" in captured.err
