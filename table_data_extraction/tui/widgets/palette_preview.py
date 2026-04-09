from __future__ import annotations

from collections.abc import Sequence

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

    def _render_preview(self) -> Text:
        text = Text()
        if not self._palette_colors:
            text.append("No palette colors configured.", style="black on white")
            return text

        for index, color in enumerate(self._palette_colors):
            sample = f" {index + 1}. ╱╲╱╲╱╲ {color} "
            text.append(sample, style=f"{color} on white")
            if index < len(self._palette_colors) - 1:
                text.append("\n", style="black on white")
        return text

    def set_colors(self, colors: Sequence[str]) -> None:
        self._palette_colors = tuple(
            color.strip() for color in colors if color.strip()
        )
        self.update(self._render_preview())
