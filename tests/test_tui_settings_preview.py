import asyncio

import pytest
from textual.containers import Vertical
from textual.widgets import Input, Label

from table_data_extraction.tui.app import NdaxTuiApp
from table_data_extraction.tui.widgets.palette_preview import PalettePreview


def test_settings_preview_uses_vertical_flow_and_spans_full_section() -> None:
    async def _run() -> None:
        app = NdaxTuiApp()
        async with app.run_test(size=(100, 36)) as pilot:
            await pilot.press("f8")
            await pilot.pause()

            palette_row = app.screen.query_one("#settings-palette-row", Vertical)
            preview_panel = app.screen.query_one("#settings-preview-panel", Vertical)
            palette_input = app.screen.query_one("#settings-palette", Input)

            assert palette_row.region.y < preview_panel.region.y
            assert abs(preview_panel.region.x - palette_input.region.x) <= 1
            assert preview_panel.region.width >= palette_input.region.width - 2

    asyncio.run(_run())


def test_settings_top_actions_match_main_screen_alignment() -> None:
    async def _run() -> None:
        app = NdaxTuiApp()
        async with app.run_test(size=(100, 36)) as pilot:
            await pilot.pause()

            main_actions = app.screen.query_one("#main-top-actions")
            main_primary = app.screen.query_one("#open-settings")
            main_exit = app.screen.query_one("#exit-app")

            await pilot.press("f8")
            await pilot.pause()

            settings_actions = app.screen.query_one("#settings-top-actions")
            settings_primary = app.screen.query_one("#settings-main-menu")
            settings_exit = app.screen.query_one("#settings-exit-app")

            assert settings_actions.region.x == main_actions.region.x
            assert settings_actions.region.width == main_actions.region.width
            assert settings_primary.region.x == main_primary.region.x
            assert settings_primary.region.width == main_primary.region.width
            assert settings_exit.region.x == main_exit.region.x
            assert settings_exit.region.width == main_exit.region.width

    asyncio.run(_run())


def test_settings_defaults_use_persistent_labels_without_placeholders() -> None:
    async def _run() -> None:
        app = NdaxTuiApp()
        async with app.run_test(size=(100, 36)) as pilot:
            await pilot.press("f8")
            await pilot.pause()

            for label_id, expected_text in (
                ("#settings-label-plot-x", "Plot X column"),
                ("#settings-label-plot-y", "Plot Y column"),
                ("#settings-label-csv-columns", "CSV columns"),
                ("#settings-label-window-points", "Window points"),
                ("#settings-label-zero-threshold", "Zero threshold"),
                ("#settings-label-min-zone-points", "Minimum zone points"),
                (
                    "#settings-label-min-extrema-separation-points",
                    "Minimum extrema separation points",
                ),
            ):
                label = app.screen.query_one(label_id, Label)
                assert label.content == expected_text

            for input_id in (
                "#settings-plot-x",
                "#settings-plot-y",
                "#settings-csv-columns",
                "#settings-window-points",
                "#settings-zero-threshold",
                "#settings-min-zone-points",
                "#settings-min-extrema-separation-points",
            ):
                control = app.screen.query_one(input_id, Input)
                assert control.placeholder == ""

    asyncio.run(_run())


@pytest.mark.parametrize("size", [(72, 24), (68, 20)])
def test_settings_actions_remain_visible_on_small_viewports(
    size: tuple[int, int]
) -> None:
    async def _run() -> None:
        app = NdaxTuiApp()
        async with app.run_test(size=size) as pilot:
            await pilot.press("f8")
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
                assert widget.region.x + widget.region.width <= size[0]
                assert widget.region.y + widget.region.height <= size[1]

    asyncio.run(_run())


@pytest.mark.parametrize("size", [(64, 18), (60, 18)])
def test_settings_actions_and_preview_hold_on_tighter_viewports(
    size: tuple[int, int]
) -> None:
    async def _run() -> None:
        app = NdaxTuiApp()
        async with app.run_test(size=size) as pilot:
            await pilot.press("f8")
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
                assert widget.region.x + widget.region.width <= size[0]
                assert widget.region.y + widget.region.height <= size[1]

            panel = app.screen.query_one("#settings-preview-panel")
            preview = app.screen.query_one("#settings-palette-preview", PalettePreview)
            assert preview.region.width <= panel.region.width
            assert preview.region.height <= panel.region.height

            palette_value = app.screen.query_one("#settings-palette", Input).value
            expected_colors = tuple(palette_value.split())
            preview_lines = [
                line
                for line in preview.content.plain.splitlines()
                if line.startswith("#")
            ]
            assert "Combined preview" not in preview.content.plain
            assert len(preview_lines) == len(expected_colors)
            for expected_color, row in zip(expected_colors, preview_lines):
                assert row.startswith(expected_color)
                assert row.count("~") >= 12

    asyncio.run(_run())


@pytest.mark.parametrize("size", [(76, 24), (70, 20)])
def test_palette_preview_stays_within_white_block_on_small_viewports(
    size: tuple[int, int]
) -> None:
    async def _run() -> None:
        app = NdaxTuiApp()
        async with app.run_test(size=size) as pilot:
            await pilot.press("f8")
            await pilot.pause()

            panel = app.screen.query_one("#settings-preview-panel")
            preview = app.screen.query_one("#settings-palette-preview", PalettePreview)

            assert panel.region.x >= 0
            assert panel.region.y >= 0
            assert preview.region.x >= panel.region.x
            assert preview.region.y >= panel.region.y
            assert preview.region.x + preview.region.width <= panel.region.x + panel.region.width
            assert preview.region.y + preview.region.height <= panel.region.y + panel.region.height
            assert preview.region.width <= panel.region.width
            assert preview.region.height <= panel.region.height

    asyncio.run(_run())


def test_palette_preview_renders_only_color_rows_with_long_white_lanes() -> None:
    preview = PalettePreview(["#1718FE", "#D35400", "#128A0C"])
    rendered = preview._render_preview()
    lines = [line for line in rendered.plain.splitlines() if line.startswith("#")]

    assert "Combined preview" not in rendered.plain
    assert len(lines) == 3
    assert lines[0].startswith("#1718FE")
    assert lines[1].startswith("#D35400")
    assert lines[2].startswith("#128A0C")
    assert all(line.count("~") >= 12 for line in lines)
    assert any("on white" in str(span.style) for span in rendered.spans)
