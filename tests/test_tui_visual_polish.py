import asyncio
from pathlib import Path

import pytest
from textual.css.query import NoMatches
from textual.widgets import Select, Static, SelectionList

from table_data_extraction.tui.app import NdaxTuiApp
from table_data_extraction.tui.widgets.file_list import FileList
from table_data_extraction.tui.widgets.palette_preview import PalettePreview


PROJECT_BLUE_RGB = (109, 183, 255)


def test_top_bar_branding_and_buttons_are_not_clipped() -> None:
    async def _run() -> None:
        app = NdaxTuiApp()
        async with app.run_test(size=(84, 40)) as pilot:
            await pilot.pause()

            main_top = app.screen.query_one("#main-top-bar")
            main_title = app.screen.query_one("#main-title", Static)
            main_subtitle = app.screen.query_one("#main-subtitle", Static)
            main_settings = app.screen.query_one("#open-settings")
            main_exit = app.screen.query_one("#exit-app")

            assert main_top.region.height >= 5
            assert main_title.region.height >= 2
            assert main_subtitle.styles.color.rgb == PROJECT_BLUE_RGB
            assert (
                main_settings.region.y + main_settings.region.height
                < main_top.region.y + main_top.region.height
            )
            assert (
                main_exit.region.y + main_exit.region.height
                < main_top.region.y + main_top.region.height
            )

            await pilot.press("f8")
            await pilot.pause()

            settings_top = app.screen.query_one("#settings-top-bar")
            settings_subtitle = app.screen.query_one("#settings-subtitle", Static)
            main_menu = app.screen.query_one("#settings-main-menu")

            assert settings_top.region.height >= 5
            assert settings_subtitle.styles.color.rgb == PROJECT_BLUE_RGB
            assert (
                main_menu.region.y + main_menu.region.height
                < settings_top.region.y + settings_top.region.height
            )

    asyncio.run(_run())


def test_output_row_stacks_button_and_path_cleanly() -> None:
    async def _run() -> None:
        app = NdaxTuiApp()
        async with app.run_test(size=(100, 34)) as pilot:
            await pilot.pause()

            select_button = app.screen.query_one("#select-output-dir")
            output_path = app.screen.query_one("#current-output-dir")

            assert output_path.region.y > select_button.region.y
            assert output_path.region.x == select_button.region.x

    asyncio.run(_run())


def test_more_options_replace_nested_advanced_sections() -> None:
    async def _run() -> None:
        app = NdaxTuiApp()
        async with app.run_test(size=(90, 30)) as pilot:
            await pilot.pause()

            with pytest.raises(NoMatches):
                app.screen.query_one("#plot-advanced")
            with pytest.raises(NoMatches):
                app.screen.query_one("#table-advanced")

            assert app.screen.query_one("#plot-more-options")
            assert app.screen.query_one("#table-more-options")

    asyncio.run(_run())


def test_main_file_list_uses_modal_removal_flow() -> None:
    async def _run() -> None:
        app = NdaxTuiApp()
        column_map = {
            Path("keep.ndax"): ["Voltage", "Time", "Current"],
            Path("remove-a.ndax"): ["Voltage", "Frequency"],
            Path("remove-b.ndax"): ["Voltage", "Time", "Temperature"],
        }
        with pytest.MonkeyPatch.context() as monkeypatch:
            monkeypatch.setattr(
                "table_data_extraction.tui.screens.main_screen.list_columns",
                lambda path: column_map[Path(path)],
            )
            async with app.run_test(size=(84, 30)) as pilot:
                await pilot.pause()

                shared_files = app.screen.query_one("#shared-files", FileList)
                plot_y = app.screen.query_one("#plot-y-column", Select)
                plot_x = app.screen.query_one("#plot-x-column", Select)
                shared_files.set_paths(
                    [
                        Path("keep.ndax"),
                        Path("remove-a.ndax"),
                        Path("remove-b.ndax"),
                    ]
                )
                await pilot.pause()

                initial_options = tuple(prompt for prompt, _ in plot_x._options)
                assert initial_options == ("", "Voltage")

                await pilot.click("#shared-manage-files")
                await pilot.pause()
                assert app.screen.query_one("#manage-files-dialog")

                selection_list = app.screen.query_one(
                    "#manage-files-list",
                    SelectionList,
                )
                remove_button = app.screen.query_one("#manage-files-remove")

                selection_list.select(Path("remove-a.ndax"))
                selection_list.select(Path("remove-b.ndax"))
                await pilot.pause()

                assert not remove_button.disabled
                await pilot.click("#manage-files-remove")
                await pilot.pause()

                assert shared_files.paths == (Path("keep.ndax"),)
                assert tuple(prompt for prompt, _ in plot_x._options) == (
                    "",
                    "Voltage",
                    "Time",
                    "Current",
                )
                assert tuple(prompt for prompt, _ in plot_y._options) == (
                    "",
                    "Voltage",
                    "Time",
                    "Current",
                )
                assert plot_y.value == "Voltage"
                assert plot_x.value == "Voltage"
                assert not plot_y.disabled
                assert not plot_x.disabled
                assert len(app.screen.query("#manage-files-dialog")) == 0

    asyncio.run(_run())


def test_palette_preview_centers_waves_in_white_sample_lane() -> None:
    preview = PalettePreview(["#1718FE", "#D35400"])
    rendered = preview._render_preview().plain.splitlines()

    assert rendered[0].startswith("#1718FE ")
    assert rendered[1].startswith("#D35400 ")

    lane_1 = rendered[0][len("#1718FE ") :]
    lane_2 = rendered[1][len("#D35400 ") :]

    assert lane_1 == "  ~~~~~~"
    assert lane_2 == "  ~~~~~~"


def test_actions_remain_visible_after_terminal_resize() -> None:
    async def _run() -> None:
        app = NdaxTuiApp()
        async with app.run_test(size=(100, 36)) as pilot:
            await pilot.pause()
            await pilot.resize_terminal(84, 24)
            await pilot.pause()

            for widget_id in (
                "#open-settings",
                "#exit-app",
                "#select-output-dir",
                "#run-active",
            ):
                widget = app.screen.query_one(widget_id)
                assert widget.region.x >= 0
                assert widget.region.y >= 0
                assert widget.region.x + widget.region.width <= 84
                assert widget.region.y + widget.region.height <= 24

            await pilot.press("f8")
            await pilot.pause()
            await pilot.resize_terminal(84, 24)
            await pilot.pause()

            for widget_id in (
                "#settings-main-menu",
                "#settings-exit-app",
                "#settings-save",
                "#settings-back",
            ):
                widget = app.screen.query_one(widget_id)
                assert widget.region.x >= 0
                assert widget.region.y >= 0
                assert widget.region.x + widget.region.width <= 84
                assert widget.region.y + widget.region.height <= 24

    asyncio.run(_run())
