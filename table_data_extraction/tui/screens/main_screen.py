from __future__ import annotations

from pathlib import Path
import threading

from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import (
    Button,
    Collapsible,
    Input,
    Label,
    Log,
    Select,
    Static,
    TabbedContent,
    TabPane,
)

from table_data_extraction.reader import list_columns
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
        ("f6", "exit_app", "Exit"),
        ("f8", "open_settings", "Settings"),
    ]

    def compose(self):
        with Horizontal(id="main-top-bar"):
            with Vertical(id="main-title-block"):
                yield Label("NDAX Terminal UI", id="main-title")
                yield Static("", id="current-output-dir")
            yield Static("", classes="spacer")
            with Horizontal(id="main-top-actions"):
                yield Button("Select Output Folder...", id="select-output-dir")
                yield Button("Settings", id="open-settings")
                yield Button("Exit", variant="error", id="exit-app")
        with TabbedContent(initial="plot-tab", id="workflow-tabs"):
            with TabPane("Plot", id="plot-tab"):
                with Vertical(id="plot-pane"):
                    with Horizontal():
                        yield Button("Add Files...", id="plot-add-files")
                        yield Button("Clear Files", id="plot-clear-files")
                    yield FileList(id="plot-files", classes="file-list")
                    yield Select(
                        [],
                        prompt="Add files first",
                        disabled=True,
                        id="plot-y-column",
                    )
                    yield Select(
                        [],
                        prompt="Add files first",
                        disabled=True,
                        id="plot-x-column",
                    )
                    with Collapsible(
                        title="Advanced",
                        collapsed=True,
                        collapsed_symbol=">",
                        expanded_symbol="v",
                        id="plot-advanced",
                    ):
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
                    yield FileList(id="table-files", classes="file-list")
                    yield Select(
                        [],
                        prompt="Add files first",
                        disabled=True,
                        id="table-y-column",
                    )
                    yield Select(
                        [],
                        prompt="Add files first",
                        disabled=True,
                        id="table-x-column",
                    )
                    yield Input(
                        placeholder="Anchor X values, comma separated",
                        id="table-anchor-x",
                    )
                    with Collapsible(
                        title="Advanced",
                        collapsed=True,
                        collapsed_symbol=">",
                        expanded_symbol="v",
                        id="table-advanced",
                    ):
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
        yield Log(id="run-log")
        with Horizontal(id="main-bottom-bar"):
            yield Static("", classes="spacer")
            with Horizontal(id="main-bottom-actions"):
                yield Button("Run", variant="success", id="run-active")

    @property
    def current_tab(self) -> str:
        return self.query_one("#workflow-tabs", TabbedContent).active

    @property
    def active_file_list(self) -> FileList:
        if self.current_tab == "table-tab":
            return self.query_one("#table-files", FileList)
        return self.query_one("#plot-files", FileList)

    def _column_selects_for_tab(self, tab_id: str) -> tuple[Select, Select]:
        if tab_id == "table-tab":
            return (
                self.query_one("#table-y-column", Select),
                self.query_one("#table-x-column", Select),
            )
        return (
            self.query_one("#plot-y-column", Select),
            self.query_one("#plot-x-column", Select),
        )

    def refresh_state_from_app(self) -> None:
        output_dir = getattr(self.app, "current_output_dir", None)
        self.query_one("#current-output-dir", Static).update(
            f"Output directory: {output_dir}"
        )

    def _log(self, message: str) -> None:
        self.query_one("#run-log", Log).write_line(message)

    def _selected_select_value(self, select: Select, field_name: str) -> str:
        value = select.value
        if value == Select.NULL:
            raise ValueError(f"Select a {field_name} column first.")
        return str(value)

    def _collect_columns(self, paths: tuple[Path, ...]) -> tuple[str, ...]:
        if not paths:
            return ()

        columns_by_file = [list_columns(path) for path in paths]
        if not columns_by_file:
            return ()

        first_file_columns = columns_by_file[0]
        common_columns = [
            column
            for column in first_file_columns
            if all(column in set(columns) for columns in columns_by_file[1:])
        ]
        return tuple(common_columns)

    def _apply_select_options(
        self,
        select: Select,
        *,
        columns: tuple[str, ...],
        preferred: str,
    ) -> None:
        if not columns:
            select.set_options([])
            select.value = Select.NULL
            select.disabled = True
            return

        current_value = select.value
        select.set_options([(column, column) for column in columns])
        select.disabled = False
        if current_value != Select.NULL and str(current_value) in columns:
            select.value = str(current_value)
            return
        select.value = preferred if preferred in columns else columns[0]

    def _refresh_column_selects(self, tab_id: str, paths: tuple[Path, ...]) -> None:
        try:
            columns = self._collect_columns(paths)
        except Exception as error:
            self._log(f"Failed to load columns for {tab_id}: {error}")
            columns = ()

        y_select, x_select = self._column_selects_for_tab(tab_id)
        self._apply_select_options(y_select, columns=columns, preferred="Voltage")
        self._apply_select_options(x_select, columns=columns, preferred="Time")

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
                    y_column=self._selected_select_value(
                        self.query_one("#table-y-column", Select),
                        "Y",
                    ),
                    anchor_x=self._parse_anchor_x(
                        self.query_one("#table-anchor-x", Input).value
                    ),
                    x_column=self._selected_select_value(
                        self.query_one("#table-x-column", Select),
                        "X",
                    ),
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
                y_column=self._selected_select_value(
                    self.query_one("#plot-y-column", Select),
                    "Y",
                ),
                x_column=self._selected_select_value(
                    self.query_one("#plot-x-column", Select),
                    "X",
                ),
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
        self.app.call_from_thread(
            self._log,
            f"Running: {' '.join(command.argv)}",
        )

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
        self._log(f"Command finished with exit code {result.returncode}.")
        self.app._cancel_event = None
        if getattr(self.app, "_pending_exit", False):
            self.app._pending_exit = False
            self.app.exit()

    def _apply_selected_files(
        self,
        tab_id: str,
        selected: tuple[Path, ...],
    ) -> None:
        if tab_id == "table-tab":
            self.query_one("#table-files", FileList).add_paths(selected)
        else:
            self.query_one("#plot-files", FileList).add_paths(selected)

    def _choose_files_in_thread(self, tab_id: str) -> None:
        selected = choose_ndax_files(initial_dir=self.app.current_output_dir)
        if selected:
            self.app.call_from_thread(
                self._apply_selected_files,
                tab_id,
                tuple(selected),
            )

    def _choose_output_directory_in_thread(self) -> None:
        selected = choose_output_directory(initial_dir=self.app.current_output_dir)
        if selected is not None:
            self.app.call_from_thread(self.app.set_output_dir, selected)
            self.app.call_from_thread(self.refresh_state_from_app)

    def action_open_settings(self) -> None:
        self.app.action_open_settings()

    def action_run_active(self) -> None:
        self._start_run()

    def action_exit_app(self) -> None:
        self.app.action_exit_app()

    def _start_run(self) -> None:
        if self.app.session_state.is_running:
            self._log("A command is already running.")
            return

        try:
            command = self._build_active_command()
        except Exception as error:
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
        plot_files = self.query_one("#plot-files", FileList)
        table_files = self.query_one("#table-files", FileList)
        plot_files.paths_changed_callback = lambda paths: self._refresh_column_selects(
            "plot-tab",
            paths,
        )
        table_files.paths_changed_callback = lambda paths: self._refresh_column_selects(
            "table-tab",
            paths,
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id in {"plot-add-files", "table-add-files"}:
            tab_id = self.current_tab
            threading.Thread(
                target=self._choose_files_in_thread,
                args=(tab_id,),
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
        if button_id == "open-settings":
            self.app.action_open_settings()
            return
        if button_id == "exit-app":
            self.app.action_exit_app()
            return
        if button_id in {"plot-health-check", "table-health-check"}:
            self._run_health_check()
