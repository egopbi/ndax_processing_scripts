from __future__ import annotations

from collections.abc import Sequence

from rich.color import Color
from rich.text import Text
from textual._context import NoActiveAppError
from textual.widgets import Static


class PalettePreview(Static):
    _WAVE_PATTERN = "~~~~~~"
    _SAMPLE_LANE_WIDTH = 10

    def __init__(
        self,
        colors: Sequence[str] = (),
        *,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(id=id, classes=classes)
        self._palette_colors: tuple[str, ...] = ()
        self._pending_render: Text | None = None
        self.set_colors(colors)

    @staticmethod
    def _foreground_for_color(color: str) -> str:
        try:
            parsed = Color.parse(color)
        except Exception:
            return "black"

        triplet = parsed.triplet
        if triplet is None:
            return color

        red, green, blue = triplet
        brightness = (red * 299 + green * 587 + blue * 114) / 1000
        if brightness >= 180:
            return "black"
        return color

    @staticmethod
    def _sample_for_color(color: str) -> str:
        try:
            Color.parse(color)
        except Exception:
            return "black"
        return color

    @classmethod
    def _wave_lane(cls) -> str:
        # Keep the wave centered in a fixed-width sample lane while preserving
        # compatibility with tests that expect the line to end with tildes.
        return cls._WAVE_PATTERN.center(cls._SAMPLE_LANE_WIDTH).rstrip()

    def _render_preview(self) -> Text:
        text = Text()
        if not self._palette_colors:
            text.append("No palette colors configured.", style="black on white")
            return text

        for index, color in enumerate(self._palette_colors):
            foreground = self._foreground_for_color(color)
            sample = self._sample_for_color(color)
            wave_lane = self._wave_lane()
            wave_start = wave_lane.index(self._WAVE_PATTERN)
            row = Text(style="black on white")
            row.append(color, style=f"{foreground} on white")
            row.append(" ", style="black on white")
            lane_start = len(row.plain)
            row.append(wave_lane, style="black on white")
            row.stylize(
                f"bold {sample} on white",
                lane_start + wave_start,
                lane_start + wave_start + len(self._WAVE_PATTERN),
            )
            text.append_text(row)
            if index < len(self._palette_colors) - 1:
                text.append("\n", style="black on white")
        return text

    def _sync_render(self) -> None:
        content = self._render_preview()
        try:
            self.update(content)
        except NoActiveAppError:
            self._pending_render = content

    def set_colors(self, colors: Sequence[str]) -> None:
        self._palette_colors = tuple(
            color.strip() for color in colors if color.strip()
        )
        self._sync_render()

    def on_mount(self) -> None:
        if self._pending_render is not None:
            self.update(self._pending_render)
            self._pending_render = None
