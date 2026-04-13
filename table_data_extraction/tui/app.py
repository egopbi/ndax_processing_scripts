from __future__ import annotations

from pathlib import Path
import threading
from typing import Sequence

from textual.app import App
from textual.scrollbar import ScrollBarRender

from table_data_extraction.tui.screens.main_screen import MainScreen
from table_data_extraction.tui.screens.settings_screen import SettingsScreen
from table_data_extraction.tui.settings_service import resolve_runtime_output_dir
from table_data_extraction.tui.state import AppSessionState

# Use ASCII caps to avoid unsupported Unicode glyphs on Windows scrollbars.
ScrollBarRender.VERTICAL_BARS = ["|", "|", "|", "|", "|", "|", "|", " "]
ScrollBarRender.HORIZONTAL_BARS = ["-", "-", "-", "-", "-", "-", "-", " "]


class NdaxTuiApp(App[None]):
    CSS = """
    Screen {
        layout: vertical;
        background: #0b0d10;
        color: #e5e7eb;
        padding: 0 1 1 1;
        scrollbar-background: #0f1216;
        scrollbar-background-hover: #0f1216;
        scrollbar-background-active: #0f1216;
        scrollbar-color: #6db7ff;
        scrollbar-color-hover: #8cc8ff;
        scrollbar-color-active: #6db7ff;
        scrollbar-gutter: stable;
    }

    #main-shell, #settings-shell {
        width: 1fr;
        height: 1fr;
        min-height: 0;
    }

    #main-top-bar, #settings-top-bar,
    #main-body, #output-folder-section, #mode-section, #logs-section,
    #main-bottom-bar, #settings-body, #settings-actions, #settings-status {
        width: 1fr;
        min-width: 0;
    }

    #main-top-bar, #settings-top-bar {
        height: 5;
        margin: 0;
        padding: 0 1;
    }

    #main-brand, #settings-brand {
        width: 1fr;
        height: 3;
    }

    #main-title, #settings-title {
        text-style: bold;
        color: #f8fafc;
        height: 2;
        content-align: left middle;
    }

    #main-subtitle, #settings-subtitle {
        color: #6db7ff;
        height: 1;
        content-align: left middle;
    }

    #main-top-actions, #settings-top-actions, #main-bottom-actions {
        width: auto;
        height: 3;
        align: right middle;
    }

    .section-shell, .surface-box {
        background: #20242b;
        border: ascii #343a43;
    }

    .section-shell {
        margin-top: 1;
        padding: 0 1 0 1;
    }

    .section-title {
        margin: 0;
        color: #e5e7eb;
    }

    .attention-box {
        background: #20242b;
        border: ascii #6db7ff;
        color: #6db7ff;
        margin-bottom: 1;
    }

    .path-value {
        width: 1fr;
        height: 3;
        content-align: left middle;
        padding: 0 1;
        overflow-x: hidden;
        text-overflow: ellipsis;
        color: #b5bcc7;
    }

    #output-folder-row, #plot-file-actions, #table-file-actions,
    #settings-palette-row, .inline-input-row {
        width: 1fr;
        height: auto;
    }

    #output-folder-row Button, #plot-file-actions Button, #table-file-actions Button {
        width: auto;
    }

    #output-folder-row {
        height: 3;
        align: left middle;
    }

    #current-output-dir {
        width: 1fr;
        height: 3;
        content-align: left middle;
    }

    .spacer {
        width: 1fr;
    }

    #main-body {
        layout: grid;
        grid-size: 1 4;
        grid-rows: auto 1fr auto auto;
        width: 1fr;
        height: 1fr;
        min-height: 0;
    }

    #workflow-tabs {
        height: 1fr;
        min-height: 0;
    }

    #mode-section {
        height: 1fr;
        min-height: 0;
    }

    #plot-pane, #table-pane, #settings-body, #settings-scroll {
        height: 1fr;
        min-height: 0;
    }

    #plot-pane, #table-pane {
        padding-right: 1;
        scrollbar-background: #0f1216;
        scrollbar-background-hover: #0f1216;
        scrollbar-background-active: #0f1216;
        scrollbar-color: #6db7ff;
        scrollbar-color-hover: #8cc8ff;
        scrollbar-color-active: #6db7ff;
    }

    #plot-files-section, #table-files-section,
    #plot-columns-section, #table-columns-section,
    #settings-defaults-section, #settings-palette-section {
        height: auto;
        width: 1fr;
        margin-bottom: 1;
    }

    #plot-columns-section, #table-columns-section {
        min-height: 0;
    }

    #main-bottom-bar {
        height: auto;
        width: 1fr;
        padding-top: 0;
    }

    #run-log {
        width: 1fr;
        height: 3;
        min-height: 3;
        margin: 0;
        padding: 0 1;
        background: #0b0d10;
        border: ascii #6db7ff;
    }

    Input, Select {
        width: 1fr;
        margin: 0 0 1 0;
        background: #1d2228;
        border: ascii #343a43;
        color: #e5e7eb;
    }

    Input:focus, Select:focus {
        border: ascii #6db7ff;
    }

    /* Keep SelectCurrent in ASCII mode to avoid unsupported tall glyphs on Windows. */
    Select > SelectCurrent {
        border: ascii #343a43;
    }

    Select:focus > SelectCurrent {
        border: ascii #6db7ff;
    }

    Select > SelectOverlay {
        border: ascii #343a43;
    }

    Select:focus > SelectOverlay {
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

    #settings-scroll {
        padding: 0;
        scrollbar-background: #0f1216;
        scrollbar-background-hover: #0f1216;
        scrollbar-background-active: #0f1216;
        scrollbar-color: #6db7ff;
        scrollbar-color-hover: #8cc8ff;
        scrollbar-color-active: #6db7ff;
        scrollbar-gutter: stable;
    }

    #settings-palette-row {
        height: auto;
    }

    #settings-palette {
        width: 1fr;
    }

    #settings-preview-panel {
        width: 24;
        min-width: 24;
        margin-left: 1;
        background: transparent;
        border: ascii #6db7ff;
        padding: 1;
        height: auto;
    }

    #settings-preview-title {
        margin: 0 0 1 0;
    }

    #settings-preview-canvas {
        width: 1fr;
        min-height: 8;
        background: white;
        color: black;
        padding: 0 1;
    }

    #settings-preview-panel PalettePreview {
        width: 1fr;
        background: transparent;
        color: black;
        height: auto;
        min-height: 0;
        padding: 0;
    }

    #settings-actions {
        height: auto;
        margin: 0;
        padding-top: 1;
    }

    #settings-status {
        height: auto;
        margin-top: 1;
    }

    #plot-column-helper, #table-column-helper, #convert-column-helper {
        height: auto;
    }

    #plot-column-controls, #table-column-controls, #convert-column-controls {
        display: none;
        height: auto;
        min-height: 0;
    }

    #plot-column-controls Horizontal, #table-column-controls Horizontal, .inline-input-row {
        width: 1fr;
        height: auto;
    }

    .column-label {
        width: 12;
        margin: 0 1 1 0;
    }

    .file-list {
        background: #20242b;
        padding: 0 2 0 0;
        margin: 0 0 1 0;
        width: 1fr;
        height: auto;
    }

    .file-list-row {
        width: 1fr;
        height: auto;
        margin-bottom: 1;
    }

    .file-list-path {
        width: 1fr;
    }

    .file-list-remove {
        width: 3;
        min-width: 3;
        margin: 0;
    }

    #plot-advanced > Contents, #table-advanced > Contents {
        overflow-y: hidden;
        scrollbar-background: #0f1216;
        scrollbar-background-hover: #0f1216;
        scrollbar-background-active: #0f1216;
        scrollbar-color: #6db7ff;
        scrollbar-color-hover: #8cc8ff;
        scrollbar-color-active: #6db7ff;
    }

    #settings-top-actions Button {
        min-width: 12;
    }

    #settings-actions Button {
        min-width: 10;
    }

    #main-body {
        layout: vertical;
        height: 1fr;
        min-height: 0;
    }

    #main-scroll {
        height: 1fr;
        min-height: 0;
        padding: 0;
        scrollbar-background: #0f1216;
        scrollbar-background-hover: #0f1216;
        scrollbar-background-active: #0f1216;
        scrollbar-color: #6db7ff;
        scrollbar-color-hover: #8cc8ff;
        scrollbar-color-active: #6db7ff;
    }

    #files-section, #parameters-section {
        width: 1fr;
        height: auto;
    }

    #output-folder-section {
        height: auto;
    }

    #mode-section {
        height: auto;
        min-height: 0;
    }

    #output-folder-row {
        height: auto;
        align: left top;
    }

    #shared-file-actions, .secondary-actions, .field-grid-row {
        width: 1fr;
        height: auto;
    }

    #mode-select {
        width: 1fr;
    }

    #mode-forms, .mode-form {
        width: 1fr;
        height: auto;
    }

    #parameters-section .attention-box {
        margin-bottom: 1;
    }

    #run-status {
        width: 1fr;
        min-width: 0;
        color: #b5bcc7;
        content-align: left middle;
        padding: 0 1 0 0;
        overflow-x: hidden;
        text-overflow: ellipsis;
    }

    #main-bottom-bar {
        height: auto;
        margin-top: 1;
        padding: 0 1;
        align: left middle;
    }

    .file-list-static, .file-list-empty {
        width: 1fr;
    }
    """

    AUTO_FOCUS = ""

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
