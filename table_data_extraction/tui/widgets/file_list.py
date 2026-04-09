from __future__ import annotations

from pathlib import Path
from typing import Sequence

from textual import events
from textual.widgets import Static

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
        self.set_paths(paths)

    def _render_text(self) -> str:
        if not self.paths:
            return "No NDAX files selected."
        return "\n".join(f"{index}. {path}" for index, path in enumerate(self.paths, start=1))

    def set_paths(self, paths: Sequence[Path]) -> None:
        self.paths = tuple(Path(path) for path in paths)
        self.update(self._render_text())

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
        self.update(self._render_text())

    def clear_paths(self) -> None:
        self.paths = ()
        self.update(self._render_text())

    def on_paste(self, event: events.Paste) -> None:
        dropped_paths = parse_dropped_paths(event.text)
        if dropped_paths:
            self.add_paths(dropped_paths)
            event.stop()
