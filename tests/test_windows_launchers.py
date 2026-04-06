from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


def _read_root_file(filename: str) -> str:
    return (ROOT_DIR / filename).read_text(encoding="utf-8")


def test_setup_windows_cmd_bootstraps_project_venv() -> None:
    content = _read_root_file("setup_windows.cmd").lower()

    assert "%~dp0" in content
    assert "py -m venv .venv" in content
    assert ".venv\\scripts\\python.exe" in content
    assert "pip install --upgrade pip" in content
    assert "pip install -r requirements.txt" in content
    assert "команда py не найдена" in content


def test_plot_ndax_cmd_proxies_to_project_venv_python() -> None:
    content = _read_root_file("plot_ndax.cmd").lower()

    assert "%~dp0" in content
    assert ".venv\\scripts\\python.exe" in content
    assert "scripts\\plot_ndax.py" in content
    assert "%*" in content
    assert "setup_windows.cmd" in content


def test_build_comparison_table_cmd_proxies_to_project_venv_python() -> None:
    content = _read_root_file("build_comparison_table.cmd").lower()

    assert "%~dp0" in content
    assert ".venv\\scripts\\python.exe" in content
    assert "scripts\\build_comparison_table.py" in content
    assert "%*" in content
    assert "setup_windows.cmd" in content


def test_readme_is_windows_only_and_uses_helper_scripts() -> None:
    content = _read_root_file("README.md")

    assert ".\\setup_windows.cmd" in content
    assert ".\\plot_ndax.cmd" in content
    assert ".\\build_comparison_table.cmd" in content
    assert "macOS" not in content
    assert "python3 scripts/plot_ndax.py" not in content
    assert "python3 scripts/build_comparison_table.py" not in content
    assert "generate_plot_poc.py" not in content
    assert "generate_csv_poc.py" not in content
