import asyncio
from pathlib import Path

from textual.app import App
from textual.widgets import Button, Input, SelectionList, Static

from table_data_extraction.tui.screens.advanced_options_screen import (
    AdvancedOptionsResult,
    AdvancedOptionsScreen,
)
from table_data_extraction.tui.screens.manage_files_screen import ManageFilesScreen


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
            app.screen.query_one("#advanced-labels", Input).value = "a, b, c"
            app.screen.query_one("#advanced-output", Input).value = "custom-output"
            await pilot.click("#advanced-save")
            await pilot.pause()

            assert app.screen_result == AdvancedOptionsResult(
                action="save",
                state=app.screen_result.state,
            )
            assert app.screen_result.state.mode == "plot"
            assert app.screen_result.state.labels == "a, b, c"
            assert app.screen_result.state.output_override == "custom-output"

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
            await pilot.click("#advanced-health-check")
            await pilot.pause()

            assert app.screen_result.action == "health-check"
            assert app.screen_result.state.mode == "table"
            assert app.screen_result.state.labels == "label-1,label-2"
            assert app.screen_result.state.output_override == "table.csv"

    asyncio.run(_run())
