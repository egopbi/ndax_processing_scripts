import asyncio
from pathlib import Path

from textual.widgets import Static

from table_data_extraction.tui.app import NdaxTuiApp
from table_data_extraction.tui.widgets.file_list import FileList
from table_data_extraction.tui.widgets.palette_preview import PalettePreview


PROJECT_BLUE_RGB = (109, 183, 255)


def _collapsible_contents(widget) -> object:
    return list(widget.children)[1]


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


def test_output_row_path_is_vertically_centered_to_button() -> None:
    async def _run() -> None:
        app = NdaxTuiApp()
        async with app.run_test(size=(100, 34)) as pilot:
            await pilot.pause()

            select_button = app.screen.query_one("#select-output-dir")
            output_path = app.screen.query_one("#current-output-dir")

            button_center = select_button.region.y + (select_button.region.height / 2)
            path_center = output_path.region.y + (output_path.region.height / 2)
            assert abs(button_center - path_center) <= 0.5

    asyncio.run(_run())


def test_advanced_sections_do_not_have_nested_scrollbars() -> None:
    async def _run() -> None:
        app = NdaxTuiApp()
        async with app.run_test(size=(90, 30)) as pilot:
            await pilot.pause()

            plot_advanced_contents = _collapsible_contents(
                app.screen.query_one("#plot-advanced")
            )
            table_advanced_contents = _collapsible_contents(
                app.screen.query_one("#table-advanced")
            )

            for widget in (plot_advanced_contents, table_advanced_contents):
                assert widget.styles.overflow_y != "auto"
                assert widget.styles.max_height is None

    asyncio.run(_run())


def test_file_remove_buttons_keep_safe_gap_from_scrollbar() -> None:
    async def _run() -> None:
        app = NdaxTuiApp()
        async with app.run_test(size=(84, 30)) as pilot:
            await pilot.pause()

            plot_files = app.screen.query_one("#plot-files", FileList)
            plot_files.add_paths([Path(f"C:/tmp/plot_{i}.ndax") for i in range(12)])
            await pilot.pause()

            plot_pane = app.screen.query_one("#plot-pane")
            plot_remove = app.screen.query_one("#plot-files-remove-0")
            plot_gap = (plot_pane.region.x + plot_pane.region.width) - (
                plot_remove.region.x + plot_remove.region.width
            )
            assert plot_gap >= 4

            tabs = app.screen.query_one("#workflow-tabs")
            tabs.active = "table-tab"
            await pilot.pause()

            table_files = app.screen.query_one("#table-files", FileList)
            table_files.add_paths([Path(f"C:/tmp/table_{i}.ndax") for i in range(12)])
            await pilot.pause()

            table_pane = app.screen.query_one("#table-pane")
            table_remove = app.screen.query_one("#table-files-remove-0")
            table_gap = (table_pane.region.x + table_pane.region.width) - (
                table_remove.region.x + table_remove.region.width
            )
            assert table_gap >= 4

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
