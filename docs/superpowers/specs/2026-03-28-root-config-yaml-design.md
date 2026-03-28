# Root Config YAML Design

## Goal

Move project defaults into one root-level YAML file so colors and other defaults can be edited in a single structured place.

The YAML file becomes the single source of truth. Python modules stop owning these values directly and instead read them from the YAML.

## Scope

In scope:

- Add one root config file in YAML format.
- Move the fixed plot palette into YAML as a list of hex colors.
- Move current default settings into YAML in a structured form.
- Add one loader module that reads and normalizes the YAML.
- Keep current import surfaces usable where practical by making existing config modules thin adapters over the loaded YAML.
- Add tests proving runtime values come from YAML.

Out of scope:

- New CLI flags.
- Changing business behavior beyond config sourcing.
- Large refactors of scripts or package layout.

## Proposed File Layout

Root file:

- `project_config.yaml`

Package support:

- `table_data_extraction/project_config.py`

Existing modules kept as adapters:

- `table_data_extraction/config.py`
- `table_data_extraction/plot_style.py`

## YAML Structure

```yaml
paths:
  source_file: example_1.ndax
  output_dir: output

plot:
  palette:
    - "#1718FE"
    - "#D35400"
    - "#128A0C"
    - "#7A44F6"
    - "#C0392B"
    - "#008AA6"
    - "#1B1F28"
    - "#A61E4D"
  defaults:
    x_column: Time
    y_column: Voltage
    x_limits: null
    y_limits: null

csv:
  defaults:
    columns:
      - Time
      - Voltage
      - Current(mA)
      - Charge_Capacity(mAh)
      - Discharge_Capacity(mAh)

labels:
  axis_overrides:
    Time: Time (s)
    Voltage: Voltage (V)
    Current(mA): Current (mA)
    Charge_Capacity(mAh): Charge Capacity (mAh)
    Discharge_Capacity(mAh): Discharge Capacity (mAh)
    Charge_Energy(mWh): Charge Energy (mWh)
    Discharge_Energy(mWh): Discharge Energy (mWh)
```

## Loader Design

`table_data_extraction/project_config.py` will:

- resolve the repository root from the package location
- read `project_config.yaml`
- validate the expected top-level sections
- expose a loaded config object or normalized dictionary
- convert path-like settings into `Path` objects where needed

This loader should be small and explicit. It does not need a heavy schema library.

## Compatibility Strategy

Current callers already import values from `table_data_extraction.config` and palette logic from `table_data_extraction.plot_style`.

To avoid wide churn:

- `config.py` will load from the YAML-backed loader and re-export:
  - `ROOT_DIR`
  - `SOURCE_FILE`
  - `OUTPUT_DIR`
  - `PLOT_OUTPUT`
  - `CSV_OUTPUT`
  - `PLOT_X_COLUMN`
  - `PLOT_Y_COLUMN`
  - `CSV_COLUMNS`
  - `X_LIMITS`
  - `Y_LIMITS`
  - `AXIS_LABEL_OVERRIDES`
- `plot_style.py` will source `PLOT_COLOR_PALETTE` from the YAML-backed loader and keep `resolve_plot_colors(...)` unchanged at the public level

This keeps the change centered on config sourcing rather than broad API changes.

## Defaults and Derived Values

Some current values are derived rather than directly configured:

- `ROOT_DIR` remains derived from code location
- `PLOT_OUTPUT` remains derived from `OUTPUT_DIR / "poc_plot.jpg"`
- `CSV_OUTPUT` remains derived from `OUTPUT_DIR / "poc_table.csv"`

These derived values stay in Python because they are implementation details built from YAML defaults.

## Error Handling

On invalid or missing YAML:

- fail fast during import with a clear `ValueError` or `KeyError`
- do not silently fall back to hardcoded defaults

This preserves the single-source-of-truth requirement.

## Testing Strategy

Add focused tests for:

- YAML loader reads expected palette and defaults
- `config.py` exports expected values sourced from YAML
- `plot_style.py` palette comes from YAML and `resolve_plot_colors(...)` still enforces the current limits

Keep existing tests green to prove the rest of the app still works with YAML-backed config.

## Risks

- Config loading at import time can make failures earlier and louder. This is acceptable because hidden fallback behavior would violate the goal.
- Tests that import config modules may need controlled reloading if they patch config files.
- If YAML dependency is not already declared, it must be available in the project environment.

## Acceptance Criteria

- The root of the repository contains a single YAML config file with palette and structured defaults.
- The palette is no longer hardcoded in Python as the source of truth.
- Existing default settings listed in current `config.py` are sourced from YAML, directly or as documented derived values.
- Existing public behavior remains unchanged.
- Tests confirm runtime values are loaded from YAML.
