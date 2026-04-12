import asyncio

from textual.containers import Vertical
from textual.widgets import Input

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


def test_palette_preview_renders_rows_and_combined_block_on_white() -> None:
    preview = PalettePreview(["#1718FE", "#D35400", "#128A0C"])
    rendered = preview._render_preview()
    lines = rendered.plain.splitlines()

    assert lines[0].startswith("#1718FE")
    assert lines[1].startswith("#D35400")
    assert lines[2].startswith("#128A0C")
    assert "Combined preview" in rendered.plain
    assert lines[-1].startswith("#1718FE")
    assert "#D35400" in lines[-1]
    assert "#128A0C" in lines[-1]
    assert "██████" in lines[-1]
    assert any("on white" in str(span.style) for span in rendered.spans)
