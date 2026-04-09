import asyncio

from textual.widgets import Input, Log, Static, TabbedContent

from table_data_extraction.tui.app import NdaxTuiApp
from table_data_extraction.tui.screens.settings_screen import SettingsScreen
from table_data_extraction.tui.widgets.palette_preview import PalettePreview


def test_app_mounts_main_screen_widgets() -> None:
    async def _run() -> None:
        app = NdaxTuiApp()
        async with app.run_test() as pilot:
            assert app.screen.query_one("#workflow-tabs", TabbedContent)
            assert app.screen.query_one("#run-log", Log)
            assert app.screen.query_one("#current-output-dir", Static)
            await pilot.press("f8")
            await pilot.pause()
            assert isinstance(app.screen, SettingsScreen)

    asyncio.run(_run())


def test_settings_screen_shows_palette_preview_and_inputs() -> None:
    async def _run() -> None:
        app = NdaxTuiApp()
        async with app.run_test() as pilot:
            app.push_screen(SettingsScreen())
            await pilot.pause()
            assert app.screen.query_one("#settings-plot-x", Input)
            assert app.screen.query_one("#settings-palette-preview", PalettePreview)

    asyncio.run(_run())
