# NDAX Table Data Extraction

This repository provides two supported CLI tools for laboratory staff:

- `scripts/plot_ndax.py` for plots
- `scripts/build_comparison_table.py` for comparison tables

`scripts/health_check_ndax.py` is a diagnostic helper for checking whether an NDAX file has the columns needed by the public tools.

Legacy PoC scripts are not the normal user interface.

The public CLI contract uses `Time` in hours and `Voltage` in mV.

## Installation

Windows:

```bash
py -m pip install -r requirements.txt
```

macOS:

```bash
uv sync
```

## Plot NDAX data

Use `scripts/plot_ndax.py` to build one plot from one or more NDAX files.

Windows:

```bash
py scripts\plot_ndax.py --files example.ndax --y-column Voltage
```

macOS:

```bash
uv run python scripts/plot_ndax.py --files example.ndax --y-column Voltage
```

The plot is saved to `output/` by default. Use `--output` if you want a custom path. When `Time` is the x-axis, values are shown in hours and `Voltage` is shown in mV.

### Example: plot with 2 `ndax`

Windows:

```bash
py scripts\plot_ndax.py --files sample_a.ndax sample_b.ndax --labels Sample_A Sample_B --y-column Voltage
```

macOS:

```bash
uv run python scripts/plot_ndax.py --files sample_a.ndax sample_b.ndax --labels Sample_A Sample_B --y-column Voltage
```

### Example: plot with non-`Time` x-column

Windows:

```bash
py scripts\plot_ndax.py --files example.ndax --x-column "current(ma)" --y-column Voltage
```

macOS:

```bash
uv run python scripts/plot_ndax.py --files example.ndax --x-column "current(ma)" --y-column Voltage
```

### Example: plot with axis ranges

Windows:

```bash
py scripts\plot_ndax.py --files example.ndax --y-column Voltage --x-min 0 --x-max 1.5 --y-min 3000 --y-max 4300
```

macOS:

```bash
uv run python scripts/plot_ndax.py --files example.ndax --y-column Voltage --x-min 0 --x-max 1.5 --y-min 3000 --y-max 4300
```

## Build a comparison table

Use `scripts/build_comparison_table.py` to generate the comparison CSV for one anchor position on the `Time` axis.

Windows:

```bash
py scripts\build_comparison_table.py --files example.ndax --anchor-x 0.5 --y-column Voltage
```

macOS:

```bash
uv run python scripts/build_comparison_table.py --files example.ndax --anchor-x 0.5 --y-column Voltage
```

The table is saved to `output/` by default. Use `--output` if you want a custom path. The output table reports `Voltage` values in mV.

### Example: table with one `anchor-x`

Windows:

```bash
py scripts\build_comparison_table.py --files sample_a.ndax sample_b.ndax --anchor-x 0.5 --labels Sample_A Sample_B --y-column Voltage
```

macOS:

```bash
uv run python scripts/build_comparison_table.py --files sample_a.ndax sample_b.ndax --anchor-x 0.5 --labels Sample_A Sample_B --y-column Voltage
```

## Health check

Use `scripts/health_check_ndax.py` when a file may have missing or invalid columns. The command prints a report and returns a non-zero exit code if problems are detected.

Windows:

```bash
py scripts\health_check_ndax.py
```

macOS:

```bash
uv run python scripts/health_check_ndax.py
```

### Example: health check when file has problems

Windows:

```bash
py scripts\health_check_ndax.py
```

macOS:

```bash
uv run python scripts/health_check_ndax.py
```

## Tests

Windows:

```bash
py -m pytest
```

macOS:

```bash
uv run pytest
```
