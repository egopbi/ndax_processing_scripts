from pathlib import Path
import sys
import threading

from table_data_extraction.tui.command_builder import (
    build_health_check_command,
    build_plot_command,
    build_table_command,
)
from table_data_extraction.tui.models import (
    HealthCheckRunConfig,
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
        str(Path("scripts/plot_ndax.py")),
    )
    assert "--files" in command.argv
    assert "--output" in command.argv
    assert command.output_path is not None
    assert command.output_path.parent == tmp_path
    assert command.argv[-1] == str(command.output_path)


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
        str(Path("scripts/build_comparison_table.py")),
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
        str(Path("scripts/health_check_ndax.py")),
        "examples/example1_1.ndax",
    )


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
