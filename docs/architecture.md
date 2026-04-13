# Architecture

This repository's technical baseline is `Python >= 3.12`.

## Entrypoints

User-facing execution on Windows goes through `plot_ndax.cmd`, `build_comparison_table.cmd`, and `convert_ndax.cmd`. Those launch the Python CLIs in `scripts/plot_ndax.py`, `scripts/build_comparison_table.py`, and `scripts/convert_ndax.py`.

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

`scripts/convert_ndax.py`:

1. parses CLI arguments
2. validates input NDAX file list and selected columns
3. resolves output path for each source file (`<input-stem>.csv`) in the target output directory
4. ensures output paths are unique within the current batch
5. loads each NDAX file and exports a CSV slice with the selected columns (always including `Time`)

## Module Boundaries

- `table_data_extraction.reader`: NDAX loading
- `table_data_extraction.preprocess`: time-axis preparation and row trimming
- `table_data_extraction.plotting`: plot column resolution, axis labels, and figure export
- `table_data_extraction.extrema`: extrema search
- `table_data_extraction.short_circuit`: short-circuit detection and rounding
- `table_data_extraction.export`: table serialization
- `table_data_extraction.output_paths`: generated output naming
- `table_data_extraction.project_config`: validated access to `project_config.yaml`
- `table_data_extraction.convert`: convert-mode column resolution, batch validation, and CSV slice export orchestration

## Invariants

- Supported public commands stay `.\setup_windows.cmd`, `.\plot_ndax.cmd`, `.\build_comparison_table.cmd`, and `.\convert_ndax.cmd`.
- Configuration defaults come from `project_config.yaml`; code should not silently fork duplicate defaults.
- CLI behavior changes require explicit tests, not documentation-only edits.
- TUI `convert` mode uses selected columns and output directory only; filename override is intentionally not part of this mode.
