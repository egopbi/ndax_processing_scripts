# Project Overview

## Purpose

This repository provides NDAX file tooling for three supported workflows:

- plotting one or more files through the Windows launcher `plot_ndax.cmd` and the Python entrypoint `scripts/plot_ndax.py`
- building a comparison table through `build_comparison_table.cmd` and `scripts/build_comparison_table.py`
- converting one or more NDAX files to CSV slices through `convert_ndax.cmd` and `scripts/convert_ndax.py`

The public runtime policy is `Python >= 3.12`. The repository pin in `.python-version` stays on `3.12` for local tooling.

## Current Layout

- `scripts/plot_ndax.py`: CLI wrapper for plot generation
- `scripts/build_comparison_table.py`: CLI wrapper for comparison-table generation
- `scripts/convert_ndax.py`: CLI wrapper for NDAX-to-CSV conversion by selected columns
- `scripts/health_check_ndax.py`: focused CLI for dataset validation
- `table_data_extraction/`: shared domain logic for loading, preprocessing, plotting, extrema detection, export, and config access
- `project_config.yaml`: repository-level defaults for output paths, plotting defaults, CSV defaults, and comparison-table tuning

Convert mode behavior contract:

- one CSV output per input `.ndax` file
- automatic inclusion of the `Time` column in every converted CSV
- no filename override in the TUI `convert` mode; output location is controlled by `--output-dir` / runtime output directory

Plot mode behavior contract:

- output image size is controlled by `--output-width-px` and `--output-height-px`
- the default size is `1500x900` px
- both size parameters accept only `300..6000` px
- the same size controls are available in TUI `Plot` -> `More Options`
- `--separate` switches plot output from one combined JPG to one JPG per input `.ndax`
- separate plot outputs are named from the source file stem, matching the convert-mode naming model
- `--separate` is mutually exclusive with `--output` / filename override
- batch preprocessing and `Rest` trimming are computed once and reused consistently for every separate plot output

## Configuration Contract

`project_config.yaml` is the source file checked into the repo. Runtime code reads it through `table_data_extraction.project_config`, which validates the required schema and exposes `load_project_config()`.

When changing config structure, update both the YAML file and `table_data_extraction.project_config` schema checks in the same change.

## Documentation Policy

The durable technical docs in this repo are:

- `docs/project_overview.md`
- `docs/architecture.md`
- `docs/development_notes.md`

Do not reintroduce historical plans, specs, or idea documents as permanent repository docs.
