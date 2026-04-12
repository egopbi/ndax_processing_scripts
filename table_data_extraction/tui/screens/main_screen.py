from __future__ import annotations

from pathlib import Path
import re
import threading

from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import (
    Button,
    ContentSwitcher,
    Input,
    Label,
    Select,
    Static,
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
from table_data_extraction.tui.screens.advanced_options_screen import (
    AdvancedOptionsResult,
    AdvancedOptionsScreen,
    AdvancedOptionsState,
)
from table_data_extraction.tui.screens.manage_files_screen import ManageFilesScreen
from table_data_extraction.tui.widgets.file_list import FileList


class MainScreen(Screen[None]):
    BINDINGS = [
        ("f5", "run_active", "Run"),
        ("f6", "exit_app", "Exit"),
        ("f8", "open_settings", "Settings"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._advanced_state = {
            "plot": AdvancedOptionsState(mode="plot"),
            "table": AdvancedOptionsState(mode="table"),
        }

    def compose(self):
        with Vertical(id="main-shell"):
            with Horizontal(id="main-top-bar", classes="surface-box"):
                with Vertical(id="main-brand"):
                    yield Label("NDAX Processor", id="main-title")
                    yield Label("by eeee_gorka", id="main-subtitle")
                yield Static("", classes="spacer")
                with Horizontal(id="main-top-actions", classes="top-actions"):
                    yield Button(
                        "Settings",
                        id="open-settings",
                        classes="top-action-button",
                    )
                    yield Button("Exit", id="exit-app", classes="top-action-button")
            with Vertical(id="main-body"):
                with VerticalScroll(id="main-scroll"):
                    with Vertical(id="output-folder-section", classes="section-shell"):
                        yield Label("Output folder", classes="section-title")
                        with Vertical(id="output-folder-row"):
                            yield Button(
                                "Select output folder",
                                id="select-output-dir",
                            )
                            yield Static(
                                "",
                                id="current-output-dir",
                                classes="path-value",
                            )
                    with Vertical(id="files-section", classes="section-shell"):
                        yield Label("Files", classes="section-title")
                        with Horizontal(id="shared-file-actions"):
                            yield Button("Add Files", id="shared-add-files")
                            yield Button("Remove...", id="shared-manage-files")
                            yield Button("Clear Files", id="shared-clear-files")
                        yield FileList(
                            id="shared-files",
                            classes="file-list",
                            allow_remove_buttons=False,
                        )
                    with Vertical(id="mode-section", classes="section-shell"):
                        yield Label("Mode", id="mode-title", classes="section-title")
                        yield Select(
                            [
                                ("Plot", "plot"),
                                ("Comparison Table", "table"),
                            ],
                            value="plot",
                            allow_blank=False,
                            id="mode-select",
                        )
                    with Vertical(
                        id="parameters-section",
                        classes="section-shell",
                    ):
                        yield Label("Parameters", classes="section-title")
                        with ContentSwitcher(initial="plot-form", id="mode-forms"):
                            with Vertical(id="plot-form", classes="mode-form"):
                                yield Static(
                                    "Select NDAX files to enable column selectors.",
                                    id="plot-column-helper",
                                    classes="attention-box",
                                )
                                with Vertical(id="plot-column-controls"):
                                    with Horizontal(classes="field-grid-row"):
                                        yield Label(
                                            "Y column",
                                            classes="column-label",
                                        )
                                        yield Select(
                                            [],
                                            prompt="Choose Y column",
                                            disabled=True,
                                            id="plot-y-column",
                                            compact=True,
                                        )
                                    with Horizontal(classes="field-grid-row"):
                                        yield Label(
                                            "X column",
                                            classes="column-label",
                                        )
                                        yield Select(
                                            [],
                                            prompt="Choose X column",
                                            disabled=True,
                                            id="plot-x-column",
                                            compact=True,
                                        )
                                with Horizontal(classes="inline-input-row"):
                                    yield Input(placeholder="X min", id="plot-x-min")
                                    yield Input(placeholder="X max", id="plot-x-max")
                                with Horizontal(classes="inline-input-row"):
                                    yield Input(placeholder="Y min", id="plot-y-min")
                                    yield Input(placeholder="Y max", id="plot-y-max")
                                with Horizontal(classes="secondary-actions"):
                                    yield Button(
                                        "More Options...",
                                        id="plot-more-options",
                                    )
                            with Vertical(id="table-form", classes="mode-form"):
                                yield Static(
                                    "Select NDAX files to enable column selectors.",
                                    id="table-column-helper",
                                    classes="attention-box",
                                )
                                with Vertical(id="table-column-controls"):
                                    with Horizontal(classes="field-grid-row"):
                                        yield Label(
                                            "Y column",
                                            classes="column-label",
                                        )
                                        yield Select(
                                            [],
                                            prompt="Choose Y column",
                                            disabled=True,
                                            id="table-y-column",
                                            compact=True,
                                        )
                                    with Horizontal(classes="field-grid-row"):
                                        yield Label(
                                            "X column",
                                            classes="column-label",
                                        )
                                        yield Select(
                                            [],
                                            prompt="Choose X column",
                                            disabled=True,
                                            id="table-x-column",
                                            compact=True,
                                        )
                                yield Input(
                                    placeholder="Anchor X values, space or comma separated",
                                    id="table-anchor-x",
                                )
                                with Horizontal(classes="secondary-actions"):
                                    yield Button(
                                        "More Options...",
                                        id="table-more-options",
                                    )
            with Horizontal(id="main-bottom-bar", classes="surface-box"):
                yield Static("Ready", id="run-status")
                yield Static("", classes="spacer")
                with Horizontal(id="main-bottom-actions"):
                    yield Button("Run", variant="success", id="run-active")

    @property
    def current_mode(self) -> str:
        value = self.query_one("#mode-select", Select).value
        return "table" if value == "table" else "plot"

    @property
    def active_file_list(self) -> FileList:
        return self.query_one("#shared-files", FileList)

    def _column_state_widgets_for_mode(
        self, mode: str
    ) -> tuple[Static, Vertical, Select, Select]:
        if mode == "table":
            return (
                self.query_one("#table-column-helper", Static),
                self.query_one("#table-column-controls", Vertical),
                self.query_one("#table-y-column", Select),
                self.query_one("#table-x-column", Select),
            )
        return (
            self.query_one("#plot-column-helper", Static),
            self.query_one("#plot-column-controls", Vertical),
            self.query_one("#plot-y-column", Select),
            self.query_one("#plot-x-column", Select),
        )

    def _set_column_state(
        self,
        mode: str,
        *,
        helper_text: str | None,
        show_controls: bool,
    ) -> None:
        helper, controls, _, _ = self._column_state_widgets_for_mode(mode)
        helper.display = helper_text is not None
        if helper_text is not None:
            helper.update(helper_text)
        controls.display = show_controls

    def refresh_state_from_app(self) -> None:
        output_dir = getattr(self.app, "current_output_dir", None)
        self.query_one("#current-output-dir", Static).update(
            "" if output_dir is None else str(output_dir)
        )

    def _log(self, message: str) -> None:
        self.query_one("#run-status", Static).update(message)

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

    def _refresh_column_selects(self, mode: str, paths: tuple[Path, ...]) -> None:
        try:
            columns = self._collect_columns(paths)
        except Exception as error:
            self._log(f"Failed to load columns for {mode}: {error}")
            self._set_column_state(
                mode,
                helper_text="Failed to load column names.",
                show_controls=False,
            )
            return

        _, controls, y_select, x_select = self._column_state_widgets_for_mode(mode)
        if not paths:
            self._set_column_state(
                mode,
                helper_text="Select NDAX files to enable column selectors.",
                show_controls=False,
            )
            y_select.set_options([])
            x_select.set_options([])
            y_select.disabled = True
            x_select.disabled = True
            return

        if not columns:
            self._set_column_state(
                mode,
                helper_text="No common columns found in the selected files.",
                show_controls=False,
            )
            y_select.set_options([])
            x_select.set_options([])
            y_select.disabled = True
            x_select.disabled = True
            return

        self._set_column_state(mode, helper_text=None, show_controls=True)
        self._apply_select_options(y_select, columns=columns, preferred="Voltage")
        self._apply_select_options(x_select, columns=columns, preferred="Time")
        controls.display = True

    def _parse_labels(self, value: str) -> tuple[str, ...] | None:
        labels = tuple(item.strip() for item in value.split(",") if item.strip())
        return labels or None

    def _resolve_output_override(
        self,
        value: str,
        *,
        enforced_suffix: str | None = None,
    ) -> Path | None:
        stripped = value.strip()
        if not stripped:
            return None
        candidate = Path(stripped)
        if candidate.is_absolute() or candidate.parent != Path("."):
            resolved = candidate
        else:
            resolved = self.app.current_output_dir / candidate

        if enforced_suffix is not None:
            resolved = resolved.with_suffix(enforced_suffix)
        return resolved

    def _parse_anchor_x(self, value: str) -> tuple[float, ...]:
        anchors = tuple(
            float(item) for item in re.split(r"[,\s]+", value.strip()) if item
        )
        if not anchors:
            raise ValueError("Anchor X must contain at least one value.")
        return anchors

    def _selected_health_file(self) -> Path:
        if not self.active_file_list.paths:
            raise ValueError("Select at least one NDAX file first.")
        return self.active_file_list.paths[0]

    def _build_active_command(self):
        mode = self.current_mode
        files = self.active_file_list.paths
        if mode == "table":
            advanced = self._advanced_state["table"]
            return build_table_command(
                TableRunConfig(
                    files=files,
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
                    labels=self._parse_labels(advanced.labels),
                    output_path=self._resolve_output_override(
                        advanced.output_override
                    ),
                ),
                output_dir=self.app.current_output_dir,
            )

        advanced = self._advanced_state["plot"]
        return build_plot_command(
            PlotRunConfig(
                files=files,
                y_column=self._selected_select_value(
                    self.query_one("#plot-y-column", Select),
                    "Y",
                ),
                x_column=self._selected_select_value(
                    self.query_one("#plot-x-column", Select),
                    "X",
                ),
                labels=self._parse_labels(advanced.labels),
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
                    advanced.output_override,
                    enforced_suffix=".jpg",
                ),
            ),
            output_dir=self.app.current_output_dir,
        )

    def _parse_optional_float(self, value: str) -> float | None:
        stripped = value.strip()
        if not stripped:
            return None
        return float(stripped)

    def _run_command_in_thread(
        self,
        command,
        cancel_event: threading.Event,
    ) -> None:
        self.app.session_state.last_command_preview = " ".join(command.argv)
        self.app.call_from_thread(self.refresh_state_from_app)
        self.app.call_from_thread(
            self._log,
            f"Running: {' '.join(command.argv)}",
        )

        def _capture_output(chunk: StreamChunk) -> None:
            text = chunk.text.rstrip()
            if text:
                self.app.call_from_thread(self._log, f"[{chunk.stream}] {text}")

        result = run_subprocess_command(
            command,
            on_output=_capture_output,
            cancel_event=cancel_event,
        )
        self.app.call_from_thread(self._finish_command, result)

    def _launch_subprocess_command(self, command) -> None:
        if self.app.session_state.is_running:
            self._log("A command is already running.")
            return

        self.app.session_state.is_running = True
        self.app._cancel_event = threading.Event()
        self.app.session_state.last_command_preview = " ".join(command.argv)

        thread = threading.Thread(
            target=self._run_command_in_thread,
            args=(command, self.app._cancel_event),
            daemon=True,
        )
        try:
            thread.start()
        except Exception:
            self.app.session_state.is_running = False
            self.app._cancel_event = None
            raise

    def _finish_command(self, result) -> None:
        self.app.session_state.is_running = False
        self.app.session_state.last_output_path = result.command.output_path
        self._log(f"Command finished with exit code {result.returncode}.")
        self.app._cancel_event = None
        if getattr(self.app, "_pending_exit", False):
            self.app._pending_exit = False
            self.app.exit()

    def _apply_selected_files(self, selected: tuple[Path, ...]) -> None:
        self.active_file_list.add_paths(selected)

    def _on_file_list_paths_changed(self, paths: tuple[Path, ...]) -> None:
        self._refresh_column_selects("plot", paths)
        self._refresh_column_selects("table", paths)

    def _choose_files_in_thread(self) -> None:
        selected = choose_ndax_files(initial_dir=self.app.current_output_dir)
        if selected:
            self.app.call_from_thread(
                self._apply_selected_files,
                tuple(selected),
            )

    def _choose_output_directory_in_thread(self) -> None:
        selected = choose_output_directory(initial_dir=self.app.current_output_dir)
        if selected is not None:
            self.app.call_from_thread(self.app.set_output_dir, selected)
            self.app.call_from_thread(self.refresh_state_from_app)

    def _manage_files_closed(self, result: tuple[Path, ...] | None) -> None:
        if result is None:
            return
        self.active_file_list.set_paths(result)

    def _advanced_options_closed(
        self,
        result: AdvancedOptionsResult | None,
    ) -> None:
        if result is None:
            return

        self._advanced_state[result.state.mode] = result.state
        if result.action == "health-check":
            self._run_health_check()
            return
        self._log("Advanced options updated.")

    def _open_advanced_options(self) -> None:
        mode = self.current_mode
        state = self._advanced_state[mode]
        self.app.push_screen(
            AdvancedOptionsScreen(
                mode=mode,
                labels=state.labels,
                output_override=state.output_override,
            ),
            self._advanced_options_closed,
        )

    def _sync_mode_form(self) -> None:
        form_id = "table-form" if self.current_mode == "table" else "plot-form"
        self.query_one("#mode-forms", ContentSwitcher).current = form_id

    def action_open_settings(self) -> None:
        self.app.action_open_settings()

    def action_run_active(self) -> None:
        self._start_run()

    def action_exit_app(self) -> None:
        self.app.action_exit_app()

    def _start_run(self) -> None:
        try:
            command = self._build_active_command()
        except Exception as error:
            self._log(f"Build failed: {error}")
            return

        self._launch_subprocess_command(command)

    def _run_health_check(self) -> None:
        try:
            command = build_health_check_command(
                HealthCheckRunConfig(file=self._selected_health_file())
            )
        except Exception as error:
            self._log(f"Health check failed: {error}")
            return

        self._launch_subprocess_command(command)

    def on_mount(self) -> None:
        self.refresh_state_from_app()
        file_list = self.query_one("#shared-files", FileList)
        file_list.paths_changed_callback = self._on_file_list_paths_changed
        self._on_file_list_paths_changed(file_list.paths)
        self._sync_mode_form()

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "mode-select":
            self._sync_mode_form()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id == "shared-add-files":
            threading.Thread(
                target=self._choose_files_in_thread,
                daemon=True,
            ).start()
            return
        if button_id == "shared-manage-files":
            self.app.push_screen(
                ManageFilesScreen(self.active_file_list.paths),
                self._manage_files_closed,
            )
            return
        if button_id == "shared-clear-files":
            self.active_file_list.clear_paths()
            return
        if button_id == "plot-more-options":
            self.query_one("#mode-select", Select).value = "plot"
            self._sync_mode_form()
            self._open_advanced_options()
            return
        if button_id == "table-more-options":
            self.query_one("#mode-select", Select).value = "table"
            self._sync_mode_form()
            self._open_advanced_options()
            return
        if button_id == "select-output-dir":
            threading.Thread(
                target=self._choose_output_directory_in_thread,
                daemon=True,
            ).start()
            return
        if button_id == "run-active":
            self._start_run()
            return
        if button_id == "open-settings":
            self.app.action_open_settings()
            return
        if button_id == "exit-app":
            self.app.action_exit_app()
