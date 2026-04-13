from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
import re

from textual import events
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label, SelectionList, Static
from textual.widgets.selection_list import Selection


class ManageFilesScreen(ModalScreen[tuple[Path, ...] | None]):
    AUTO_FOCUS = ""

    BINDINGS = [
        ("escape", "dismiss(None)", "Cancel"),
    ]

    CSS = """
    ManageFilesScreen {
        align: center middle;
    }

    #manage-files-dialog {
        width: 80%;
        height: 85%;
        max-height: 24;
        min-height: 12;
        background: #20242b;
        border: ascii #6db7ff;
        padding: 1 2;
    }

    #manage-files-list {
        margin-top: 1;
        height: 1fr;
        min-height: 3;
        border: ascii #343a43;
        scrollbar-background: #0f1216;
        scrollbar-background-hover: #0f1216;
        scrollbar-background-active: #0f1216;
        scrollbar-color: #6db7ff;
        scrollbar-color-hover: #8cc8ff;
        scrollbar-color-active: #6db7ff;
        scrollbar-gutter: stable;
    }

    #manage-files-actions {
        dock: bottom;
        height: auto;
        margin-top: 1;
        background: #20242b;
    }

    .manage-files-action-row {
        width: 1fr;
        height: auto;
        background: #20242b;
    }

    .manage-files-action-row Button {
        width: 1fr;
        margin: 0;
    }
    """

    def __init__(self, paths: Sequence[Path]) -> None:
        super().__init__()
        self._paths = tuple(Path(path) for path in paths)

    def compose(self):
        with Vertical(id="manage-files-dialog"):
            yield Label("Manage Files", id="manage-files-title")
            yield Static(
                "Select one or more files to remove from the shared file list.",
                id="manage-files-description",
            )
            if self._paths:
                yield SelectionList[Path](
                    *[
                        Selection(
                            self._tail_focused_path_label(path, max_chars=64),
                            path,
                        )
                        for path in self._paths
                    ],
                    id="manage-files-list",
                )
            else:
                yield Static("No files available.", id="manage-files-empty")
            with Vertical(id="manage-files-actions"):
                with Horizontal(classes="manage-files-action-row"):
                    yield Button(
                        "Select All",
                        id="manage-files-select-all",
                    )
                    yield Button(
                        "Clear Selection",
                        id="manage-files-clear-selection",
                    )
                with Horizontal(classes="manage-files-action-row"):
                    yield Button(
                        "Remove Selected",
                        id="manage-files-remove",
                        disabled=True,
                    )
                    yield Button("Cancel", id="manage-files-cancel")

    def _selection_list(self) -> SelectionList[Path] | None:
        matches = list(self.query(SelectionList))
        if not matches:
            return None
        return matches[0]

    def _sync_remove_button(self) -> None:
        button = self.query_one("#manage-files-remove", Button)
        selection_list = self._selection_list()
        button.disabled = selection_list is None or not selection_list.selected

    def _remaining_paths(self) -> tuple[Path, ...]:
        selection_list = self._selection_list()
        if selection_list is None:
            return self._paths
        selected = set(selection_list.selected)
        return tuple(path for path in self._paths if path not in selected)

    def on_mount(self) -> None:
        self.call_after_refresh(self._refresh_displayed_path_labels)
        self._sync_remove_button()

    def on_resize(self, _event: events.Resize) -> None:
        self._refresh_displayed_path_labels()

    def on_selection_list_selected_changed(
        self,
        _event: SelectionList.SelectedChanged[Path],
    ) -> None:
        self._sync_remove_button()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        selection_list = self._selection_list()

        if button_id == "manage-files-select-all":
            if selection_list is not None:
                selection_list.select_all()
            self._sync_remove_button()
            return

        if button_id == "manage-files-clear-selection":
            if selection_list is not None:
                selection_list.deselect_all()
            self._sync_remove_button()
            return

        if button_id == "manage-files-remove":
            self.dismiss(self._remaining_paths())
            return

        if button_id == "manage-files-cancel":
            self.dismiss(None)

    @staticmethod
    def _tail_focused_path_label(path: Path, *, max_chars: int) -> str:
        path_text = str(path)
        if max_chars <= 0 or len(path_text) <= max_chars:
            return path_text
        if max_chars <= 4:
            return path_text[-max_chars:]

        separator = "\\" if "\\" in path_text else "/"
        normalized_parts = [part for part in re.split(r"[\\/]+", path_text) if part]
        if not normalized_parts:
            return "..." + path_text[-(max_chars - 3):]

        tail = normalized_parts[-1]
        max_tail_length = max_chars - 3
        for part in reversed(normalized_parts[:-1]):
            candidate = f"{part}/{tail}"
            if len(candidate) > max_tail_length:
                break
            tail = candidate

        if len(tail) > max_tail_length:
            tail = tail[-max_tail_length:]
        tail = tail.replace("/", separator)

        if separator in tail:
            return f"...{separator}{tail}"
        return f"...{tail}"

    def _display_label_width(self) -> int:
        selection_list = self._selection_list()
        if selection_list is None or selection_list.size.width <= 0:
            return 48
        # Keep room for checkbox glyphs, paddings, and vertical scrollbar.
        return max(18, selection_list.size.width - 8)

    def _refresh_displayed_path_labels(self) -> None:
        selection_list = self._selection_list()
        if selection_list is None:
            return

        selected_paths = set(selection_list.selected)
        max_chars = self._display_label_width()
        selection_list.set_options(
            [
                Selection(
                    self._tail_focused_path_label(path, max_chars=max_chars),
                    path,
                    initial_state=path in selected_paths,
                )
                for path in self._paths
            ]
        )
        self._sync_remove_button()
