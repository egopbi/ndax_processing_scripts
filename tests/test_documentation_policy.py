from pathlib import Path

import tomllib

import table_data_extraction


ROOT_DIR = Path(__file__).resolve().parents[1]
README_PATH = ROOT_DIR / "README.md"
PYPROJECT_PATH = ROOT_DIR / "pyproject.toml"
PYTHON_VERSION_PATH = ROOT_DIR / ".python-version"
CANONICAL_DOC_PATHS = [
    ROOT_DIR / "docs" / "project_overview.md",
    ROOT_DIR / "docs" / "architecture.md",
    ROOT_DIR / "docs" / "development_notes.md",
]
LEGACY_PUBLIC_PATHS = [
    ROOT_DIR / "main.py",
    ROOT_DIR / "Project_idea.md",
    ROOT_DIR / "docs" / "plan.md",
    ROOT_DIR / "docs" / "windows_compatibility.md",
    ROOT_DIR / "scripts" / "generate_plot_poc.py",
    ROOT_DIR / "scripts" / "generate_csv_poc.py",
]


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_python_policy_is_consistent_across_repo_docs_and_metadata() -> None:
    readme = _read_text(README_PATH)
    pyproject = tomllib.loads(_read_text(PYPROJECT_PATH))
    python_version = _read_text(PYTHON_VERSION_PATH).strip()

    assert "Python >= 3.12" in readme
    assert "Python 3.13" not in readme
    assert pyproject["project"]["requires-python"] == ">=3.12"
    assert python_version == "3.12"

    for path in CANONICAL_DOC_PATHS:
        assert "Python >= 3.12" in _read_text(path), (
            f"Canonical doc must state Python policy: {path.relative_to(ROOT_DIR)}"
        )


def test_readme_uses_shipped_example_paths_for_first_run_commands() -> None:
    readme = _read_text(README_PATH)

    assert r".\ndax_ui.cmd" in readme
    assert r".\plot_ndax.cmd --files examples\example1_1.ndax --y-column Voltage" in readme
    assert (
        r".\build_comparison_table.cmd --files examples\example1_1.ndax --y-column Voltage --anchor-x 0.5"
        in readme
    )
    assert (
        r'.\convert_ndax.cmd --files examples\example1_1.ndax --columns Voltage "Current(mA)"'
        in readme
    )
    assert "--separate" in readme
    assert "Output filename override" in readme
    assert r"data\sample.ndax" not in readme
    assert "в первой строке заголовка" not in readme


def test_canonical_technical_docs_exist_and_reference_entrypoints_and_config() -> None:
    for path in CANONICAL_DOC_PATHS:
        assert path.exists(), f"Missing canonical doc: {path.relative_to(ROOT_DIR)}"

    combined_docs = "\n".join(_read_text(path) for path in CANONICAL_DOC_PATHS)

    assert "scripts/plot_ndax.py" in combined_docs
    assert "scripts/build_comparison_table.py" in combined_docs
    assert "scripts/convert_ndax.py" in combined_docs
    assert "project_config.yaml" in combined_docs
    assert "table_data_extraction.project_config" in combined_docs
    assert "--separate" in combined_docs
    assert "shared batch preprocessing" in combined_docs or "shared preprocessing" in combined_docs


def test_legacy_public_files_are_removed() -> None:
    for path in LEGACY_PUBLIC_PATHS:
        assert not path.exists(), f"Legacy file should be removed: {path.relative_to(ROOT_DIR)}"

    superpowers_markdown_files = sorted(
        path.relative_to(ROOT_DIR)
        for path in (ROOT_DIR / "docs" / "superpowers").rglob("*.md")
    )
    assert superpowers_markdown_files == []

    plan_markdown_files = sorted(
        path.relative_to(ROOT_DIR) for path in (ROOT_DIR / "plans").rglob("*.md")
    )
    assert plan_markdown_files == []


def test_package_docstring_drops_poc_wording() -> None:
    assert table_data_extraction.__doc__ is not None
    assert "poc" not in table_data_extraction.__doc__.lower()
