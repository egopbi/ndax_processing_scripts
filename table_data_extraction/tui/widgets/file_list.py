from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Sequence

from textual import events
from textual.containers import Horizontal
from textual.widgets import Button, Static
from rich.text import Text

from table_data_extraction.tui.path_drop import parse_dropped_paths

FILE_LIST_ACCENT = "#6db7ff"
FILE_LIST_SELECTED = "#b5bcc7"


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
        self._pending_refresh = False
        self.paths_changed_callback: Callable[[tuple[Path, ...]], None] | None = None
        self.set_paths(paths)

    def _remove_button_prefix(self) -> str:
        widget_id = self.id or "file-list"
        return f"{widget_id}-remove-"

    def _remove_button_id(self, index: int) -> str:
        return f"{self._remove_button_prefix()}{index}"

    def _render_text(self) -> Text:
        if not self.paths:
            text = Text()
            text.append("No NDAX files selected.", style=f"bold {FILE_LIST_ACCENT}")
            return text

        lines = Text()
        for index, path in enumerate(self.paths, start=1):
            if lines:
                lines.append("\n")
            lines.append(f"{index}. ", style="dim")
            lines.append(str(path), style=f"bold {FILE_LIST_SELECTED}")
        return lines

    def _build_file_row(self, index: int, path: Path) -> Horizontal:
        path_text = Text()
        path_text.append(f"{index + 1}. ", style="dim")
        path_text.append(str(path), style=f"bold {FILE_LIST_SELECTED}")

        path_label = Static(path_text, classes="file-list-path")
        path_label.styles.width = "1fr"

        remove_button = Button(
            "-",
            id=self._remove_button_id(index),
            classes="file-list-remove",
        )
        remove_button.styles.width = 3
        remove_button.styles.min_width = 3

        row = Horizontal(
            path_label,
            remove_button,
            classes="file-list-row",
        )
        row.styles.width = "1fr"
        row.styles.height = "auto"
        return row

    def _sync_render(self) -> None:
        if not self.is_mounted:
            self._pending_refresh = True
            return

        self._pending_refresh = False
        self.remove_children()
        if not self.paths:
            self.mount(Static(self._render_text(), classes="file-list-empty"))
            return

        for index, path in enumerate(self.paths):
            self.mount(self._build_file_row(index, path))

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

    def remove_path_at(self, index: int) -> None:
        if index < 0 or index >= len(self.paths):
            return

        remaining = list(self.paths)
        del remaining[index]
        self.paths = tuple(remaining)
        self._sync_render()
        self._notify_paths_changed()

    def on_mount(self) -> None:
        if self._pending_refresh:
            self._sync_render()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id is None:
            return

        prefix = self._remove_button_prefix()
        if not button_id.startswith(prefix):
            return

        index_text = button_id.removeprefix(prefix)
        if not index_text.isdigit():
            return

        self.remove_path_at(int(index_text))
        event.stop()

    def on_paste(self, event: events.Paste) -> None:
        dropped_paths = parse_dropped_paths(event.text)
        if dropped_paths:
            self.add_paths(dropped_paths)
            event.stop()
