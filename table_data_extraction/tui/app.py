from __future__ import annotations

from pathlib import Path
import threading
from typing import Sequence

from textual.app import App

from table_data_extraction.tui.screens.main_screen import MainScreen
from table_data_extraction.tui.screens.settings_screen import SettingsScreen
from table_data_extraction.tui.settings_service import resolve_runtime_output_dir
from table_data_extraction.tui.state import AppSessionState


class NdaxTuiApp(App[None]):
    CSS = """
    Screen {
        layout: vertical;
        background: #0b0d10;
        color: #e5e7eb;
        scrollbar-background: #0f1216;
        scrollbar-background-hover: #0f1216;
        scrollbar-background-active: #0f1216;
        scrollbar-color: #6db7ff;
        scrollbar-color-hover: #8cc8ff;
        scrollbar-color-active: #6db7ff;
        scrollbar-gutter: stable;
    }

    #main-shell {
        height: 1fr;
        min-height: 0;
    }

    #main-top-bar, #settings-top-bar {
        height: auto;
    }

    #main-top-bar, #settings-top-bar {
        margin: 0 1 0 1;
        padding: 0;
    }

    #output-folder-section, #mode-section, #logs-section,
    #plot-pane, #table-pane,
    #plot-files-section, #plot-columns-section,
    #table-files-section, #table-columns-section,
    #settings-defaults-section, #settings-palette-section {
        height: auto;
    }

    #main-top-row, #settings-top-row {
        height: auto;
        width: auto;
    }

    #main-top-actions, #settings-top-actions, #main-bottom-actions, #settings-actions {
        width: auto;
        height: auto;
    }

    .section-shell {
        background: #20242b;
        border: ascii #343a43;
        margin: 0 1 0 1;
        padding: 0 1 0 1;
    }

    .section-title {
        margin: 0 0 1 0;
        color: #e5e7eb;
    }

    .surface-box {
        background: #20242b;
        border: ascii #343a43;
    }

    .attention-box {
        background: #20242b;
        border: ascii #6db7ff;
        color: #6db7ff;
    }

    .path-value {
        width: 1fr;
        height: 1;
        overflow-x: hidden;
        text-overflow: ellipsis;
        color: #b5bcc7;
    }

    #output-folder-row {
        height: auto;
        width: 1fr;
    }

    #output-folder-row Button {
        width: auto;
    }

    #current-output-dir, #settings-output-dir {
        width: 1fr;
        height: 1;
    }

    .spacer, #main-title-spacer, #settings-title-spacer {
        width: 1fr;
    }

    #workflow-tabs {
        height: 1fr;
        min-height: 0;
    }

    #mode-section {
        height: 1fr;
        min-height: 0;
    }

    #plot-pane, #table-pane {
        height: 1fr;
        min-height: 0;
    }

    #plot-files-section, #table-files-section {
        height: auto;
    }

    #plot-columns-section, #table-columns-section {
        height: 1fr;
        min-height: 0;
        overflow-y: auto;
    }

    #mode-title, #files-title, #columns-title, #logs-title {
        margin: 0 0 1 0;
    }

    #main-bottom-bar {
        height: auto;
        padding: 0 1 0 1;
    }

    #run-log {
        height: 6;
        margin: 0;
        padding: 0 1;
        background: #0b0d10;
        border: ascii #6db7ff;
    }

    Input, Select {
        margin: 0 1 0 1;
        width: 1fr;
        background: #1d2228;
        border: ascii #343a43;
        color: #e5e7eb;
    }

    Input:focus, Select:focus {
        border: ascii #6db7ff;
    }

    Button {
        background: #2a2f36;
        color: #e5e7eb;
        border: ascii #343a43;
        margin: 0 1 0 0;
    }

    Button:hover, Button:focus {
        border: ascii #6db7ff;
    }

    #run-active, #settings-save {
        background: #7ecb8f;
        color: #0b0d10;
        border: ascii #7ecb8f;
    }

    #run-active:hover, #run-active:focus,
    #settings-save:hover, #settings-save:focus {
        border: ascii #7ecb8f;
    }

    #settings-status {
        height: auto;
        margin: 0 1;
        width: 1fr;
    }

    #settings-scroll {
        height: 1fr;
        min-height: 0;
        padding: 0 1 1 1;
        scrollbar-background: #0f1216;
        scrollbar-background-hover: #0f1216;
        scrollbar-background-active: #0f1216;
        scrollbar-color: #6db7ff;
        scrollbar-color-hover: #8cc8ff;
        scrollbar-color-active: #6db7ff;
        scrollbar-gutter: stable;
    }

    #settings-body, #settings-scroll {
        height: 1fr;
    }

    #settings-palette-section {
        height: auto;
        margin: 0 1 0 1;
    }

    #settings-palette-section Horizontal {
        height: auto;
    }

    #settings-palette {
        width: 1fr;
    }

    #settings-preview-panel {
        width: 24;
        margin-left: 1;
        background: #20242b;
        border: ascii #6db7ff;
        padding: 0 1;
        height: auto;
    }

    #settings-preview-title {
        margin: 0 0 1 0;
    }

    #settings-preview-panel PalettePreview {
        background: white;
        color: black;
        height: auto;
    }

    #plot-file-actions, #table-file-actions {
        height: auto;
        width: auto;
        margin-bottom: 0;
    }

    #plot-column-helper, #table-column-helper {
        margin: 0 1 0 1;
        height: auto;
    }

    #plot-column-controls, #table-column-controls {
        display: none;
        margin: 0 1 0 1;
        min-height: 0;
        overflow-y: auto;
    }

    #plot-column-controls Horizontal, #table-column-controls Horizontal {
        height: auto;
    }

    .column-label {
        width: 12;
        margin: 0 1 0 0;
    }

    .file-list {
        background: #20242b;
        padding: 0 1;
        margin: 0 1 0 1;
    }

    #settings-top-actions Button {
        min-width: 12;
    }

    #settings-actions Button {
        min-width: 10;
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
