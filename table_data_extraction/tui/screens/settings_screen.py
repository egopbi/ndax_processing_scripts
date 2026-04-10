from __future__ import annotations

from pathlib import Path
import threading

from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Input, Label, Static

from table_data_extraction.project_config import load_project_config
from table_data_extraction.tui.dialogs import choose_output_directory
from table_data_extraction.tui.settings_service import (
    build_updated_config,
    resolve_runtime_output_dir,
    save_updated_config,
)
from table_data_extraction.tui.widgets.palette_preview import PalettePreview


def _format_compact_path(value: Path | None, *, limit: int = 42) -> str:
    if value is None:
        return ""

    text = str(value)
    if len(text) <= limit:
        return text

    if limit <= 3:
        return "..."[:limit]

    return f"...{text[-(limit - 3):]}"


class SettingsScreen(Screen[dict[str, object] | None]):
    BINDINGS = [
        ("escape", "dismiss(None)", "Back"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._current_config = load_project_config()
        self._selected_output_dir = resolve_runtime_output_dir(
            self._current_config
        )

    def compose(self):
        palette = self._current_config["plot"]["palette"]
        csv_columns = ", ".join(self._current_config["csv"]["defaults"]["columns"])
        extrema = self._current_config["comparison_table"]["extrema_detection"]

        with Vertical(id="settings-top-bar"):
            with Horizontal(id="settings-top-row"):
                yield Label("Settings", id="settings-title")
                yield Static("", classes="spacer")
                with Horizontal(id="settings-top-actions"):
                    yield Button(
                        "Select Default Output Directory...",
                        id="settings-select-output-dir",
                    )
                    yield Button("Back", id="settings-back")
            yield Static(
                f"Default output directory: {_format_compact_path(self._selected_output_dir)}",
                id="settings-output-dir",
            )
        with VerticalScroll(id="settings-scroll"):
            with Vertical(id="settings-form"):
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
                yield Label("Palette", id="settings-palette-label")
                with Horizontal(id="settings-palette-section"):
                    with Vertical(id="settings-palette-inputs"):
                        for index, color in enumerate(palette):
                            yield Input(
                                value=str(color),
                                placeholder=f"Palette color {index + 1}",
                                id=f"settings-palette-{index}",
                            )
                    with Vertical(id="settings-preview-panel"):
                        yield Label("Palette preview", id="settings-preview-title")
                        yield PalettePreview(
                            palette, id="settings-palette-preview"
                        )
                with Horizontal(id="settings-actions"):
                    yield Button("Save", variant="success", id="settings-save")
                    yield Button("Cancel", variant="default", id="settings-cancel")
                yield Static("", id="settings-status")

    def _palette_values(self) -> list[str]:
        values: list[str] = []
        index = 0
        while True:
            widget_id = f"#settings-palette-{index}"
            try:
                values.append(self.query_one(widget_id, Input).value)
            except Exception:
                break
            index += 1
        return values

    def _refresh_preview(self) -> None:
        preview = self.query_one("#settings-palette-preview", PalettePreview)
        preview.set_colors(self._palette_values())

    def _show_status(self, message: str) -> None:
        self.query_one("#settings-status", Static).update(message)

    def _refresh_output_label(self) -> None:
        self.query_one("#settings-output-dir", Static).update(
            "Default output directory: "
            f"{_format_compact_path(self._selected_output_dir)}"
        )

    def _choose_output_directory_in_thread(self) -> None:
        selected = choose_output_directory(initial_dir=self._selected_output_dir)
        if selected is not None:
            self.app.call_from_thread(self._apply_selected_output_dir, selected)

    def _apply_selected_output_dir(self, selected: Path) -> None:
        self._selected_output_dir = selected
        self._refresh_output_label()

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
        if event.input.id and event.input.id.startswith("settings-palette-"):
            self._refresh_preview()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "settings-select-output-dir":
            thread = threading.Thread(
                target=self._choose_output_directory_in_thread,
                daemon=True,
            )
            thread.start()
            return

        if event.button.id == "settings-save":
            self._save()
            return

        if event.button.id == "settings-back":
            self.dismiss(None)
            return

        if event.button.id == "settings-cancel":
            self.dismiss(None)
