from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Static

from table_data_extraction.plot_dimensions import (
    DEFAULT_PLOT_OUTPUT_HEIGHT_PX,
    DEFAULT_PLOT_OUTPUT_WIDTH_PX,
)

AdvancedMode = Literal["plot", "table"]
AdvancedAction = Literal["save", "health-check"]


@dataclass(frozen=True)
class AdvancedOptionsState:
    mode: AdvancedMode
    labels: str = ""
    output_override: str = ""
    output_width_px: str = str(DEFAULT_PLOT_OUTPUT_WIDTH_PX)
    output_height_px: str = str(DEFAULT_PLOT_OUTPUT_HEIGHT_PX)


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
        height: 85%;
        max-height: 24;
        min-height: 12;
        background: #20242b;
        border: ascii #6db7ff;
        padding: 1 2;
    }

    #advanced-options-body {
        height: 1fr;
        min-height: 0;
    }

    #advanced-options-scroll {
        height: 1fr;
        min-height: 0;
        padding-right: 1;
        scrollbar-background: #0f1216;
        scrollbar-background-hover: #0f1216;
        scrollbar-background-active: #0f1216;
        scrollbar-color: #6db7ff;
        scrollbar-color-hover: #8cc8ff;
        scrollbar-color-active: #6db7ff;
        scrollbar-gutter: stable;
    }

    #advanced-output-size-section {
        height: 9;
    }

    #advanced-labels-section {
        height: 5;
    }

    #advanced-options-actions {
        width: 1fr;
        height: auto;
        margin-top: 1;
        background: #20242b;
    }
    """

    def __init__(
        self,
        *,
        mode: AdvancedMode,
        labels: str = "",
        output_override: str = "",
        output_width_px: str = str(DEFAULT_PLOT_OUTPUT_WIDTH_PX),
        output_height_px: str = str(DEFAULT_PLOT_OUTPUT_HEIGHT_PX),
    ) -> None:
        super().__init__()
        self._mode = mode
        self._labels = labels
        self._output_override = output_override
        self._output_width_px = output_width_px
        self._output_height_px = output_height_px

    @property
    def _title(self) -> str:
        if self._mode == "table":
            return "Comparison Table Options"
        return "Plot Options"

    def compose(self):
        with Vertical(id="advanced-options-dialog"):
            with Vertical(id="advanced-options-body"):
                with VerticalScroll(id="advanced-options-scroll"):
                    yield Label(self._title, id="advanced-options-title")
                    yield Static(
                        "Adjust labels or run a health check without changing the main layout.",
                        id="advanced-options-description",
                    )
                    if self._mode == "plot":
                        with Vertical(
                            id="advanced-output-size-section",
                            classes="section-shell",
                        ):
                            yield Label("Image size", classes="section-title")
                            yield Label("Width (px)", id="advanced-label-output-width")
                            yield Input(
                                value=self._output_width_px,
                                id="advanced-output-width",
                            )
                            yield Label("Height (px)", id="advanced-label-output-height")
                            yield Input(
                                value=self._output_height_px,
                                id="advanced-output-height",
                            )
                    with Vertical(id="advanced-labels-section", classes="section-shell"):
                        yield Label("Labels", classes="section-title")
                        yield Label(
                            "Labels, comma separated",
                            id="advanced-labels-label",
                        )
                        yield Input(value=self._labels, id="advanced-labels")
            with Horizontal(id="advanced-options-actions"):
                yield Button("Save", id="advanced-save")
                yield Button("Run Health Check", id="advanced-health-check")
                yield Button("Cancel", id="advanced-cancel")

    def _build_result(self, action: AdvancedAction) -> AdvancedOptionsResult:
        return AdvancedOptionsResult(
            action=action,
            state=AdvancedOptionsState(
                mode=self._mode,
                labels=self.query_one("#advanced-labels", Input).value,
                output_override=self._output_override,
                output_width_px=(
                    self.query_one("#advanced-output-width", Input).value
                    if self._mode == "plot"
                    else self._output_width_px
                ),
                output_height_px=(
                    self.query_one("#advanced-output-height", Input).value
                    if self._mode == "plot"
                    else self._output_height_px
                ),
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
