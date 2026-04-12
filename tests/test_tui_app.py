import asyncio
import threading
from pathlib import Path
from types import SimpleNamespace

import pytest
from textual.containers import Horizontal, VerticalScroll
from textual.widgets import Input, Log, Select, Static, TabbedContent

from table_data_extraction.tui.app import NdaxTuiApp
from table_data_extraction.tui.models import CompletedCommand
from table_data_extraction.tui.screens.main_screen import MainScreen
from table_data_extraction.tui.screens.settings_screen import SettingsScreen
from table_data_extraction.tui.widgets.file_list import FileList
from table_data_extraction.tui.widgets.palette_preview import PalettePreview


def test_app_mounts_main_screen_widgets() -> None:
    async def _run() -> None:
        app = NdaxTuiApp()
        async with app.run_test(size=(84, 40)) as pilot:
            assert app.screen.query_one("#main-top-bar")
            assert app.screen.query_one("#output-folder-section")
            assert app.screen.query_one("#mode-section")
            assert app.screen.query_one("#workflow-tabs")
            assert app.screen.query_one("#logs-section")
            assert app.screen.query_one("#run-log", Log)
            assert app.screen.query_one("#exit-app")
            assert app.screen.query_one("#run-active")
            assert len(app.screen.query("#run-log")) == 1
            assert app.screen.query_one("#plot-column-helper", Static)
            assert app.screen.query_one("#table-column-helper", Static)
            assert not app.screen.query_one("#plot-column-controls").display
            assert not app.screen.query_one("#table-column-controls").display
            assert (
                app.screen.query_one("#current-output-dir", Static).content
                == str(app.current_output_dir)
            )
            assert app.screen.query_one("#main-top-bar").region.height <= 4
            assert app.screen.query_one("#output-folder-section").region.y < 10
            assert app.screen.query_one("#mode-section").region.y < 15
            assert (
                app.screen.query_one("#run-log", Log).region.y
                + app.screen.query_one("#run-log", Log).region.height
                <= 40
            )
            assert (
                app.screen.query_one("#run-active").region.y
                + app.screen.query_one("#run-active").region.height
                <= 40
            )
            assert (
                app.screen.query_one("#plot-columns-section").region.height
                >= app.screen.query_one("#plot-files-section").region.height
            )
            assert (
                app.screen.query_one("#table-columns-section").region.height
                >= app.screen.query_one("#table-files-section").region.height
            )
            assert (
                app.screen.query_one("#plot-files", FileList).region.y
                <= app.screen.query_one("#plot-file-actions").region.y + 4
            )
            assert (
                app.screen.query_one("#plot-column-helper", Static).region.y
                <= app.screen.query_one("#plot-files", FileList).region.y + 3
            )
            assert (
                app.screen.query_one("#table-files", FileList).region.y
                <= app.screen.query_one("#table-file-actions").region.y + 4
            )
            assert (
                app.screen.query_one("#table-column-helper", Static).region.y
                <= app.screen.query_one("#table-files", FileList).region.y + 3
            )
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
            plot_controls = app.screen.query_one("#plot-column-controls")
            plot_helper = app.screen.query_one("#plot-column-helper", Static)
            table_controls = app.screen.query_one("#table-column-controls")
            table_helper = app.screen.query_one("#table-column-helper", Static)
            assert plot_y.disabled
            assert plot_x.disabled
            assert not plot_controls.display
            assert plot_helper.display
            assert not table_controls.display
            assert table_helper.display

            plot_files.add_paths([Path("plot-1.ndax")])
            await pilot.pause()
            assert not plot_y.disabled
            assert not plot_x.disabled
            assert plot_controls.display
            assert not plot_helper.display
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
            assert table_controls.display
            assert not table_helper.display
            assert table_y.value == "Voltage"
            assert table_x.value == "Time"

            table_files.clear_paths()
            await pilot.pause()
            assert table_y.disabled
            assert table_x.disabled
            assert not table_controls.display
            assert table_helper.display
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
        async with app.run_test(size=(84, 40)) as pilot:
            app.push_screen(SettingsScreen())
            await pilot.pause()
            assert app.screen.query_one("#settings-top-bar")
            assert isinstance(app.screen.query_one("#settings-scroll"), VerticalScroll)
            assert app.screen.query_one("#settings-main-menu")
            assert app.screen.query_one("#settings-defaults-section")
            assert app.screen.query_one("#settings-palette-section")
            assert app.screen.query_one("#settings-scroll").region.y < 10
            assert app.screen.query_one("#settings-defaults-section").region.y < 10
            assert app.screen.query_one("#settings-preview-panel")
            assert app.screen.query_one("#settings-palette", Input)
            assert app.screen.query_one("#settings-plot-x")
            assert app.screen.query_one("#settings-palette-preview", PalettePreview)
            assert app.screen.query_one("#settings-save")
            assert app.screen.query_one("#settings-back")
            assert app.screen.query_one("#settings-actions")
            assert (
                app.screen.query_one("#settings-actions").region.y
                + app.screen.query_one("#settings-actions").region.height
                <= 40
            )
            assert (
                app.screen.query_one("#settings-save").region.y
                + app.screen.query_one("#settings-save").region.height
                <= 40
            )
            assert (
                app.screen.query_one("#settings-back").region.y
                + app.screen.query_one("#settings-back").region.height
                <= 40
            )
            assert (
                app.screen.query_one("#settings-output-dir", Static).content
                == str(app.current_output_dir)
            )
            preview = app.screen.query_one("#settings-palette-preview", PalettePreview)
            assert "~~~~~~" in preview.content.plain
            assert "#1718FE" in preview.content.plain
            assert any(
                "#1718FE" in str(span.style) and "on white" in str(span.style)
                for span in preview.content.spans
            )
            await pilot.click("#settings-main-menu")
            await pilot.pause()
            assert isinstance(app.screen, MainScreen)

    asyncio.run(_run())


def test_palette_preview_uses_black_for_light_colors() -> None:
    assert PalettePreview._foreground_for_color("#f0f0f0") == "black"
    assert PalettePreview._foreground_for_color("#1718fe") == "#1718fe"


def test_file_list_uses_blue_empty_state_and_gray_selected_paths() -> None:
    empty_list = FileList()
    empty_render = empty_list._render_text()
    assert empty_render.plain == "No NDAX files selected."
    assert any("#6db7ff" in str(span.style) for span in empty_render.spans)

    selected_list = FileList([Path("one.ndax"), Path("two.ndax")])
    selected_render = selected_list._render_text()
    assert "one.ndax" in selected_render.plain
    assert "two.ndax" in selected_render.plain
    assert any("#b5bcc7" in str(span.style) for span in selected_render.spans)
    assert all("#6bdcff" not in str(span.style) for span in selected_render.spans)


def test_file_list_supports_removing_single_selected_file() -> None:
    async def _run() -> None:
        app = NdaxTuiApp()
        async with app.run_test(size=(84, 40)) as pilot:
            plot_files = app.screen.query_one("#plot-files", FileList)
            plot_files.add_paths(
                [Path("one.ndax"), Path("two.ndax"), Path("three.ndax")]
            )
            await pilot.pause()
            assert plot_files.paths == (
                Path("one.ndax"),
                Path("two.ndax"),
                Path("three.ndax"),
            )

            await pilot.click("#plot-files-remove-1")
            await pilot.pause()
            assert plot_files.paths == (Path("one.ndax"), Path("three.ndax"))

    asyncio.run(_run())


def test_palette_preview_places_wave_sample_to_the_right_of_color_code() -> None:
    preview = PalettePreview(["#1718FE"])
    rendered = preview._render_preview()
    first_line = rendered.plain.splitlines()[0]

    assert first_line.startswith("#1718FE")
    assert first_line.endswith("~~~~~~")
