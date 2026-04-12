from __future__ import annotations

from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Input, Label, Static

from table_data_extraction.project_config import load_project_config
from table_data_extraction.tui.settings_service import (
    build_updated_config,
    resolve_runtime_output_dir,
    save_updated_config,
)
from table_data_extraction.tui.widgets.palette_preview import PalettePreview


class SettingsScreen(Screen[dict[str, object] | None]):
    BINDINGS = [
        ("escape", "dismiss(None)", "Back"),
        ("f6", "exit_app", "Exit"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._current_config = load_project_config()
        self._selected_output_dir = resolve_runtime_output_dir(
            self._current_config
        )

    def compose(self):
        palette = self._current_config["plot"]["palette"]
        palette_text = " ".join(palette)
        csv_columns = ", ".join(self._current_config["csv"]["defaults"]["columns"])
        extrema = self._current_config["comparison_table"]["extrema_detection"]

        with Vertical(id="settings-shell"):
            with Horizontal(id="settings-top-bar", classes="surface-box"):
                with Vertical(id="settings-brand"):
                    yield Label("NDAX Processor", id="settings-title")
                    yield Label("by eeee_gorka", id="settings-subtitle")
                yield Static("", classes="spacer")
                with Horizontal(id="settings-top-actions", classes="top-actions"):
                    yield Button(
                        "Main Menu",
                        id="settings-main-menu",
                        classes="top-action-button",
                    )
                    yield Button(
                        "Exit",
                        id="settings-exit-app",
                        classes="top-action-button",
                    )
            with Vertical(id="settings-body"):
                with VerticalScroll(id="settings-scroll"):
                    with Vertical(id="settings-defaults-section", classes="section-shell"):
                        yield Label("Defaults", classes="section-title")
                        yield Input(
                            value=self._current_config["plot"]["defaults"]["x_column"],
                            placeholder="Plot X column",
                            id="settings-plot-x",
                        )
                        yield Input(
                            value=self._current_config["plot"]["defaults"]["y_column"],
                            placeholder="Plot Y column",
                            id="settings-plot-y",
                        )
                        yield Input(
                            value=csv_columns,
                            placeholder="CSV columns, comma separated",
                            id="settings-csv-columns",
                        )
                        yield Input(
                            value=str(extrema["window_points"]),
                            placeholder="Window points",
                            id="settings-window-points",
                        )
                        yield Input(
                            value=str(extrema["zero_threshold"]),
                            placeholder="Zero threshold",
                            id="settings-zero-threshold",
                        )
                        yield Input(
                            value=str(extrema["min_zone_points"]),
                            placeholder="Minimum zone points",
                            id="settings-min-zone-points",
                        )
                        yield Input(
                            value=str(extrema["min_extrema_separation_points"]),
                            placeholder="Minimum extrema separation points",
                            id="settings-min-extrema-separation-points",
                        )
                    with Vertical(id="settings-palette-section", classes="section-shell"):
                        yield Label("Palette", id="settings-palette-label", classes="section-title")
                        with Horizontal(id="settings-palette-row"):
                            yield Input(
                                value=palette_text,
                                placeholder="Hex colors separated by spaces",
                                id="settings-palette",
                            )
                            with Vertical(id="settings-preview-panel"):
                                yield Label("Palette preview", id="settings-preview-title")
                                yield PalettePreview(
                                    palette, id="settings-palette-preview"
                                )
            with Horizontal(id="settings-actions"):
                yield Static("", classes="spacer")
                yield Button("Save", variant="success", id="settings-save")
                yield Button("Back", variant="default", id="settings-back")
            yield Static("", id="settings-status")

    def _palette_values(self) -> list[str]:
        value = self.query_one("#settings-palette", Input).value
        return [item for item in value.replace(",", " ").split() if item]

    def _refresh_preview(self) -> None:
        preview = self.query_one("#settings-palette-preview", PalettePreview)
        preview.set_colors(self._palette_values())

    def _show_status(self, message: str) -> None:
        self.query_one("#settings-status", Static).update(message)

    def _save(self) -> None:
        try:
            config = build_updated_config(
                current_config=self._current_config,
                output_dir=self._selected_output_dir,
                palette=self._palette_values(),
                plot_x_column=self.query_one("#settings-plot-x", Input).value,
                plot_y_column=self.query_one("#settings-plot-y", Input).value,
                csv_columns=self.query_one("#settings-csv-columns", Input).value,
                window_points=self.query_one("#settings-window-points", Input).value,
                zero_threshold=self.query_one("#settings-zero-threshold", Input).value,
                min_zone_points=self.query_one("#settings-min-zone-points", Input).value,
                min_extrema_separation_points=self.query_one(
                    "#settings-min-extrema-separation-points",
                    Input,
                ).value,
            )
            saved = save_updated_config(config)
        except Exception as error:
            self._show_status(f"Save failed: {error}")
            return

        self.dismiss(saved)

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "settings-palette":
            self._refresh_preview()

    def action_exit_app(self) -> None:
        self.app.action_exit_app()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "settings-main-menu":
            self.dismiss(None)
            return

        if event.button.id == "settings-exit-app":
            self.app.action_exit_app()
            return

        if event.button.id == "settings-save":
            self._save()
            return

        if event.button.id == "settings-back":
            self.dismiss(None)
