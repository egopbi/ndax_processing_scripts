from __future__ import annotations

from collections.abc import Sequence

from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label, SelectionList, Static
from textual.widgets.selection_list import Selection


class SelectColumnsScreen(ModalScreen[tuple[str, ...] | None]):
    AUTO_FOCUS = ""

    BINDINGS = [
        ("escape", "dismiss(None)", "Cancel"),
    ]

    CSS = """
    SelectColumnsScreen {
        align: center middle;
    }

    #select-columns-dialog {
        width: 80%;
        height: 85%;
        max-height: 24;
        min-height: 12;
        background: #20242b;
        border: ascii #6db7ff;
        padding: 1 2;
    }

    #select-columns-list {
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

    #select-columns-actions {
        dock: bottom;
        height: auto;
        margin-top: 1;
        background: #20242b;
    }

    .select-columns-action-row {
        width: 1fr;
        height: auto;
        background: #20242b;
    }

    .select-columns-action-row Button {
        width: 1fr;
        margin: 0;
    }
    """

    def __init__(
        self,
        columns: Sequence[str],
        *,
        selected_columns: Sequence[str],
        locked_columns: Sequence[str] = (),
    ) -> None:
        super().__init__()
        self._columns = tuple(str(column) for column in columns)
        self._selected_columns = {
            str(column) for column in selected_columns if str(column) in self._columns
        }
        self._locked_columns = {
            str(column) for column in locked_columns if str(column) in self._columns
        }

    def compose(self):
        with Vertical(id="select-columns-dialog"):
            yield Label("Select Columns", id="select-columns-title")
            yield Static(
                "Choose columns to include in CSV output files.",
                id="select-columns-description",
            )
            if self._columns:
                yield SelectionList[str](
                    *[
                        Selection(
                            column,
                            column,
                            initial_state=(
                                column in self._selected_columns
                                or column in self._locked_columns
                            ),
                            disabled=column in self._locked_columns,
                        )
                        for column in self._columns
                    ],
                    id="select-columns-list",
                )
            else:
                yield Static("No columns available.", id="select-columns-empty")
            with Vertical(id="select-columns-actions"):
                with Horizontal(classes="select-columns-action-row"):
                    yield Button("Select All", id="select-columns-select-all")
                    yield Button(
                        "Clear selected",
                        id="select-columns-clear-selected",
                    )
                with Horizontal(classes="select-columns-action-row"):
                    yield Button("Apply", id="select-columns-apply", disabled=True)
                    yield Button("Cancel", id="select-columns-cancel")

    def _selection_list(self) -> SelectionList[str] | None:
        matches = list(self.query(SelectionList))
        if not matches:
            return None
        return matches[0]

    def _enforce_locked_columns(self) -> None:
        selection_list = self._selection_list()
        if selection_list is None:
            return
        for column in self._locked_columns:
            selection_list.select(column)

    def _ordered_selected_columns(self) -> tuple[str, ...]:
        selection_list = self._selection_list()
        if selection_list is None:
            return ()
        selected = set(selection_list.selected)
        return tuple(column for column in self._columns if column in selected)

    def _sync_apply_button(self) -> None:
        button = self.query_one("#select-columns-apply", Button)
        button.disabled = not self._ordered_selected_columns()

    def on_mount(self) -> None:
        self._enforce_locked_columns()
        self._sync_apply_button()

    def on_selection_list_selected_changed(
        self,
        _event: SelectionList.SelectedChanged[str],
    ) -> None:
        self._enforce_locked_columns()
        self._sync_apply_button()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        selection_list = self._selection_list()

        if button_id == "select-columns-select-all":
            if selection_list is not None:
                selection_list.select_all()
            self._enforce_locked_columns()
            self._sync_apply_button()
            return

        if button_id == "select-columns-clear-selected":
            if selection_list is not None:
                selection_list.deselect_all()
            self._enforce_locked_columns()
            self._sync_apply_button()
            return

        if button_id == "select-columns-apply":
            self.dismiss(self._ordered_selected_columns())
            return

        if button_id == "select-columns-cancel":
            self.dismiss(None)
