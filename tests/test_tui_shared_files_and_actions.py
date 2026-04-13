import asyncio
from pathlib import Path

from textual.widgets import Button, Select

from table_data_extraction.tui.app import NdaxTuiApp
from table_data_extraction.tui.widgets.file_list import FileList


def test_shared_files_persist_across_mode_switches() -> None:
    async def _run() -> None:
        app = NdaxTuiApp()
        async with app.run_test(size=(96, 36)) as pilot:
            shared_files = app.screen.query_one("#shared-files", FileList)
            mode_select = app.screen.query_one("#mode-select", Select)

            shared_files.add_paths([Path("plot-a.ndax"), Path("plot-b.ndax")])
            await pilot.pause()
            assert shared_files.paths == (
                Path("plot-a.ndax"),
                Path("plot-b.ndax"),
            )

            mode_select.value = "table"
            await pilot.pause()
            assert app.screen.current_mode == "table"
            assert shared_files.paths == (
                Path("plot-a.ndax"),
                Path("plot-b.ndax"),
            )

            mode_select.value = "convert"
            await pilot.pause()
            assert app.screen.current_mode == "convert"
            assert shared_files.paths == (
                Path("plot-a.ndax"),
                Path("plot-b.ndax"),
            )

            mode_select.value = "plot"
            await pilot.pause()
            assert app.screen.current_mode == "plot"
            assert shared_files.paths == (
                Path("plot-a.ndax"),
                Path("plot-b.ndax"),
            )

    asyncio.run(_run())


def test_settings_top_actions_include_exit_and_match_main_structure() -> None:
    async def _run() -> None:
        app = NdaxTuiApp()
        async with app.run_test(size=(96, 36)) as pilot:
            main_actions = app.screen.query_one("#main-top-actions")
            assert "top-actions" in set(main_actions.classes)
            assert "top-action-button" in set(
                app.screen.query_one("#open-settings", Button).classes
            )
            assert "top-action-button" in set(
                app.screen.query_one("#exit-app", Button).classes
            )

            await pilot.press("f8")
            await pilot.pause()

            settings_actions = app.screen.query_one("#settings-top-actions")
            assert "top-actions" in set(settings_actions.classes)
            settings_main_menu = app.screen.query_one("#settings-main-menu", Button)
            settings_exit = app.screen.query_one("#settings-exit-app", Button)
            assert "top-action-button" in set(settings_main_menu.classes)
            assert "top-action-button" in set(settings_exit.classes)
            assert settings_actions.region.x + settings_actions.region.width <= (
                app.screen.query_one("#settings-top-bar").region.x
                + app.screen.query_one("#settings-top-bar").region.width
            )

    asyncio.run(_run())


def test_file_action_buttons_update_shared_files(monkeypatch) -> None:
    async def _run() -> None:
        app = NdaxTuiApp()

        async with app.run_test(size=(96, 36)) as pilot:
            def _fake_choose_files() -> None:
                app.call_from_thread(
                    app.screen._apply_selected_files,
                    (Path("button-a.ndax"), Path("button-b.ndax")),
                )

            monkeypatch.setattr(app.screen, "_choose_files_in_thread", _fake_choose_files)

            await pilot.click("#shared-add-files")
            await pilot.pause()

            shared_files = app.screen.query_one("#shared-files", FileList)
            assert shared_files.paths == (
                Path("button-a.ndax"),
                Path("button-b.ndax"),
            )

            await pilot.click("#shared-clear-files")
            await pilot.pause()
            assert shared_files.paths == ()

    asyncio.run(_run())


def test_settings_exit_button_calls_app_exit(monkeypatch) -> None:
    async def _run() -> None:
        app = NdaxTuiApp()
        exit_calls: list[bool] = []

        async with app.run_test(size=(96, 36)) as pilot:
            monkeypatch.setattr(app, "action_exit_app", lambda: exit_calls.append(True))

            await pilot.press("f8")
            await pilot.pause()
            await pilot.click("#settings-exit-app")
            await pilot.pause()

            assert exit_calls == [True]

    asyncio.run(_run())
