from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Static

AdvancedMode = Literal["plot", "table"]
AdvancedAction = Literal["save", "health-check"]


@dataclass(frozen=True)
class AdvancedOptionsState:
    mode: AdvancedMode
    labels: str = ""
    output_override: str = ""


@dataclass(frozen=True)
class AdvancedOptionsResult:
    action: AdvancedAction
    state: AdvancedOptionsState


class AdvancedOptionsScreen(ModalScreen[AdvancedOptionsResult | None]):
    AUTO_FOCUS = ""

    BINDINGS = [
        ("escape", "dismiss(None)", "Cancel"),
    ]

    CSS = """
    AdvancedOptionsScreen {
        align: center middle;
    }

    #advanced-options-dialog {
        width: 80%;
        background: #20242b;
        border: ascii #6db7ff;
        padding: 1 2;
    }

    #advanced-options-actions {
        height: auto;
        margin-top: 1;
    }
    """

    def __init__(
        self,
        *,
        mode: AdvancedMode,
        labels: str = "",
        output_override: str = "",
    ) -> None:
        super().__init__()
        self._mode = mode
        self._labels = labels
        self._output_override = output_override

    @property
    def _title(self) -> str:
        if self._mode == "table":
            return "Comparison Table Options"
        return "Plot Options"

    def compose(self):
        with Vertical(id="advanced-options-dialog"):
            yield Label(self._title, id="advanced-options-title")
            yield Static(
                "Adjust labels or run a health check without changing the main layout.",
                id="advanced-options-description",
            )
            yield Input(
                value=self._labels,
                placeholder="Labels, comma separated",
                id="advanced-labels",
            )
            with Horizontal(id="advanced-options-actions"):
                yield Button("Save", id="advanced-save")
                yield Button("Run Health Check", id="advanced-health-check")
                yield Static("", classes="spacer")
                yield Button("Cancel", id="advanced-cancel")

    def _build_result(self, action: AdvancedAction) -> AdvancedOptionsResult:
        return AdvancedOptionsResult(
            action=action,
            state=AdvancedOptionsState(
                mode=self._mode,
                labels=self.query_one("#advanced-labels", Input).value,
                output_override=self._output_override,
            ),
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id == "advanced-save":
            self.dismiss(self._build_result("save"))
            return

        if button_id == "advanced-health-check":
            self.dismiss(self._build_result("health-check"))
            return

        if button_id == "advanced-cancel":
            self.dismiss(None)
