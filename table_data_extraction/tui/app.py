from __future__ import annotations

from pathlib import Path
import threading
from typing import Sequence

from textual.app import App

from table_data_extraction.tui.screens.main_screen import MainScreen
from table_data_extraction.tui.screens.settings_screen import SettingsScreen
from table_data_extraction.tui.settings_service import resolve_runtime_output_dir
from table_data_extraction.tui.state import AppSessionState


def _compact_path_text(value: str | Path | None, *, limit: int = 42) -> str:
    if value is None:
        return ""

    text = str(value)
    if len(text) <= limit:
        return text

    if limit <= 3:
        return "..."[:limit]

    return f"...{text[-(limit - 3):]}"


class NdaxTuiApp(App[None]):
    CSS = """
    Screen {
        layout: vertical;
    }

    #main-top-bar, #main-bottom-bar, #settings-top-bar, #settings-actions {
        height: auto;
    }

    #main-top-bar, #settings-top-bar {
        height: 4;
        padding: 0 1;
    }

    #plot-file-actions, #table-file-actions {
        height: auto;
        width: auto;
    }

    #settings-body, #settings-scroll {
        height: 1fr;
    }

    #run-log {
        height: 10;
        margin: 0 1 1 1;
        padding: 0 1;
        background: $panel;
    }

    Select {
        margin: 0 1 1 1;
        width: 1fr;
        border: none;
        background: $panel;
    }

    Input {
        margin: 0 1 1 1;
        border: none;
        background: $panel;
    }

    #current-output-dir, #settings-output-dir {
        height: 1;
        margin: 0 1;
        width: 1fr;
    }

    #settings-status {
        height: auto;
        margin: 0 1;
        width: 1fr;
    }

    #main-title-block, #settings-title-block {
        width: 1fr;
    }

    #main-top-row, #settings-top-row {
        height: auto;
    }

    .spacer {
        width: 1fr;
    }

    #main-top-actions, #main-bottom-actions, #settings-top-actions {
        width: auto;
        height: auto;
    }

    #main-bottom-bar {
        padding: 0 1 1 1;
    }

    #main-top-actions Button, #main-bottom-actions Button {
        margin-left: 1;
    }

    .file-list {
        background: $panel;
        padding: 0 1;
        margin: 0 1 1 1;
    }

    #settings-title, #main-title {
        margin: 0 1 0 1;
    }

    #settings-top-actions Button {
        margin-left: 1;
    }

    #settings-scroll {
        padding: 0 1 1 1;
    }

    #plot-column-helper, #table-column-helper {
        margin: 0 1 1 1;
        height: auto;
    }

    #plot-column-controls, #table-column-controls {
        display: none;
        margin: 0 1 1 1;
    }

    #plot-column-controls Horizontal, #table-column-controls Horizontal {
        height: auto;
    }

    .column-label {
        width: 12;
        margin: 0 1 0 0;
    }

    #settings-palette-section {
        height: auto;
        margin: 0 1 1 1;
    }

    #settings-palette-inputs {
        width: 1fr;
    }

    #settings-preview-panel {
        width: 38;
        margin-left: 1;
        background: $panel;
        padding: 0 1;
    }

    #settings-preview-title {
        margin: 0 0 1 0;
    }

    #settings-preview-panel PalettePreview {
        background: white;
        color: black;
        height: auto;
    }
    """

    BINDINGS = [
        ("f8", "open_settings", "Settings"),
        ("f5", "run_active", "Run"),
        ("f6", "exit_app", "Exit"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.session_state = AppSessionState()
        self._cancel_event: threading.Event | None = None
        self._pending_exit = False
        self._load_runtime_settings()

    def _load_runtime_settings(self) -> None:
        from table_data_extraction.project_config import reload_project_config

        config = reload_project_config()
        self.current_config = config
        self.current_output_dir = resolve_runtime_output_dir(config)
        self.session_state.output_dir = self.current_output_dir

    def on_mount(self) -> None:
        self.push_screen(MainScreen())

    def action_open_settings(self) -> None:
        self.push_screen(SettingsScreen(), self._settings_closed)

    def action_run_active(self) -> None:
        if isinstance(self.screen, MainScreen):
            self.screen.action_run_active()

    def action_exit_app(self) -> None:
        if self.session_state.is_running:
            self._pending_exit = True
            self.request_cancel()
            return
        self.exit()

    def _settings_closed(self, result: dict[str, object] | None) -> None:
        if result is None:
            return
        self.current_config = result
        self.current_output_dir = resolve_runtime_output_dir(result)
        self.session_state.output_dir = self.current_output_dir
        if isinstance(self.screen, MainScreen):
            self.screen.refresh_state_from_app()

    def set_output_dir(self, output_dir: str | Path) -> None:
        self.current_output_dir = Path(output_dir)
        self.session_state.output_dir = self.current_output_dir

    def request_cancel(self) -> None:
        if self._cancel_event is not None:
            self._cancel_event.set()


def main(argv: Sequence[str] | None = None) -> int:
    del argv
    app = NdaxTuiApp()
    app.run()
    return 0
