# Architecture

This repository's technical baseline is `Python >= 3.12`.

## Entrypoints

User-facing execution on Windows goes through `plot_ndax.cmd` and `build_comparison_table.cmd`. Those launch the Python CLIs in `scripts/plot_ndax.py` and `scripts/build_comparison_table.py`.

The health-check workflow is separate and runs from `scripts/health_check_ndax.py`.

## Data Flow

`scripts/plot_ndax.py`:

1. parses CLI arguments
2. loads each NDAX file with `table_data_extraction.reader`
3. resolves columns and plot labels
4. prepares plot-ready data through `table_data_extraction.plotting`
5. writes the final image through the export helpers

`scripts/build_comparison_table.py`:

1. parses CLI arguments
2. loads each NDAX file
3. resolves columns and trims leading rest rows
4. derives X/Y series, short-circuit timing, and extrema windows
5. writes the CSV table

## Module Boundaries

- `table_data_extraction.reader`: NDAX loading
- `table_data_extraction.preprocess`: time-axis preparation and row trimming
- `table_data_extraction.plotting`: plot column resolution, axis labels, and figure export
- `table_data_extraction.extrema`: extrema search
- `table_data_extraction.short_circuit`: short-circuit detection and rounding
- `table_data_extraction.export`: table serialization
- `table_data_extraction.output_paths`: generated output naming
- `table_data_extraction.project_config`: validated access to `project_config.yaml`

## Invariants

- Supported public commands stay `.\setup_windows.cmd`, `.\plot_ndax.cmd`, and `.\build_comparison_table.cmd`.
- Configuration defaults come from `project_config.yaml`; code should not silently fork duplicate defaults.
- CLI behavior changes require explicit tests, not documentation-only edits.
