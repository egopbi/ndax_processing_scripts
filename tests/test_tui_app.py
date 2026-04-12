import asyncio
import threading
from pathlib import Path
from types import SimpleNamespace

import pytest
from textual.containers import VerticalScroll
from textual.css.query import NoMatches
from textual.widgets import Button, Input, Select, Static

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
            assert app.focused is None
            assert app.screen.query_one("#main-top-bar")
            assert app.screen.query_one("#main-body")
            assert app.screen.query_one("#output-folder-section")
            assert app.screen.query_one("#files-section")
            assert app.screen.query_one("#mode-section")
            assert app.screen.query_one("#main-scroll", VerticalScroll)
            assert app.screen.query_one("#shared-files", FileList)
            assert app.screen.query_one("#parameters-section")
            assert app.screen.query_one("#exit-app")
            assert app.screen.query_one("#run-active")
            assert app.screen.query_one("#main-title", Static).content == "NDAX Processor"
            assert app.screen.query_one("#main-subtitle", Static).content == "by eeee_gorka"
            assert app.screen.query_one("#run-status", Static).content == "Ready"
            assert app.screen.query_one("#plot-column-helper", Static)
            assert app.screen.query_one("#table-column-helper", Static)
            assert not app.screen.query_one("#plot-column-controls").display
            assert not app.screen.query_one("#table-column-controls").display
            assert app.screen.query_one("#mode-select", Select).value == "plot"
            assert app.screen.query_one("#plot-x-min", Input)
            assert app.screen.query_one("#plot-x-max", Input)
            assert app.screen.query_one("#plot-y-min", Input)
            assert app.screen.query_one("#plot-y-max", Input)
            assert (
                app.screen.query_one("#current-output-dir", Static).content
                == str(app.current_output_dir)
            )
            assert app.screen.query_one("#main-top-bar").region.height <= 5
            assert (
                app.screen.query_one("#main-scroll").region.y
                + app.screen.query_one("#main-scroll").region.height
                <= 40
            )
            assert (
                app.screen.query_one("#run-active").region.y
                + app.screen.query_one("#run-active").region.height
                <= 40
            )
            assert (
                app.screen.query_one("#main-bottom-bar").region.y
                + app.screen.query_one("#main-bottom-bar").region.height
                <= 40
            )
            await pilot.press("f8")
            await pilot.pause()
            assert isinstance(app.screen, SettingsScreen)

    asyncio.run(_run())


@pytest.mark.parametrize("size", [(84, 20), (70, 25)])
def test_main_layout_keeps_run_button_visible_on_small_heights(
    size: tuple[int, int]
) -> None:
    async def _run() -> None:
        app = NdaxTuiApp()
        async with app.run_test(size=size) as pilot:
            await pilot.pause()
            run_button = app.screen.query_one("#run-active")
            bottom_bar = app.screen.query_one("#main-bottom-bar")
            assert run_button.region.x >= 0
            assert run_button.region.y >= 0
            assert run_button.region.x + run_button.region.width <= size[0]
            assert run_button.region.y + run_button.region.height <= size[1]
            assert bottom_bar.region.y + bottom_bar.region.height <= size[1]

    asyncio.run(_run())


def test_main_screen_sections_align_to_shared_grid() -> None:
    async def _run() -> None:
        app = NdaxTuiApp()
        async with app.run_test(size=(100, 34)) as pilot:
            await pilot.pause()
            top = app.screen.query_one("#main-top-bar").region
            output = app.screen.query_one("#output-folder-section").region
            files = app.screen.query_one("#files-section").region
            mode = app.screen.query_one("#mode-section").region
            parameters = app.screen.query_one("#parameters-section").region
            bottom = app.screen.query_one("#main-bottom-bar").region
            left_edges = {top.x, output.x, files.x, mode.x, parameters.x, bottom.x}
            right_edges = {
                top.x + top.width,
                output.x + output.width,
                files.x + files.width,
                mode.x + mode.width,
                parameters.x + parameters.width,
                bottom.x + bottom.width,
            }
            assert len(left_edges) == 1
            assert max(right_edges) - min(right_edges) <= 2

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
            shared_files = app.screen.query_one("#shared-files", FileList)
            mode_select = app.screen.query_one("#mode-select", Select)
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

            shared_files.set_paths([Path("plot-1.ndax")])
            await pilot.pause()
            assert not plot_y.disabled
            assert not plot_x.disabled
            assert plot_controls.display
            assert not plot_helper.display
            assert plot_y.value == "Voltage"
            assert plot_x.value == "Time"

            shared_files.add_paths([Path("plot-2.ndax")])
            await pilot.pause()
            assert plot_y.value == "Voltage"
            assert plot_x.value == "Time"

            mode_select.value = "table"
            await pilot.pause()

            shared_files.set_paths([Path("table-1.ndax"), Path("table-2.ndax")])
            await pilot.pause()
            table_y = app.screen.query_one("#table-y-column", Select)
            table_x = app.screen.query_one("#table-x-column", Select)
            assert table_controls.display
            assert not table_helper.display
            assert table_y.value == "Voltage"
            assert table_x.value == "Time"

            shared_files.clear_paths()
            await pilot.pause()
            assert table_y.disabled
            assert table_x.disabled
            assert not table_controls.display
            assert table_helper.display
            assert table_y.value == Select.NULL
            assert table_x.value == Select.NULL

    asyncio.run(_run())


@pytest.mark.parametrize("mode", ["plot", "table"])
def test_column_load_failures_are_logged_and_disable_selects(
    monkeypatch,
    mode: str,
) -> None:
    monkeypatch.setattr(
        "table_data_extraction.tui.screens.main_screen.list_columns",
        lambda path: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    async def _run() -> None:
        app = NdaxTuiApp()
        async with app.run_test() as pilot:
            shared_files = app.screen.query_one("#shared-files", FileList)
            plot_y = app.screen.query_one("#plot-y-column", Select)
            plot_x = app.screen.query_one("#plot-x-column", Select)
            status = app.screen.query_one("#run-status", Static)
            mode_select = app.screen.query_one("#mode-select", Select)

            mode_select.value = mode
            await pilot.pause()

            shared_files.add_paths([Path("broken.ndax")])
            await pilot.pause()

            assert plot_y.disabled
            assert plot_x.disabled
            assert status.content == f"Failed to load columns for {mode}: boom"

    asyncio.run(_run())


def test_column_load_failure_status_tracks_visible_mode_after_switch(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "table_data_extraction.tui.screens.main_screen.list_columns",
        lambda path: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    async def _run() -> None:
        app = NdaxTuiApp()
        async with app.run_test() as pilot:
            shared_files = app.screen.query_one("#shared-files", FileList)
            status = app.screen.query_one("#run-status", Static)
            mode_select = app.screen.query_one("#mode-select", Select)

            shared_files.add_paths([Path("broken.ndax")])
            await pilot.pause()
            assert status.content == "Failed to load columns for plot: boom"

            mode_select.value = "table"
            await pilot.pause()
            assert status.content == "Failed to load columns for table: boom"

            mode_select.value = "plot"
            await pilot.pause()
            assert status.content == "Failed to load columns for plot: boom"

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
            assert app.focused is None
            assert app.screen.query_one("#settings-top-bar")
            assert app.screen.query_one("#settings-shell")
            assert isinstance(app.screen.query_one("#settings-scroll"), VerticalScroll)
            assert app.screen.query_one("#settings-main-menu")
            assert app.screen.query_one("#settings-title", Static).content == "NDAX Processor"
            assert app.screen.query_one("#settings-subtitle", Static).content == "by eeee_gorka"
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
            assert len(app.screen.query("#settings-output-dir")) == 0
            canvas = app.screen.query_one("#settings-preview-canvas")
            preview = app.screen.query_one("#settings-palette-preview", PalettePreview)
            assert "~~~~~~" in preview.content.plain
            assert "#1718FE" in preview.content.plain
            assert canvas.styles.background.rgb == (255, 255, 255)
            assert any("#1718FE" in str(span.style) for span in preview.content.spans)
            await pilot.click("#settings-main-menu")
            await pilot.pause()
            assert isinstance(app.screen, MainScreen)

    asyncio.run(_run())


@pytest.mark.parametrize("size", [(84, 20), (70, 25)])
def test_settings_layout_keeps_actions_visible_on_small_heights(
    size: tuple[int, int]
) -> None:
    async def _run() -> None:
        app = NdaxTuiApp()
        async with app.run_test(size=size) as pilot:
            await pilot.press("f8")
            await pilot.pause()
            save_button = app.screen.query_one("#settings-save")
            back_button = app.screen.query_one("#settings-back")
            actions = app.screen.query_one("#settings-actions")
            for button in (save_button, back_button):
                assert button.region.x >= 0
                assert button.region.y >= 0
                assert button.region.x + button.region.width <= size[0]
                assert button.region.y + button.region.height <= size[1]
            assert actions.region.y + actions.region.height <= size[1]

    asyncio.run(_run())


def test_settings_sections_align_to_shared_grid() -> None:
    async def _run() -> None:
        app = NdaxTuiApp()
        async with app.run_test(size=(100, 34)) as pilot:
            await pilot.press("f8")
            await pilot.pause()
            top = app.screen.query_one("#settings-top-bar").region
            body = app.screen.query_one("#settings-body").region
            actions = app.screen.query_one("#settings-actions").region
            status = app.screen.query_one("#settings-status").region
            left_edges = {top.x, body.x, actions.x, status.x}
            right_edges = {
                top.x + top.width,
                body.x + body.width,
                actions.x + actions.width,
                status.x + status.width,
            }
            assert len(left_edges) == 1
            assert max(right_edges) - min(right_edges) <= 1

    asyncio.run(_run())


def test_more_options_open_modal_screen() -> None:
    async def _run() -> None:
        app = NdaxTuiApp()
        async with app.run_test(size=(100, 36)) as pilot:
            await pilot.pause()

            with pytest.raises(NoMatches):
                app.screen.query_one("#plot-advanced")
            with pytest.raises(NoMatches):
                app.screen.query_one("#table-advanced")

            main_scroll = app.screen.query_one("#main-scroll", VerticalScroll)
            button = app.screen.query_one("#plot-more-options", Button)
            main_scroll.scroll_to_widget(button, animate=False, immediate=True)
            await pilot.pause()
            await pilot.click("#plot-more-options")
            await pilot.pause()

            assert app.screen.query_one("#advanced-options-dialog")

    asyncio.run(_run())


def test_parse_anchor_x_accepts_space_separator() -> None:
    screen = MainScreen()
    assert screen._parse_anchor_x("0.5 1.0 2.5") == (0.5, 1.0, 2.5)
    assert screen._parse_anchor_x("0.5, 1.0 2.5") == (0.5, 1.0, 2.5)


def test_plot_override_forces_jpg_suffix() -> None:
    async def _run() -> None:
        app = NdaxTuiApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            assert app.screen._resolve_output_override(
                "custom_name",
                enforced_suffix=".jpg",
            ) == app.current_output_dir / "custom_name.jpg"
            assert app.screen._resolve_output_override(
                "custom_name.png",
                enforced_suffix=".jpg",
            ) == app.current_output_dir / "custom_name.jpg"
            assert app.screen._resolve_output_override(
                "/tmp/custom_name.bmp",
                enforced_suffix=".jpg",
            ) == Path("/tmp/custom_name.jpg")

    asyncio.run(_run())


def test_table_override_forces_csv_suffix_from_main_input(monkeypatch) -> None:
    monkeypatch.setattr(
        "table_data_extraction.tui.screens.main_screen.list_columns",
        lambda path: ["Voltage", "Time"],
    )

    async def _run() -> None:
        app = NdaxTuiApp()
        async with app.run_test() as pilot:
            shared_files = app.screen.query_one("#shared-files", FileList)
            mode_select = app.screen.query_one("#mode-select", Select)

            shared_files.set_paths([Path("table.ndax")])
            mode_select.value = "table"
            await pilot.pause()

            app.screen.query_one("#table-anchor-x", Input).value = "1.0"
            app.screen.query_one("#table-output-override", Input).value = "custom_name.jpg"
            command = app.screen._build_active_command()

            assert command.mode == "table"
            assert command.output_path == app.current_output_dir / "custom_name.csv"

    asyncio.run(_run())


def test_output_override_inputs_live_in_main_parameters_forms() -> None:
    async def _run() -> None:
        app = NdaxTuiApp()
        async with app.run_test(size=(100, 36)) as pilot:
            await pilot.pause()
            plot_override = app.screen.query_one("#plot-output-override", Input)
            plot_y_max = app.screen.query_one("#plot-y-max", Input)
            plot_more = app.screen.query_one("#plot-more-options", Button)

            assert plot_override.region.y > plot_y_max.region.y
            assert plot_override.region.y < plot_more.region.y

            app.screen.query_one("#mode-select", Select).value = "table"
            await pilot.pause()

            table_override = app.screen.query_one("#table-output-override", Input)
            table_anchor = app.screen.query_one("#table-anchor-x", Input)
            table_more = app.screen.query_one("#table-more-options", Button)

            assert table_override.region.y > table_anchor.region.y
            assert table_override.region.y < table_more.region.y

    asyncio.run(_run())


def test_plot_axis_limits_are_outside_advanced_collapsible() -> None:
    async def _run() -> None:
        app = NdaxTuiApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            for widget_id in ("#plot-x-min", "#plot-x-max", "#plot-y-min", "#plot-y-max"):
                widget = app.screen.query_one(widget_id, Input)
                ancestor = widget.parent
                ancestor_ids: list[str] = []
                while ancestor is not None:
                    if ancestor.id is not None:
                        ancestor_ids.append(ancestor.id)
                    ancestor = ancestor.parent
                assert "plot-form" in ancestor_ids
            with pytest.raises(NoMatches):
                app.screen.query_one("#plot-advanced")

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
    file_list = FileList(
        [Path("one.ndax"), Path("two.ndax"), Path("three.ndax")]
    )
    file_list.remove_path_at(1)
    assert file_list.paths == (Path("one.ndax"), Path("three.ndax"))


def test_palette_preview_places_wave_sample_to_the_right_of_color_code() -> None:
    preview = PalettePreview(["#1718FE"])
    rendered = preview._render_preview()
    first_line = rendered.plain.splitlines()[0]

    assert first_line.startswith("#1718FE")
    assert first_line.endswith("~~~~~~")
