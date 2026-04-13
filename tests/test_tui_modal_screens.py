import asyncio
from pathlib import Path

import pytest
from textual.app import App
from textual.css.query import NoMatches
from textual.widgets import Button, Input, SelectionList, Static

from table_data_extraction.tui.screens.advanced_options_screen import (
    AdvancedOptionsResult,
    AdvancedOptionsScreen,
)
from table_data_extraction.tui.models import (
    DEFAULT_PLOT_OUTPUT_HEIGHT_PX,
    DEFAULT_PLOT_OUTPUT_WIDTH_PX,
)
from table_data_extraction.tui.screens.manage_files_screen import ManageFilesScreen
from table_data_extraction.tui.screens.select_columns_screen import (
    SelectColumnsScreen,
)

PROJECT_BLUE_RGB = (109, 183, 255)
PROJECT_BLUE_HOVER_RGB = (140, 200, 255)
MODAL_SURFACE_RGB = (32, 36, 43)


class _ScreenHarnessApp(App[None]):
    AUTO_FOCUS = ""

    def __init__(self, screen) -> None:
        super().__init__()
        self._initial_screen = screen
        self.screen_result = None

    def on_mount(self) -> None:
        self.push_screen(self._initial_screen, self._capture_result)

    def _capture_result(self, result) -> None:
        self.screen_result = result


def test_manage_files_screen_removes_selected_paths() -> None:
    async def _run() -> None:
        app = _ScreenHarnessApp(
            ManageFilesScreen(
                [
                    Path("one.ndax"),
                    Path("two.ndax"),
                    Path("three.ndax"),
                ]
            )
        )
        async with app.run_test(size=(90, 30)) as pilot:
            selection_list = app.screen.query_one("#manage-files-list", SelectionList)
            remove_button = app.screen.query_one("#manage-files-remove", Button)

            assert remove_button.disabled
            selection_list.select(Path("two.ndax"))
            selection_list.select(Path("three.ndax"))
            await pilot.pause()
            assert not remove_button.disabled

            await pilot.click("#manage-files-remove")
            await pilot.pause()

            assert app.screen_result == (Path("one.ndax"),)

    asyncio.run(_run())


def test_manage_files_screen_supports_select_all_and_cancel() -> None:
    async def _run() -> None:
        app = _ScreenHarnessApp(ManageFilesScreen([Path("only.ndax")]))
        async with app.run_test(size=(90, 30)) as pilot:
            selection_list = app.screen.query_one("#manage-files-list", SelectionList)

            await pilot.click("#manage-files-select-all")
            await pilot.pause()
            assert selection_list.selected == [Path("only.ndax")]

            await pilot.click("#manage-files-clear-selection")
            await pilot.pause()
            assert selection_list.selected == []

            await pilot.click("#manage-files-cancel")
            await pilot.pause()
            assert app.screen_result is None

    asyncio.run(_run())


def test_manage_files_screen_handles_empty_state() -> None:
    async def _run() -> None:
        app = _ScreenHarnessApp(ManageFilesScreen([]))
        async with app.run_test(size=(90, 30)) as pilot:
            assert app.screen.query_one("#manage-files-empty", Static).content == "No files available."
            assert app.screen.query_one("#manage-files-remove", Button).disabled
            await pilot.click("#manage-files-cancel")
            await pilot.pause()
            assert app.screen_result is None

    asyncio.run(_run())


def test_manage_files_screen_keeps_action_buttons_visible_on_tight_viewport() -> None:
    async def _run() -> None:
        app = _ScreenHarnessApp(
            ManageFilesScreen(
                [Path(f"/very/long/path/to/cycles/run_{index:02d}/sample_{index:02d}.ndax") for index in range(30)]
            )
        )
        async with app.run_test(size=(84, 20)) as pilot:
            await pilot.pause()
            viewport_height = app.screen.size.height

            for button_id in (
                "#manage-files-select-all",
                "#manage-files-clear-selection",
                "#manage-files-remove",
                "#manage-files-cancel",
            ):
                button = app.screen.query_one(button_id, Button)
                assert button.region.height > 0
                assert button.region.y + button.region.height <= viewport_height

    asyncio.run(_run())


def test_manage_files_screen_action_buttons_have_uniform_width() -> None:
    async def _run() -> None:
        app = _ScreenHarnessApp(ManageFilesScreen([Path(f"sample_{index:02d}.ndax") for index in range(8)]))
        async with app.run_test(size=(90, 24)) as pilot:
            await pilot.pause()
            widths = [
                app.screen.query_one(button_id, Button).region.width
                for button_id in (
                    "#manage-files-select-all",
                    "#manage-files-clear-selection",
                    "#manage-files-remove",
                    "#manage-files-cancel",
                )
            ]
            assert len(set(widths)) == 1

    asyncio.run(_run())


def test_manage_files_screen_action_buttons_have_real_surface_gaps() -> None:
    async def _run() -> None:
        app = _ScreenHarnessApp(ManageFilesScreen([Path(f"sample_{index:02d}.ndax") for index in range(8)]))
        async with app.run_test(size=(90, 24)) as pilot:
            await pilot.pause()
            top_left = app.screen.query_one("#manage-files-select-all", Button)
            top_right = app.screen.query_one("#manage-files-clear-selection", Button)
            bottom_left = app.screen.query_one("#manage-files-remove", Button)

            horizontal_gap = top_right.region.x - (top_left.region.x + top_left.region.width)
            vertical_gap = bottom_left.region.y - (top_left.region.y + top_left.region.height)

            assert horizontal_gap > 0
            assert vertical_gap > 0

    asyncio.run(_run())


def test_manage_files_screen_action_area_uses_modal_surface_background() -> None:
    async def _run() -> None:
        app = _ScreenHarnessApp(ManageFilesScreen([Path(f"sample_{index:02d}.ndax") for index in range(8)]))
        async with app.run_test(size=(90, 24)) as pilot:
            await pilot.pause()
            actions = app.screen.query_one("#manage-files-actions")
            rows = list(app.screen.query(".manage-files-action-row"))
            button_gaps = list(app.screen.query(".manage-files-button-gap"))
            row_gap = app.screen.query_one(".manage-files-row-gap", Static)
            right_button = app.screen.query_one("#manage-files-cancel", Button)

            assert actions.styles.background.rgb == MODAL_SURFACE_RGB
            assert all(row.styles.background.rgb == MODAL_SURFACE_RGB for row in rows)
            assert all(gap.styles.background.rgb == MODAL_SURFACE_RGB for gap in button_gaps)
            assert row_gap.styles.background.rgb == MODAL_SURFACE_RGB
            assert right_button.styles.background.rgb != MODAL_SURFACE_RGB

    asyncio.run(_run())


def test_manage_files_screen_scrollbar_uses_project_blue() -> None:
    async def _run() -> None:
        app = _ScreenHarnessApp(ManageFilesScreen([Path(f"sample_{index:02d}.ndax") for index in range(40)]))
        async with app.run_test(size=(90, 24)) as pilot:
            await pilot.pause()
            selection_list = app.screen.query_one("#manage-files-list", SelectionList)

            assert selection_list.styles.scrollbar_color.rgb == PROJECT_BLUE_RGB
            assert selection_list.styles.scrollbar_color_hover.rgb == PROJECT_BLUE_HOVER_RGB
            assert selection_list.styles.scrollbar_color_active.rgb == PROJECT_BLUE_RGB

    asyncio.run(_run())


def test_manage_files_screen_displays_tail_of_long_paths() -> None:
    async def _run() -> None:
        long_path = Path(
            "/mnt/storage/users/alex/very/deep/location/for/ndax/files/final-parent/sample_001.ndax"
        )
        app = _ScreenHarnessApp(ManageFilesScreen([long_path]))
        async with app.run_test(size=(68, 20)) as pilot:
            await pilot.pause()
            selection_list = app.screen.query_one("#manage-files-list", SelectionList)
            option_text = str(selection_list.get_option_at_index(0).prompt)

            assert option_text.startswith("...")
            assert option_text.endswith("final-parent/sample_001.ndax")
            assert "/mnt/storage/users" not in option_text

            selection_list.select(long_path)
            await pilot.pause()
            assert selection_list.selected == [long_path]

    asyncio.run(_run())


def test_advanced_options_screen_saves_plot_values() -> None:
    async def _run() -> None:
        app = _ScreenHarnessApp(
            AdvancedOptionsScreen(
                mode="plot",
                labels="before",
                output_override="plot.jpg",
            )
        )
        async with app.run_test(size=(90, 30)) as pilot:
            assert app.screen.query_one("#advanced-options-title", Static).content == "Plot Options"
            size_section = app.screen.query_one("#advanced-output-size-section")
            labels_section = app.screen.query_one("#advanced-labels-section")
            width_label = app.screen.query_one("#advanced-label-output-width", Static)
            width_input = app.screen.query_one("#advanced-output-width", Input)
            height_label = app.screen.query_one("#advanced-label-output-height", Static)
            height_input = app.screen.query_one("#advanced-output-height", Input)
            labels_input = app.screen.query_one("#advanced-labels", Input)
            assert size_section.has_class("section-shell")
            assert labels_section.has_class("section-shell")
            assert app.screen.query_one("#advanced-options-title", Static).content == "Plot Options"
            assert width_label.content == "Width (px)"
            assert height_label.content == "Height (px)"
            assert width_input.value == str(DEFAULT_PLOT_OUTPUT_WIDTH_PX)
            assert height_input.value == str(DEFAULT_PLOT_OUTPUT_HEIGHT_PX)
            assert size_section.region.y < labels_input.region.y
            assert width_input.region.y < height_input.region.y
            assert (
                app.screen.query_one("#advanced-labels-label", Static).content
                == "Labels, comma separated"
            )
            app.screen.query_one("#advanced-labels", Input).value = "a, b, c"
            width_input.value = "1800"
            height_input.value = "1200"
            await pilot.click("#advanced-save")
            await pilot.pause()

            assert app.screen_result == AdvancedOptionsResult(
                action="save",
                state=app.screen_result.state,
            )
            assert app.screen_result.state.mode == "plot"
            assert app.screen_result.state.labels == "a, b, c"
            assert app.screen_result.state.output_override == "plot.jpg"
            assert app.screen_result.state.output_width_px == "1800"
            assert app.screen_result.state.output_height_px == "1200"

    asyncio.run(_run())


def test_advanced_options_screen_can_request_health_check_for_table() -> None:
    async def _run() -> None:
        app = _ScreenHarnessApp(
            AdvancedOptionsScreen(
                mode="table",
                labels="label-1,label-2",
                output_override="table.csv",
            )
        )
        async with app.run_test(size=(90, 30)) as pilot:
            assert (
                app.screen.query_one("#advanced-options-title", Static).content
                == "Comparison Table Options"
            )
            assert app.screen.query_one("#advanced-labels-section")
            with pytest.raises(NoMatches):
                app.screen.query_one("#advanced-output-size-section")
            with pytest.raises(NoMatches):
                app.screen.query_one("#advanced-output-width", Input)
            await pilot.click("#advanced-health-check")
            await pilot.pause()

            assert app.screen_result.action == "health-check"
            assert app.screen_result.state.mode == "table"
            assert app.screen_result.state.labels == "label-1,label-2"
            assert app.screen_result.state.output_override == "table.csv"

    asyncio.run(_run())


def test_select_columns_screen_locks_time_and_applies_selection() -> None:
    async def _run() -> None:
        app = _ScreenHarnessApp(
            SelectColumnsScreen(
                ["Time", "Voltage", "Current(mA)"],
                selected_columns=["Time", "Voltage"],
                locked_columns=["Time"],
            )
        )
        async with app.run_test(size=(90, 30)) as pilot:
            selection_list = app.screen.query_one("#select-columns-list", SelectionList)
            apply_button = app.screen.query_one("#select-columns-apply", Button)

            assert selection_list.selected == ["Time", "Voltage"]
            assert not apply_button.disabled

            await pilot.click("#select-columns-clear-selected")
            await pilot.pause()
            assert selection_list.selected == ["Time"]
            assert not apply_button.disabled

            await pilot.click("#select-columns-apply")
            await pilot.pause()
            assert app.screen_result == ("Time",)

    asyncio.run(_run())


def test_select_columns_screen_handles_empty_state() -> None:
    async def _run() -> None:
        app = _ScreenHarnessApp(
            SelectColumnsScreen(
                [],
                selected_columns=[],
            )
        )
        async with app.run_test(size=(90, 30)) as pilot:
            assert app.screen.query_one("#select-columns-empty", Static).content == "No columns available."
            assert app.screen.query_one("#select-columns-apply", Button).disabled
            await pilot.click("#select-columns-cancel")
            await pilot.pause()
            assert app.screen_result is None

    asyncio.run(_run())


def test_select_columns_screen_keeps_action_buttons_visible_on_tight_viewport() -> None:
    async def _run() -> None:
        app = _ScreenHarnessApp(
            SelectColumnsScreen(
                [f"Column {index:02d}" for index in range(40)],
                selected_columns=["Column 00"],
            )
        )
        async with app.run_test(size=(84, 20)) as pilot:
            await pilot.pause()
            viewport_height = app.screen.size.height

            for button_id in (
                "#select-columns-select-all",
                "#select-columns-clear-selected",
                "#select-columns-apply",
                "#select-columns-cancel",
            ):
                button = app.screen.query_one(button_id, Button)
                assert button.region.height > 0
                assert button.region.y + button.region.height <= viewport_height

    asyncio.run(_run())


def test_select_columns_screen_action_buttons_have_uniform_width() -> None:
    async def _run() -> None:
        app = _ScreenHarnessApp(
            SelectColumnsScreen(
                [f"Column {index:02d}" for index in range(12)],
                selected_columns=["Column 00"],
            )
        )
        async with app.run_test(size=(90, 24)) as pilot:
            await pilot.pause()
            widths = [
                app.screen.query_one(button_id, Button).region.width
                for button_id in (
                    "#select-columns-select-all",
                    "#select-columns-clear-selected",
                    "#select-columns-apply",
                    "#select-columns-cancel",
                )
            ]
            assert len(set(widths)) == 1

    asyncio.run(_run())


def test_select_columns_screen_action_buttons_have_real_surface_gaps() -> None:
    async def _run() -> None:
        app = _ScreenHarnessApp(
            SelectColumnsScreen(
                [f"Column {index:02d}" for index in range(12)],
                selected_columns=["Column 00"],
            )
        )
        async with app.run_test(size=(90, 24)) as pilot:
            await pilot.pause()
            top_left = app.screen.query_one("#select-columns-select-all", Button)
            top_right = app.screen.query_one("#select-columns-clear-selected", Button)
            bottom_left = app.screen.query_one("#select-columns-apply", Button)

            horizontal_gap = top_right.region.x - (top_left.region.x + top_left.region.width)
            vertical_gap = bottom_left.region.y - (top_left.region.y + top_left.region.height)

            assert horizontal_gap > 0
            assert vertical_gap > 0

    asyncio.run(_run())


def test_select_columns_screen_action_area_uses_modal_surface_background() -> None:
    async def _run() -> None:
        app = _ScreenHarnessApp(
            SelectColumnsScreen(
                [f"Column {index:02d}" for index in range(12)],
                selected_columns=["Column 00"],
            )
        )
        async with app.run_test(size=(90, 24)) as pilot:
            await pilot.pause()
            actions = app.screen.query_one("#select-columns-actions")
            rows = list(app.screen.query(".select-columns-action-row"))
            button_gaps = list(app.screen.query(".select-columns-button-gap"))
            row_gap = app.screen.query_one(".select-columns-row-gap", Static)
            right_button = app.screen.query_one("#select-columns-cancel", Button)

            assert actions.styles.background.rgb == MODAL_SURFACE_RGB
            assert all(row.styles.background.rgb == MODAL_SURFACE_RGB for row in rows)
            assert all(gap.styles.background.rgb == MODAL_SURFACE_RGB for gap in button_gaps)
            assert row_gap.styles.background.rgb == MODAL_SURFACE_RGB
            assert right_button.styles.background.rgb != MODAL_SURFACE_RGB

    asyncio.run(_run())


def test_select_columns_screen_scrollbar_uses_project_blue() -> None:
    async def _run() -> None:
        app = _ScreenHarnessApp(
            SelectColumnsScreen(
                [f"Column {index:02d}" for index in range(40)],
                selected_columns=["Column 00"],
            )
        )
        async with app.run_test(size=(90, 24)) as pilot:
            await pilot.pause()
            selection_list = app.screen.query_one("#select-columns-list", SelectionList)

            assert selection_list.styles.scrollbar_color.rgb == PROJECT_BLUE_RGB
            assert selection_list.styles.scrollbar_color_hover.rgb == PROJECT_BLUE_HOVER_RGB
            assert selection_list.styles.scrollbar_color_active.rgb == PROJECT_BLUE_RGB

    asyncio.run(_run())
