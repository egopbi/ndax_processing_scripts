import asyncio

from table_data_extraction.tui.app import NdaxTuiApp
from table_data_extraction.tui.screens.settings_screen import SettingsScreen
from table_data_extraction.tui.widgets.palette_preview import PalettePreview


def test_app_mounts_main_screen_widgets() -> None:
    async def _run() -> None:
        app = NdaxTuiApp()
        async with app.run_test() as pilot:
            assert app.screen.query_one("#main-top-bar")
            assert app.screen.query_one("#workflow-tabs")
            assert app.screen.query_one("#run-log")
            assert app.screen.query_one("#exit-app")
            assert app.screen.query_one("#run-active")
            assert len(app.screen.query("#run-log")) == 1
            assert len(app.screen.query("#run-status")) == 0
            assert len(app.screen.query("#command-preview")) == 0
            assert len(app.screen.query("#last-output-path")) == 0
            assert len(app.screen.query("#cancel-run")) == 0
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
            assert app.screen.query_one("#settings-top-bar")
            assert app.screen.query_one("#settings-plot-x")
            assert app.screen.query_one("#settings-palette-preview", PalettePreview)

    asyncio.run(_run())
