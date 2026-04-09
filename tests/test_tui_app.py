import asyncio
import threading
from pathlib import Path
from types import SimpleNamespace

import pytest
from textual.containers import Horizontal, VerticalScroll
from textual.widgets import Log, Select, TabbedContent

from table_data_extraction.tui.app import NdaxTuiApp
from table_data_extraction.tui.models import CompletedCommand
from table_data_extraction.tui.screens.settings_screen import SettingsScreen
from table_data_extraction.tui.widgets.file_list import FileList
from table_data_extraction.tui.widgets.palette_preview import PalettePreview


def test_app_mounts_main_screen_widgets() -> None:
    async def _run() -> None:
        app = NdaxTuiApp()
        async with app.run_test() as pilot:
            assert app.screen.query_one("#main-top-bar")
            assert app.screen.query_one("#workflow-tabs")
            assert app.screen.query_one("#run-log", Log)
            assert app.screen.query_one("#exit-app")
            assert app.screen.query_one("#run-active")
            assert len(app.screen.query("#run-log")) == 1
            assert app.screen.query_one("#plot-y-column", Select)
            assert app.screen.query_one("#plot-x-column", Select)
            assert app.screen.query_one("#table-y-column", Select)
            assert app.screen.query_one("#table-x-column", Select)
            await pilot.press("f8")
            await pilot.pause()
            assert isinstance(app.screen, SettingsScreen)

    asyncio.run(_run())


def test_column_selects_update_and_clear_with_loaded_files(monkeypatch) -> None:
    column_map = {
        Path("plot-1.ndax"): ["Voltage", "Time", "Current(mA)"],
        Path("plot-2.ndax"): ["Voltage", "Time", "Temperature"],
        Path("table-1.ndax"): ["Voltage", "Time", "Charge_Capacity(mAh)"],
        Path("table-2.ndax"): ["Voltage", "Time", "Discharge_Capacity(mAh)"],
    }
    monkeypatch.setattr(
        "table_data_extraction.tui.screens.main_screen.list_columns",
        lambda path: column_map[Path(path)],
    )

    async def _run() -> None:
        app = NdaxTuiApp()
        async with app.run_test() as pilot:
            plot_files = app.screen.query_one("#plot-files", FileList)
            plot_y = app.screen.query_one("#plot-y-column", Select)
            plot_x = app.screen.query_one("#plot-x-column", Select)
            assert plot_y.disabled
            assert plot_x.disabled

            plot_files.add_paths([Path("plot-1.ndax")])
            await pilot.pause()
            assert not plot_y.disabled
            assert not plot_x.disabled
            assert plot_y.value == "Voltage"
            assert plot_x.value == "Time"

            plot_files.add_paths([Path("plot-2.ndax")])
            await pilot.pause()
            assert plot_y.value == "Voltage"
            assert plot_x.value == "Time"

            tabbed = app.screen.query_one("#workflow-tabs", TabbedContent)
            tabbed.active = "table-tab"
            await pilot.pause()

            table_files = app.screen.query_one("#table-files", FileList)
            table_y = app.screen.query_one("#table-y-column", Select)
            table_x = app.screen.query_one("#table-x-column", Select)
            table_files.add_paths([Path("table-1.ndax"), Path("table-2.ndax")])
            await pilot.pause()
            assert table_y.value == "Voltage"
            assert table_x.value == "Time"

            table_files.clear_paths()
            await pilot.pause()
            assert table_y.disabled
            assert table_x.disabled
            assert table_y.value == Select.NULL
            assert table_x.value == Select.NULL

    asyncio.run(_run())


def test_column_load_failures_are_logged_and_disable_selects(monkeypatch) -> None:
    monkeypatch.setattr(
        "table_data_extraction.tui.screens.main_screen.list_columns",
        lambda path: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    async def _run() -> None:
        app = NdaxTuiApp()
        async with app.run_test() as pilot:
            plot_files = app.screen.query_one("#plot-files", FileList)
            plot_y = app.screen.query_one("#plot-y-column", Select)
            plot_x = app.screen.query_one("#plot-x-column", Select)
            log = app.screen.query_one("#run-log", Log)

            plot_files.add_paths([Path("broken.ndax")])
            await pilot.pause()

            assert plot_y.disabled
            assert plot_x.disabled
            assert any("Failed to load columns for plot-tab" in line for line in log.lines)

    asyncio.run(_run())


@pytest.mark.parametrize("launch_mode", ["run", "health"])
def test_exit_waits_for_command_cleanup_during_start_boundary(monkeypatch, launch_mode: str) -> None:
    async def _run() -> None:
        app = NdaxTuiApp()
        exit_calls: list[bool] = []
        release = threading.Event()

        def _spy_exit(*args, **kwargs):
            exit_calls.append(True)

        original_start = threading.Thread.start
        fake_command = SimpleNamespace(
            argv=("python", "-u", "fake_script.py"),
            output_path=None,
        )

        def _fake_run_subprocess_command(
            command,
            *,
            on_output=None,
            cancel_event=None,
            env=None,
        ):
            assert cancel_event is not None
            assert cancel_event.is_set()
            assert release.wait(timeout=1)
            return CompletedCommand(
                command=command,
                returncode=0,
                stdout="",
                stderr="",
                was_cancelled=True,
            )

        def _patched_start(self, *args, **kwargs):
            if getattr(getattr(self, "_target", None), "__name__", "") == "_run_command_in_thread":
                app.action_exit_app()
                assert app._pending_exit is True
                assert app.session_state.is_running is True
                assert app._cancel_event is not None
                assert app._cancel_event.is_set()
                assert exit_calls == []
                return original_start(self, *args, **kwargs)
            return original_start(self, *args, **kwargs)

        async with app.run_test() as pilot:
            monkeypatch.setattr(app, "exit", _spy_exit)
            monkeypatch.setattr(threading.Thread, "start", _patched_start)

            if launch_mode == "run":
                monkeypatch.setattr(
                    app.screen,
                    "_build_active_command",
                    lambda: fake_command,
                )
            else:
                monkeypatch.setattr(
                    "table_data_extraction.tui.screens.main_screen.build_health_check_command",
                    lambda config: fake_command,
                )
                monkeypatch.setattr(
                    app.screen,
                    "_selected_health_file",
                    lambda: Path("sample.ndax"),
                )

            monkeypatch.setattr(
                "table_data_extraction.tui.screens.main_screen.run_subprocess_command",
                _fake_run_subprocess_command,
            )

            if launch_mode == "run":
                app.screen.action_run_active()
            else:
                app.screen._run_health_check()

            assert app._pending_exit is True
            assert exit_calls == []

            release.set()
            for _ in range(20):
                if exit_calls == [True]:
                    break
                await pilot.pause()
            assert exit_calls == [True]

    asyncio.run(_run())


def test_settings_screen_shows_palette_preview_and_inputs() -> None:
    async def _run() -> None:
        app = NdaxTuiApp()
        async with app.run_test(size=(80, 16)) as pilot:
            app.push_screen(SettingsScreen())
            await pilot.pause()
            assert app.screen.query_one("#settings-top-bar")
            assert isinstance(app.screen.query_one("#settings-scroll"), VerticalScroll)
            assert isinstance(
                app.screen.query_one("#settings-palette-section"),
                Horizontal,
            )
            assert app.screen.query_one("#settings-preview-panel")
            assert app.screen.query_one("#settings-plot-x")
            assert app.screen.query_one("#settings-palette-preview", PalettePreview)
            assert app.screen.query_one("#settings-save")
            assert app.screen.query_one("#settings-cancel")

    asyncio.run(_run())
