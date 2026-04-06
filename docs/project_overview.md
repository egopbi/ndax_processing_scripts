# Project Overview

## Purpose

This repository provides NDAX file tooling for two supported workflows:

- plotting one or more files through the Windows launcher `plot_ndax.cmd` and the Python entrypoint `scripts/plot_ndax.py`
- building a comparison table through `build_comparison_table.cmd` and `scripts/build_comparison_table.py`

The public runtime policy is `Python >= 3.12`. The repository pin in `.python-version` stays on `3.12` for local tooling.

## Current Layout

- `scripts/plot_ndax.py`: CLI wrapper for plot generation
- `scripts/build_comparison_table.py`: CLI wrapper for comparison-table generation
- `scripts/health_check_ndax.py`: focused CLI for dataset validation
- `table_data_extraction/`: shared domain logic for loading, preprocessing, plotting, extrema detection, export, and config access
- `project_config.yaml`: repository-level defaults for output paths, plotting defaults, CSV defaults, and comparison-table tuning

## Configuration Contract

`project_config.yaml` is the source file checked into the repo. Runtime code reads it through `table_data_extraction.project_config`, which validates the required schema and exposes `load_project_config()`.

When changing config structure, update both the YAML file and `table_data_extraction.project_config` schema checks in the same change.

## Documentation Policy

The durable technical docs in this repo are:

- `docs/project_overview.md`
- `docs/architecture.md`
- `docs/development_notes.md`

Do not reintroduce historical plans, specs, or idea documents as permanent repository docs.
