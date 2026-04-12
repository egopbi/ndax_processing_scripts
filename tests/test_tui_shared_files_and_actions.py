import asyncio
from pathlib import Path

from textual.widgets import Button

from table_data_extraction.tui.app import NdaxTuiApp
from table_data_extraction.tui.widgets.file_list import FileList


def test_files_are_shared_between_plot_and_table_modes() -> None:
    async def _run() -> None:
        app = NdaxTuiApp()
        async with app.run_test(size=(96, 36)) as pilot:
            plot_files = app.screen.query_one("#plot-files", FileList)
            table_files = app.screen.query_one("#table-files", FileList)

            plot_files.add_paths([Path("plot-a.ndax"), Path("plot-b.ndax")])
            await pilot.pause()
            assert table_files.paths == (
                Path("plot-a.ndax"),
                Path("plot-b.ndax"),
            )

            table_files.add_paths([Path("table-c.ndax")])
            await pilot.pause()
            assert plot_files.paths == (
                Path("plot-a.ndax"),
                Path("plot-b.ndax"),
                Path("table-c.ndax"),
            )

            table_files.clear_paths()
            await pilot.pause()
            assert plot_files.paths == ()

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


def test_file_action_buttons_keep_files_shared(monkeypatch) -> None:
    async def _run() -> None:
        app = NdaxTuiApp()

        async with app.run_test(size=(96, 36)) as pilot:
            def _fake_choose_files(tab_id: str) -> None:
                app.call_from_thread(
                    app.screen._apply_selected_files,
                    tab_id,
                    (Path("button-a.ndax"), Path("button-b.ndax")),
                )

            monkeypatch.setattr(app.screen, "_choose_files_in_thread", _fake_choose_files)

            await pilot.click("#plot-add-files")
            await pilot.pause()

            plot_files = app.screen.query_one("#plot-files", FileList)
            table_files = app.screen.query_one("#table-files", FileList)
            assert plot_files.paths == (
                Path("button-a.ndax"),
                Path("button-b.ndax"),
            )
            assert table_files.paths == plot_files.paths

            clear_button = app.screen.query_one("#table-clear-files", Button)
            app.screen.on_button_pressed(Button.Pressed(clear_button))
            await pilot.pause()
            assert plot_files.paths == ()
            assert table_files.paths == ()

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
