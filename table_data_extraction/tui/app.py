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
    }

    #main-actions, #settings-actions {
        height: auto;
    }

    #run-log {
        height: 12;
        border: round $accent;
    }

    #current-output-dir, #run-status, #command-preview, #last-output-path, #settings-status {
        height: auto;
        margin: 0 1;
    }

    Input {
        margin: 0 1 1 1;
    }
    """

    BINDINGS = [
        ("f8", "open_settings", "Settings"),
        ("f5", "run_active", "Run"),
        ("f6", "cancel_active_run", "Cancel"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.session_state = AppSessionState()
        self._cancel_event: threading.Event | None = None
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

    def action_cancel_active_run(self) -> None:
        self.request_cancel()

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
