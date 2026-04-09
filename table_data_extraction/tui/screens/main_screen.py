from __future__ import annotations

from pathlib import Path
import threading

from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import (
    Button,
    Collapsible,
    Footer,
    Header,
    Input,
    Label,
    Log,
    Static,
    TabbedContent,
    TabPane,
)

from table_data_extraction.tui.command_builder import (
    build_health_check_command,
    build_plot_command,
    build_table_command,
)
from table_data_extraction.tui.dialogs import (
    choose_ndax_files,
    choose_output_directory,
)
from table_data_extraction.tui.models import (
    HealthCheckRunConfig,
    PlotRunConfig,
    StreamChunk,
    TableRunConfig,
)
from table_data_extraction.tui.runner import run_subprocess_command
from table_data_extraction.tui.widgets.file_list import FileList


class MainScreen(Screen[None]):
    BINDINGS = [
        ("f5", "run_active", "Run"),
        ("f6", "cancel_run", "Cancel"),
        ("f8", "open_settings", "Settings"),
    ]

    def compose(self):
        yield Header()
        yield Footer()
        yield Label("NDAX Terminal UI", id="main-title")
        yield Static("", id="current-output-dir")
        with Horizontal(id="main-actions"):
            yield Button("Select Output Folder...", id="select-output-dir")
            yield Button("Settings", id="open-settings")
            yield Button("Run", variant="success", id="run-active")
            yield Button("Cancel", variant="warning", id="cancel-run")
        with TabbedContent(initial="plot-tab", id="workflow-tabs"):
            with TabPane("Plot", id="plot-tab"):
                with Vertical(id="plot-pane"):
                    with Horizontal():
                        yield Button("Add Files...", id="plot-add-files")
                        yield Button("Clear Files", id="plot-clear-files")
                    yield FileList(id="plot-files")
                    yield Input(placeholder="Y column", value="Voltage", id="plot-y-column")
                    yield Input(placeholder="X column", value="Time", id="plot-x-column")
                    with Collapsible(title="Advanced", collapsed=True, id="plot-advanced"):
                        yield Input(placeholder="Labels, comma separated", id="plot-labels")
                        yield Input(placeholder="X min", id="plot-x-min")
                        yield Input(placeholder="X max", id="plot-x-max")
                        yield Input(placeholder="Y min", id="plot-y-min")
                        yield Input(placeholder="Y max", id="plot-y-max")
                        yield Input(
                            placeholder="Output filename override",
                            id="plot-output",
                        )
                        yield Button(
                            "Run Health Check",
                            variant="default",
                            id="plot-health-check",
                        )
            with TabPane("Comparison Table", id="table-tab"):
                with Vertical(id="table-pane"):
                    with Horizontal():
                        yield Button("Add Files...", id="table-add-files")
                        yield Button("Clear Files", id="table-clear-files")
                    yield FileList(id="table-files")
                    yield Input(placeholder="Y column", value="Voltage", id="table-y-column")
                    yield Input(
                        placeholder="Anchor X values, comma separated",
                        id="table-anchor-x",
                    )
                    yield Input(placeholder="X column", value="Time", id="table-x-column")
                    with Collapsible(title="Advanced", collapsed=True, id="table-advanced"):
                        yield Input(placeholder="Labels, comma separated", id="table-labels")
                        yield Input(
                            placeholder="Output filename override",
                            id="table-output",
                        )
                        yield Button(
                            "Run Health Check",
                            variant="default",
                            id="table-health-check",
                        )
        yield Static("Status: idle", id="run-status")
        yield Static("Command: ", id="command-preview")
        yield Static("Output: ", id="last-output-path")
        yield Log(id="run-log")

    @property
    def current_tab(self) -> str:
        return self.query_one("#workflow-tabs", TabbedContent).active

    @property
    def active_file_list(self) -> FileList:
        if self.current_tab == "table-tab":
            return self.query_one("#table-files", FileList)
        return self.query_one("#plot-files", FileList)

    def refresh_state_from_app(self) -> None:
        output_dir = getattr(self.app, "current_output_dir", None)
        self.query_one("#current-output-dir", Static).update(
            f"Output directory: {output_dir}"
        )
        command_preview = getattr(self.app, "session_state", None)
        if command_preview is not None:
            self.query_one("#command-preview", Static).update(
                f"Command: {command_preview.last_command_preview}"
            )

    def _log(self, message: str) -> None:
        self.query_one("#run-log", Log).write_line(message)

    def _set_status(self, message: str) -> None:
        self.query_one("#run-status", Static).update(f"Status: {message}")

    def _set_output_path(self, output_path: Path | None) -> None:
        label = "" if output_path is None else str(output_path)
        self.query_one("#last-output-path", Static).update(f"Output: {label}")

    def _parse_labels(self, value: str) -> tuple[str, ...] | None:
        labels = tuple(item.strip() for item in value.split(",") if item.strip())
        return labels or None

    def _resolve_output_override(self, value: str) -> Path | None:
        stripped = value.strip()
        if not stripped:
            return None
        candidate = Path(stripped)
        if candidate.is_absolute() or candidate.parent != Path("."):
            return candidate
        return self.app.current_output_dir / candidate

    def _parse_anchor_x(self, value: str) -> tuple[float, ...]:
        anchors = tuple(
            float(item.strip()) for item in value.split(",") if item.strip()
        )
        if not anchors:
            raise ValueError("Anchor X must contain at least one value.")
        return anchors

    def _selected_health_file(self) -> Path:
        if not self.active_file_list.paths:
            raise ValueError("Select at least one NDAX file first.")
        return self.active_file_list.paths[0]

    def _build_active_command(self):
        if self.current_tab == "table-tab":
            return build_table_command(
                TableRunConfig(
                    files=self.query_one("#table-files", FileList).paths,
                    y_column=self.query_one("#table-y-column", Input).value.strip(),
                    anchor_x=self._parse_anchor_x(
                        self.query_one("#table-anchor-x", Input).value
                    ),
                    x_column=self.query_one("#table-x-column", Input).value.strip()
                    or "Time",
                    labels=self._parse_labels(
                        self.query_one("#table-labels", Input).value
                    ),
                    output_path=self._resolve_output_override(
                        self.query_one("#table-output", Input).value
                    ),
                ),
                output_dir=self.app.current_output_dir,
            )

        return build_plot_command(
            PlotRunConfig(
                files=self.query_one("#plot-files", FileList).paths,
                y_column=self.query_one("#plot-y-column", Input).value.strip(),
                x_column=self.query_one("#plot-x-column", Input).value.strip()
                or "Time",
                labels=self._parse_labels(
                    self.query_one("#plot-labels", Input).value
                ),
                x_min=self._parse_optional_float(
                    self.query_one("#plot-x-min", Input).value
                ),
                x_max=self._parse_optional_float(
                    self.query_one("#plot-x-max", Input).value
                ),
                y_min=self._parse_optional_float(
                    self.query_one("#plot-y-min", Input).value
                ),
                y_max=self._parse_optional_float(
                    self.query_one("#plot-y-max", Input).value
                ),
                output_path=self._resolve_output_override(
                    self.query_one("#plot-output", Input).value
                ),
            ),
            output_dir=self.app.current_output_dir,
        )

    def _parse_optional_float(self, value: str) -> float | None:
        stripped = value.strip()
        if not stripped:
            return None
        return float(stripped)

    def _run_command_in_thread(self, command) -> None:
        self.app.session_state.is_running = True
        self.app._cancel_event = threading.Event()
        self.app.session_state.last_command_preview = " ".join(command.argv)
        self.app.call_from_thread(self.refresh_state_from_app)
        self.app.call_from_thread(self._set_status, "running")
        self.app.call_from_thread(self._set_output_path, command.output_path)

        def _capture_output(chunk: StreamChunk) -> None:
            self.app.call_from_thread(
                self._log,
                f"[{chunk.stream}] {chunk.text.rstrip()}",
            )

        result = run_subprocess_command(
            command,
            on_output=_capture_output,
            cancel_event=self.app._cancel_event,
        )
        self.app.call_from_thread(self._finish_command, result)

    def _finish_command(self, result) -> None:
        self.app.session_state.is_running = False
        self.app.session_state.last_output_path = result.command.output_path
        if result.command.output_path is not None:
            self._set_output_path(result.command.output_path)
        status = (
            f"cancelled ({result.returncode})"
            if result.was_cancelled
            else f"finished ({result.returncode})"
        )
        self._set_status(status)
        self._log(f"Command finished with exit code {result.returncode}.")

    def _choose_files_in_thread(self) -> None:
        selected = choose_ndax_files(initial_dir=self.app.current_output_dir)
        if selected:
            self.app.call_from_thread(self.active_file_list.add_paths, selected)

    def _choose_output_directory_in_thread(self) -> None:
        selected = choose_output_directory(initial_dir=self.app.current_output_dir)
        if selected is not None:
            self.app.call_from_thread(self.app.set_output_dir, selected)
            self.app.call_from_thread(self.refresh_state_from_app)

    def action_open_settings(self) -> None:
        self.app.action_open_settings()

    def action_run_active(self) -> None:
        self._start_run()

    def action_cancel_run(self) -> None:
        self.app.request_cancel()

    def _start_run(self) -> None:
        if self.app.session_state.is_running:
            self._log("A command is already running.")
            return

        try:
            command = self._build_active_command()
        except Exception as error:
            self._set_status(f"failed to start: {error}")
            self._log(f"Build failed: {error}")
            return

        thread = threading.Thread(
            target=self._run_command_in_thread,
            args=(command,),
            daemon=True,
        )
        thread.start()

    def _run_health_check(self) -> None:
        if self.app.session_state.is_running:
            self._log("A command is already running.")
            return

        try:
            command = build_health_check_command(
                HealthCheckRunConfig(file=self._selected_health_file())
            )
        except Exception as error:
            self._set_status(f"health check failed to start: {error}")
            self._log(f"Health check failed: {error}")
            return

        thread = threading.Thread(
            target=self._run_command_in_thread,
            args=(command,),
            daemon=True,
        )
        thread.start()

    def on_mount(self) -> None:
        self.refresh_state_from_app()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id in {"plot-add-files", "table-add-files"}:
            threading.Thread(
                target=self._choose_files_in_thread,
                daemon=True,
            ).start()
            return
        if button_id == "select-output-dir":
            threading.Thread(
                target=self._choose_output_directory_in_thread,
                daemon=True,
            ).start()
            return
        if button_id in {"plot-clear-files", "table-clear-files"}:
            self.active_file_list.clear_paths()
            return
        if button_id == "run-active":
            self._start_run()
            return
        if button_id == "cancel-run":
            self.app.request_cancel()
            return
        if button_id == "open-settings":
            self.app.action_open_settings()
            return
        if button_id in {"plot-health-check", "table-health-check"}:
            self._run_health_check()
