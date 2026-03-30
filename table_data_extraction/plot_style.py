from .project_config import load_project_config

_CONFIG = load_project_config()

PLOT_COLOR_PALETTE: tuple[str, ...] = tuple(_CONFIG["plot"]["palette"])


def resolve_plot_colors(series_count: int) -> list[str]:
    if series_count < 1:
        return []
    max_series = len(PLOT_COLOR_PALETTE)
    if series_count > max_series:
        raise ValueError(
            f"At most {max_series} input files are supported for plotting."
        )
    return list(PLOT_COLOR_PALETTE[:series_count])
