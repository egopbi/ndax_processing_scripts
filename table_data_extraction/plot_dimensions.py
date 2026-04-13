from __future__ import annotations

DEFAULT_PLOT_OUTPUT_WIDTH_PX = 1500
DEFAULT_PLOT_OUTPUT_HEIGHT_PX = 900
MIN_PLOT_OUTPUT_DIMENSION_PX = 300
MAX_PLOT_OUTPUT_DIMENSION_PX = 6000


def validate_plot_output_dimension(
    value_px: int,
    *,
    dimension_name: str,
) -> int:
    if not (
        MIN_PLOT_OUTPUT_DIMENSION_PX
        <= value_px
        <= MAX_PLOT_OUTPUT_DIMENSION_PX
    ):
        raise ValueError(
            f"{dimension_name} must be between "
            f"{MIN_PLOT_OUTPUT_DIMENSION_PX} and {MAX_PLOT_OUTPUT_DIMENSION_PX} "
            f"pixels."
        )
    return value_px


def resolve_plot_output_dimensions(
    *,
    output_width_px: int | None = None,
    output_height_px: int | None = None,
) -> tuple[int, int]:
    resolved_width_px = (
        DEFAULT_PLOT_OUTPUT_WIDTH_PX
        if output_width_px is None
        else int(output_width_px)
    )
    resolved_height_px = (
        DEFAULT_PLOT_OUTPUT_HEIGHT_PX
        if output_height_px is None
        else int(output_height_px)
    )
    validate_plot_output_dimension(
        resolved_width_px, dimension_name="Output width"
    )
    validate_plot_output_dimension(
        resolved_height_px, dimension_name="Output height"
    )
    return resolved_width_px, resolved_height_px
