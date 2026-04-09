from typing import Any

from .project_config import load_project_config


def _apply_plot_palette(config: dict[str, Any]) -> None:
    global _CONFIG, PLOT_COLOR_PALETTE
    _CONFIG = config
    PLOT_COLOR_PALETTE = tuple(_CONFIG["plot"]["palette"])


_CONFIG: dict[str, Any]
PLOT_COLOR_PALETTE: tuple[str, ...]

_apply_plot_palette(load_project_config())


def refresh_plot_palette(
    config: dict[str, Any] | None = None,
) -> tuple[str, ...]:
    refreshed = config if config is not None else load_project_config()
    _apply_plot_palette(refreshed)
    return PLOT_COLOR_PALETTE


def resolve_plot_colors(series_count: int) -> list[str]:
    if series_count < 1:
        return []
    max_series = len(PLOT_COLOR_PALETTE)
    if series_count > max_series:
        raise ValueError(
            f"At most {max_series} input files are supported for plotting."
        )
    return list(PLOT_COLOR_PALETTE[:series_count])
