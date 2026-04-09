from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Sequence

from textual import events
from textual._context import NoActiveAppError
from textual.widgets import Static
from rich.text import Text

from table_data_extraction.tui.path_drop import parse_dropped_paths


class FileList(Static):
    def __init__(
        self,
        paths: Sequence[Path] = (),
        *,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(id=id, classes=classes)
        self.paths: tuple[Path, ...] = ()
        self._pending_render: Text | None = None
        self.paths_changed_callback: Callable[[tuple[Path, ...]], None] | None = None
        self.set_paths(paths)

    def _render_text(self) -> Text:
        if not self.paths:
            return Text("No NDAX files selected.", style="dim")

        lines = Text()
        for index, path in enumerate(self.paths, start=1):
            if lines:
                lines.append("\n")
            lines.append(f"{index}. ", style="dim")
            lines.append(str(path), style="bold #6bdcff")
        return lines

    def _sync_render(self) -> None:
        content = self._render_text()
        try:
            self.update(content)
        except NoActiveAppError:
            self._pending_render = content

    def _notify_paths_changed(self) -> None:
        if self.paths_changed_callback is not None:
            self.paths_changed_callback(self.paths)

    def set_paths(self, paths: Sequence[Path]) -> None:
        self.paths = tuple(Path(path) for path in paths)
        self._sync_render()
        self._notify_paths_changed()

    def add_paths(self, paths: Sequence[Path]) -> None:
        existing = list(self.paths)
        seen = {str(path) for path in existing}
        for path in paths:
            candidate = Path(path)
            key = str(candidate)
            if key in seen:
                continue
            existing.append(candidate)
            seen.add(key)
        self.paths = tuple(existing)
        self._sync_render()
        self._notify_paths_changed()

    def clear_paths(self) -> None:
        self.paths = ()
        self._sync_render()
        self._notify_paths_changed()

    def on_mount(self) -> None:
        if self._pending_render is not None:
            self.update(self._pending_render)
            self._pending_render = None

    def on_paste(self, event: events.Paste) -> None:
        dropped_paths = parse_dropped_paths(event.text)
        if dropped_paths:
            self.add_paths(dropped_paths)
            event.stop()
