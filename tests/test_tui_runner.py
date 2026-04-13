from pathlib import Path
import sys
import threading

import pytest

from table_data_extraction.tui.command_builder import (
    build_convert_command,
    build_health_check_command,
    build_plot_command,
    build_table_command,
)
from table_data_extraction.tui.models import (
    DEFAULT_PLOT_OUTPUT_HEIGHT_PX,
    DEFAULT_PLOT_OUTPUT_WIDTH_PX,
    ConvertRunConfig,
    HealthCheckRunConfig,
    MAX_PLOT_OUTPUT_DIMENSION_PX,
    MIN_PLOT_OUTPUT_DIMENSION_PX,
    PlotRunConfig,
    SubprocessCommand,
    TableRunConfig,
)
from table_data_extraction.tui.runner import run_subprocess_command


def test_build_plot_command_uses_overridden_output_dir(tmp_path: Path) -> None:
    command = build_plot_command(
        PlotRunConfig(
            files=(Path("examples/example1_1.ndax"),),
            y_column="Voltage",
        ),
        output_dir=tmp_path,
        python_executable="python-test",
    )

    assert command.mode == "plot"
    assert command.argv[:2] == (
        "python-test",
        "-u",
    )
    assert command.argv[2:4] == (
        str(Path("scripts/plot_ndax.py")),
        "--files",
    )
    assert "--files" in command.argv
    assert command.argv[command.argv.index("--output-width-px") + 1] == str(
        DEFAULT_PLOT_OUTPUT_WIDTH_PX
    )
    assert command.argv[command.argv.index("--output-height-px") + 1] == str(
        DEFAULT_PLOT_OUTPUT_HEIGHT_PX
    )
    assert "--output" in command.argv
    assert command.output_path is not None
    assert command.output_path.parent == tmp_path
    assert command.argv[-1] == str(command.output_path)


def test_build_plot_command_includes_separate_flag() -> None:
    command = build_plot_command(
        PlotRunConfig(
            files=(Path("examples/example1_1.ndax"),),
            y_column="Voltage",
            separate=True,
        ),
        python_executable="python-test",
    )

    assert command.mode == "plot"
    assert "--separate" in command.argv


def test_build_plot_command_accepts_custom_output_dimensions() -> None:
    command = build_plot_command(
        PlotRunConfig(
            files=(Path("examples/example1_1.ndax"),),
            y_column="Voltage",
            output_width_px=1800,
            output_height_px=1200,
        ),
        python_executable="python-test",
    )

    width_index = command.argv.index("--output-width-px")
    height_index = command.argv.index("--output-height-px")
    assert command.argv[width_index + 1] == "1800"
    assert command.argv[height_index + 1] == "1200"


@pytest.mark.parametrize(
    ("field", "value", "match"),
    [
        (
            "output_width_px",
            MIN_PLOT_OUTPUT_DIMENSION_PX - 1,
            rf"Output width must be between {MIN_PLOT_OUTPUT_DIMENSION_PX} and {MAX_PLOT_OUTPUT_DIMENSION_PX} pixels\.",
        ),
        (
            "output_height_px",
            MAX_PLOT_OUTPUT_DIMENSION_PX + 1,
            rf"Output height must be between {MIN_PLOT_OUTPUT_DIMENSION_PX} and {MAX_PLOT_OUTPUT_DIMENSION_PX} pixels\.",
        ),
    ],
)
def test_build_plot_command_rejects_unreasonable_output_dimensions(
    field: str,
    value: int,
    match: str,
) -> None:
    kwargs = {"output_width_px": None, "output_height_px": None}
    kwargs[field] = value

    try:
        build_plot_command(
            PlotRunConfig(
                files=(Path("examples/example1_1.ndax"),),
                y_column="Voltage",
                **kwargs,
            )
        )
    except ValueError as error:
        assert match.replace(r"\.", ".").casefold() in str(error).casefold()
    else:
        raise AssertionError("Expected output dimension validation failure.")


def test_build_plot_command_drops_output_when_separate_enabled(tmp_path: Path) -> None:
    command = build_plot_command(
        PlotRunConfig(
            files=(Path("examples/example1_1.ndax"),),
            y_column="Voltage",
            separate=True,
            output_path=tmp_path / "custom.jpg",
        ),
        output_dir=tmp_path,
        python_executable="python-test",
    )

    assert "--separate" in command.argv
    assert "--output" not in command.argv
    assert command.output_path is None


def test_build_table_command_includes_anchor_x_and_labels(tmp_path: Path) -> None:
    command = build_table_command(
        TableRunConfig(
            files=(
                Path("examples/example1_1.ndax"),
                Path("examples/example2_2.ndax"),
            ),
            y_column="Voltage",
            anchor_x=(0.5, 1.0),
            labels=("a", "b"),
        ),
        output_dir=tmp_path,
        python_executable="python-test",
    )

    assert command.mode == "table"
    assert command.argv[:2] == (
        "python-test",
        "-u",
    )
    assert command.argv[2:4] == (
        str(Path("scripts/build_comparison_table.py")),
        "--files",
    )
    anchor_index = command.argv.index("--anchor-x")
    assert command.argv[anchor_index + 1:anchor_index + 3] == ("0.5", "1.0")
    labels_index = command.argv.index("--labels")
    assert command.argv[labels_index + 1:labels_index + 3] == ("a", "b")
    assert command.output_path is not None
    assert command.output_path.parent == tmp_path


def test_build_health_check_command_targets_script() -> None:
    command = build_health_check_command(
        HealthCheckRunConfig(file=Path("examples/example1_1.ndax")),
        python_executable="python-test",
    )

    assert command.mode == "health-check"
    assert command.argv == (
        "python-test",
        "-u",
        str(Path("scripts/health_check_ndax.py")),
        "examples/example1_1.ndax",
    )


def test_build_convert_command_passes_columns_and_output_dir(tmp_path: Path) -> None:
    command = build_convert_command(
        ConvertRunConfig(
            files=(
                Path("examples/example1_1.ndax"),
                Path("examples/example2_2.ndax"),
            ),
            columns=("Time", "Voltage", "Current(mA)"),
        ),
        output_dir=tmp_path,
        python_executable="python-test",
    )

    assert command.mode == "convert"
    assert command.argv[:2] == ("python-test", "-u")
    assert command.argv[2:4] == (str(Path("scripts/convert_ndax.py")), "--files")
    files_index = command.argv.index("--files")
    assert command.argv[files_index + 1:files_index + 3] == (
        "examples/example1_1.ndax",
        "examples/example2_2.ndax",
    )
    columns_index = command.argv.index("--columns")
    assert command.argv[columns_index + 1:columns_index + 4] == (
        "Time",
        "Voltage",
        "Current(mA)",
    )
    assert command.argv[-2:] == ("--output-dir", str(tmp_path))
    assert command.output_path is None


def test_build_plot_command_rejects_mismatched_labels() -> None:
    try:
        build_plot_command(
            PlotRunConfig(
                files=(
                    Path("examples/example1_1.ndax"),
                    Path("examples/example2_2.ndax"),
                ),
                y_column="Voltage",
                labels=("single",),
            )
        )
    except ValueError as error:
        assert "labels" in str(error).lower()
    else:
        raise AssertionError("Expected label validation failure.")


def test_build_convert_command_rejects_empty_columns() -> None:
    try:
        build_convert_command(
            ConvertRunConfig(
                files=(Path("examples/example1_1.ndax"),),
                columns=(),
            )
        )
    except ValueError as error:
        assert "column" in str(error).lower()
    else:
        raise AssertionError("Expected column validation failure.")


def test_run_subprocess_command_captures_stdout_and_stderr() -> None:
    command = SubprocessCommand(
        mode="health-check",
        argv=(
            sys.executable,
            "-c",
            (
                "import sys; "
                "print('hello'); "
                "print('problem', file=sys.stderr)"
            ),
        ),
        cwd=Path.cwd(),
    )
    chunks: list[tuple[str, str]] = []

    result = run_subprocess_command(
        command,
        on_output=lambda chunk: chunks.append((chunk.stream, chunk.text)),
    )

    assert result.returncode == 0
    assert result.stdout == "hello\n"
    assert result.stderr == "problem\n"
    assert ("stdout", "hello\n") in chunks
    assert ("stderr", "problem\n") in chunks


def test_run_subprocess_command_honors_cancellation() -> None:
    cancel_event = threading.Event()
    command = SubprocessCommand(
        mode="health-check",
        argv=(
            sys.executable,
            "-c",
            (
                "import sys, time; "
                "print('start'); "
                "sys.stdout.flush(); "
                "time.sleep(5)"
            ),
        ),
        cwd=Path.cwd(),
    )
    seen_chunks: list[str] = []

    def _capture_and_cancel(chunk) -> None:
        seen_chunks.append(chunk.text)
        cancel_event.set()

    result = run_subprocess_command(
        command,
        on_output=_capture_and_cancel,
        cancel_event=cancel_event,
    )

    assert seen_chunks == ["start\n"]
    assert result.was_cancelled is True
