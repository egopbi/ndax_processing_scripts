from __future__ import annotations

from collections.abc import Sequence

from rich.color import Color
from rich.text import Text
from textual.widgets import Static


class PalettePreview(Static):
    def __init__(
        self,
        colors: Sequence[str] = (),
        *,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(id=id, classes=classes)
        self._palette_colors: tuple[str, ...] = ()
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

    def _render_preview(self) -> Text:
        text = Text()
        if not self._palette_colors:
            text.append("No palette colors configured.", style="black on white")
            return text

        for index, color in enumerate(self._palette_colors):
            foreground = self._foreground_for_color(color)
            text.append(color, style=f"bold {foreground} on white")
            if index < len(self._palette_colors) - 1:
                text.append("\n", style="black on white")
        return text

    def set_colors(self, colors: Sequence[str]) -> None:
        self._palette_colors = tuple(
            color.strip() for color in colors if color.strip()
        )
        self.update(self._render_preview())
