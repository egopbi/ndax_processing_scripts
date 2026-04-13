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


def _section(text: str, heading: str) -> str:
    start = text.index(heading)
    remainder = text[start + len(heading) :]
    next_heading = remainder.find("\n## ")
    if next_heading == -1:
        return text[start:]
    return text[start : start + len(heading) + next_heading]


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
    plot_cli_section = _section(readme, r"`.\plot_ndax.cmd` принимает:")
    ui_section = _section(readme, r"Что можно сделать в `.\ndax_ui.cmd`:")
    plot_cli_lines = [line.strip() for line in plot_cli_section.splitlines()]
    ui_lines = [line.strip() for line in ui_section.splitlines()]

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
    width_cli_line = next(line for line in plot_cli_lines if "--output-width-px" in line)
    height_cli_line = next(line for line in plot_cli_lines if "--output-height-px" in line)
    ui_contract_line = next(
        line for line in ui_lines if "Separate" in line and "Output filename override" in line
    )
    plot_options_line = next(line for line in ui_lines if "More Options" in line)
    assert ui_contract_line.index("Separate") < ui_contract_line.index("Output filename override")

    separate_cli_line = next(line for line in plot_cli_lines if "--separate" in line)
    output_cli_line = next(line for line in plot_cli_lines if "--output" in line)
    contract_line = next(
        line
        for line in plot_cli_lines
        if "stem" in line and ("cannot" in line or "нельзя" in line) and "Rest" in line
    )
    assert plot_cli_lines.index(separate_cli_line) < plot_cli_lines.index(output_cli_line)
    assert "Separate" in ui_contract_line
    assert "Output filename override" in ui_contract_line
    assert "--separate" in separate_cli_line
    assert "--output" in output_cli_line
    assert "stem" in contract_line
    assert "Rest" in contract_line
    assert "1500" in readme
    assert "900" in readme
    assert "300" in readme
    assert "6000" in readme
    assert "--output-width-px" in width_cli_line
    assert "--output-height-px" in height_cli_line
    assert "More Options" in plot_options_line
    assert r"data\sample.ndax" not in readme
    assert "в первой строке заголовка" not in readme


def test_canonical_technical_docs_exist_and_reference_entrypoints_and_config() -> None:
    for path in CANONICAL_DOC_PATHS:
        assert path.exists(), f"Missing canonical doc: {path.relative_to(ROOT_DIR)}"

    project_overview = _read_text(ROOT_DIR / "docs" / "project_overview.md")
    architecture = _read_text(ROOT_DIR / "docs" / "architecture.md")
    development_notes = _read_text(ROOT_DIR / "docs" / "development_notes.md")

    plot_contract = _section(project_overview, "Plot mode behavior contract:")
    plot_data_flow = _section(architecture, "`scripts/plot_ndax.py`:")

    assert "scripts/plot_ndax.py" in project_overview
    assert "scripts/build_comparison_table.py" in project_overview
    assert "scripts/convert_ndax.py" in project_overview
    assert "project_config.yaml" in project_overview
    assert "table_data_extraction.project_config" in project_overview
    assert "output-width-px" in project_overview
    assert "output-height-px" in project_overview
    assert "scripts/plot_ndax.py" in architecture
    assert "project_config.yaml" in architecture
    assert "table_data_extraction.project_config" in architecture
    assert "Python >= 3.12" in development_notes

    plot_contract_lines = [line.strip() for line in plot_contract.splitlines()]
    plot_data_flow_lines = [line.strip() for line in plot_data_flow.splitlines()]

    separate_line = next(
        line for line in plot_contract_lines if line.startswith("- `--separate` switches plot output")
    )
    stem_line = next(line for line in plot_contract_lines if "source file stem" in line)
    exclusive_line = next(line for line in plot_contract_lines if "mutually exclusive" in line)
    trimming_line = next(line for line in plot_contract_lines if "batch preprocessing" in line)
    assert plot_contract_lines.index(separate_line) < plot_contract_lines.index(stem_line)
    assert plot_contract_lines.index(stem_line) < plot_contract_lines.index(exclusive_line)
    assert plot_contract_lines.index(exclusive_line) < plot_contract_lines.index(trimming_line)

    data_flow_line = next(line for line in plot_data_flow_lines if "shared preprocessing" in line)
    combined_line = next(line for line in plot_data_flow_lines if "one image per input file" in line)
    assert "shared preprocessing" in data_flow_line
    assert "one image per input file" in combined_line
    assert "figure size validation" in architecture
    assert "1500x900" in architecture
    assert "300..6000" in architecture
    assert "More Options" in architecture
    assert "incompatible with filename override / `--output`" in architecture
    assert "shared batch preprocessing reused by plot outputs" in architecture
    assert "Public plot docs must also describe the `--separate` mode" in development_notes
    assert "pixel-based output image size controls" in development_notes


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
