# Customer Corrections Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Update the public plot and comparison-table CLIs to match the latest customer corrections: fixed 8-color palette, simpler plot grid, startup-tail removal on plots, and a new `Короткое замыкание` column in the comparison CSV.

**Architecture:** Keep the existing CLI surface unchanged. Implement the plotting changes inside the current plot pipeline, and implement short-circuit detection as a separate helper module used only by `scripts/build_comparison_table.py`. Do not change unrelated public contracts or add new CLI flags.

**Tech Stack:** Python, pandas, matplotlib, pytest, existing `table_data_extraction` package modules.

---

## Summary

- The first implementation phase must be color-palette work.
- Plot output must use a fixed 8-color order on white background, with no fallback to matplotlib defaults.
- Plot startup artifact must be removed by dropping the first non-`Rest` working point from the plot-only pipeline.
- Plot grid must revert to major-grid-only behavior: lines only at labeled ticks, no minor ticks, no minor grid.
- The comparison CSV must gain one new trailing column named `Короткое замыкание`.
- `Короткое замыкание` is determined by the earliest qualifying event in time:
  - threshold event: first local extremum at or beyond `+200 mV` or `-200 mV`
  - amplitude-collapse event: first 5-hour bin that satisfies the collapse criteria defined below
- If the formal algorithm disagrees with example values previously mentioned in discussion, the algorithm is the source of truth.
- `Короткое замыкание` is written as a bare integer hour value rounded to the nearest multiple of 5 using half-up behavior.

## Locked Decisions

- Fixed palette order:
  - `#1718FE`
  - `#D35400`
  - `#128A0C`
  - `#7A44F6`
  - `#C0392B`
  - `#008AA6`
  - `#1B1F28`
  - `#A61E4D`
- If more than 8 files are passed to `plot_ndax.py`, fail with a clear `ValueError`; do not cycle colors.
- No new CLI flags.
- Keep the existing public units:
  - `Time` is public hours
  - `Voltage` is public `mV`
- The startup-tail removal applies to:
  - plot generation
  - short-circuit detection
- The startup-tail removal does **not** apply to the existing six-extrema search used for `+U_l ... -U_r`.
- The new `Короткое замыкание` column is the last column in the CSV.
- The second header row keeps the new column empty, matching the current two-header-row table style.

## Current Repo Context

- Plot CLI entrypoint: `scripts/plot_ndax.py`
- Comparison-table CLI entrypoint: `scripts/build_comparison_table.py`
- Plot behavior is currently implemented in `table_data_extraction/plotting.py`
- CSV export is currently implemented in `table_data_extraction/export.py`
- Six-extrema search is implemented in `table_data_extraction/extrema.py`
- Shared preprocessing helpers are in `table_data_extraction/preprocess.py`
- Existing comparison-table row schema is defined in `table_data_extraction/table_builder.py`
- Existing plot tests:
  - `tests/test_plotting.py`
  - `tests/test_plotting_cli.py`
- Existing comparison-table tests:
  - `tests/test_table_builder.py`
  - `tests/test_table_cli.py`

## Public Interface Changes

- `scripts/plot_ndax.py`
  - no new arguments
  - plot color assignment becomes deterministic and fixed by file order
  - passing more than 8 input files becomes an explicit error
- `scripts/build_comparison_table.py`
  - no new arguments
  - output CSV gains one new trailing column: `Короткое замыкание`
- Comparison CSV shape changes from:
  - `name`, six extrema columns
- To:
  - `name`, six extrema columns, `Короткое замыкание`

## Phase 1: Fixed Plot Palette

### Files

- Create: `table_data_extraction/plot_style.py`
- Modify: `table_data_extraction/plotting.py`
- Test: `tests/test_plotting_cli.py`

### Implementation

- Add `PLOT_COLOR_PALETTE` in `table_data_extraction/plot_style.py` as the exact 8-color tuple listed in the locked decisions section.
- Add helper `resolve_plot_colors(series_count: int) -> list[str]` in `table_data_extraction/plot_style.py`.
- Helper rules:
  - if `series_count < 1`, return empty list
  - if `series_count > 8`, raise `ValueError("At most 8 input files are supported for plotting.")`
  - otherwise return the first `series_count` colors from the fixed palette in order
- In `table_data_extraction/plotting.py`, assign one explicit color per plotted series in `save_multi_series_plot(...)`.
- The color index must match the series index after `lines` are assembled in `scripts/plot_ndax.py`.
- Do not use matplotlib default cycle anywhere after this change.

### Tests

- Add a test that `resolve_plot_colors(1)`, `resolve_plot_colors(2)`, `resolve_plot_colors(3)`, and `resolve_plot_colors(8)` return the exact expected prefixes/order.
- Add a CLI-path test that verifies the first two plotted series receive the first two colors in order.
- Add a CLI-path or plotting-level test that `series_count > 8` raises the exact plotting error.

## Phase 2: Plot Cleanup

### Files

- Modify: `table_data_extraction/plotting.py`
- Test: `tests/test_plotting.py`
- Test: `tests/test_plotting_cli.py`

### Implementation

- In `prepare_plot_frame(...)`, after `trim_leading_rest_rows(dataframe)`, drop the first remaining working row if the trimmed frame is non-empty.
- This drop is plot-only behavior. Do not move it into `trim_leading_rest_rows(...)`, because the six-extrema pipeline must keep its current behavior.
- After this drop:
  - keep the existing `Time -> hours` conversion behavior
  - keep the existing `Voltage -> mV` conversion behavior
- Remove minor tick and minor grid logic from `save_multi_series_plot(...)`:
  - delete `AutoMinorLocator`
  - delete `NullFormatter`
  - delete `which="minor"` grid call
  - keep a single major-grid call only
- Keep major grid enabled on both axes.
- Grid lines must correspond only to displayed major ticks.

### Tests

- Replace the current test assertions that expect minor ticks and minor grid.
- Add a test for `prepare_plot_frame(...)` on a synthetic frame with `Rest` + three working points, asserting that the first surviving working point is excluded from the plot frame.
- Add a plotting-level test asserting:
  - major grid exists
  - minor tick locations are absent or empty
  - no minor gridlines are visible
- Update CLI tests so the expected plotted series for the current sample DataFrame start from the second working point, not the first one.

## Phase 3: Short-Circuit Detection Module

### Files

- Create: `table_data_extraction/short_circuit.py`
- Test: `tests/test_short_circuit.py`

### Public Helper Contract

- Create `detect_short_circuit_time_hours(dataframe: pd.DataFrame) -> float | None`
- Input expectation:
  - raw NDAX dataframe
- Output expectation:
  - public time in hours before rounding, or `None` if no short circuit is detected
- Create `round_short_circuit_hours(value: float | None) -> int | None`
- Rounding rule:
  - nearest multiple of 5
  - half-up, not banker’s rounding
  - examples:
    - `183 -> 185`
    - `182 -> 180`
    - `182.5 -> 185`

### Preprocessing for Detection

- Start from `trim_leading_rest_rows(dataframe)`.
- If the trimmed frame is non-empty, drop the first remaining working row. This must mirror the plot cleanup rule.
- Build public time in hours:
  - if `Timestamp` is usable for `Time`, use `prepare_x_series(trimmed, "Time") / 3600`
  - otherwise use `trimmed["Time"] / 3600`
- Build public voltage in `mV`:
  - `trimmed["Voltage"] * 1000`
- Reset index before local-extrema logic so positional indexing is stable.

### Detector A: Threshold Event

- Detect on local extrema only, not on arbitrary points.
- Reuse the same local-max/local-min semantics already used in `table_data_extraction/extrema.py`:
  - local maximum: `current >= left and current >= right and (current > left or current > right)`
  - local minimum: `current <= left and current <= right and (current < left or current < right)`
- The threshold candidate time is the earliest public-time extremum where either:
  - local maximum `>= 200`
  - local minimum `<= -200`
- Use the extremum time directly as the candidate event time.

### Detector B: Amplitude-Collapse Event

- Bin the public time series into 5-hour bins:
  - `bin_start = floor(hours / 5) * 5`
- For each 5-hour bin, compute:
  - `min_y`
  - `max_y`
  - `amp = max_y - min_y`
- A collapse candidate exists for bin `B` only if all bins `B-15`, `B-10`, `B-5`, `B`, `B+5`, and `B+10` exist.
- Compute `baseline = median(amp[B-15], amp[B-10], amp[B-5])`.
- Bin `B` is the first collapse candidate if:
  - `amp[B+5] < 0.8 * baseline`
  - `amp[B+10] < 0.5 * baseline`
  - for every later existing bin `L >= B+10`, `amp[L] <= 0.6 * baseline`
- The collapse candidate time is `B`, meaning the time directly before the stable amplitude-collapse regime starts.

### Final Selection

- Compute both candidate times independently.
- If both are present, choose the smaller time.
- If only one is present, use that one.
- If neither is present, return `None`.

### Tests

- Add synthetic threshold-only series test.
- Add synthetic collapse-only series test.
- Add synthetic series where both detectors fire and assert earliest-time wins.
- Add test for `None` when neither detector fires.
- Add dedicated tests for `round_short_circuit_hours(...)`.

## Phase 4: Comparison Table Integration

### Files

- Modify: `table_data_extraction/table_builder.py`
- Modify: `table_data_extraction/export.py`
- Modify: `scripts/build_comparison_table.py`
- Test: `tests/test_table_builder.py`
- Test: `tests/test_table_cli.py`

### Implementation

- In `table_data_extraction/table_builder.py`:
  - extend `COMPARISON_TABLE_COLUMNS` to include trailing `Короткое замыкание`
  - keep `EXTREMA_COLUMNS` unchanged
  - update `build_comparison_row(...)` to accept a new keyword-only argument `short_circuit_hours: int | None`
  - write `""` when `short_circuit_hours is None`, otherwise write the integer value
- In `table_data_extraction/export.py`:
  - keep existing extrema header formatting logic
  - update `save_comparison_table(...)` so the first header row includes `Короткое замыкание` as the final column name
  - update the second header row so the final column is empty
  - keep the existing numeric formatting behavior for numeric cells
  - do not append units to the new short-circuit column value
- In `scripts/build_comparison_table.py`:
  - import `detect_short_circuit_time_hours` and `round_short_circuit_hours`
  - for each file:
    - compute the existing extrema row as before
    - compute `short_circuit_raw = detect_short_circuit_time_hours(dataframe)`
    - compute `short_circuit_rounded = round_short_circuit_hours(short_circuit_raw)`
    - pass `short_circuit_rounded` into `build_comparison_row(...)`
  - do not reuse the x-anchor or six-extrema x/y series for short-circuit detection; detection must use the raw dataframe and its own preprocessing path from `short_circuit.py`

### Tests

- Add table-builder test asserting the new column exists and is placed last.
- Add export test asserting the two header rows become:
  - first row: `name;{anchor};...;Короткое замыкание`
  - second row: `;{extrema labels};`
- Add CLI test asserting that when the detector returns a value, the resulting row includes that value in the new trailing column.
- Add CLI test asserting empty cell when detector returns `None`.
- Keep the existing `Voltage -> mV` extrema-header test green.

## Phase 5: Real-Data Smoke Verification

### Files

- No new code files in this phase.
- This is verification only after implementation is complete.

### Required Commands

- `uv run pytest -q`
- `uv run python scripts/plot_ndax.py --files examples/example_1.ndax --y-column voltage`
- `uv run python scripts/plot_ndax.py --files examples/example_1.ndax examples/example_2.ndax examples/example_3.ndax --y-column voltage`
- `uv run python scripts/build_comparison_table.py --files examples/example_1.ndax examples/example_2.ndax examples/example_3.ndax --y-column voltage --anchor-x 50`

### Required Manual Checks

- Open the generated plot for `examples/example_1.ndax` and confirm:
  - there is no startup downward tail at the far left edge
  - only major gridlines are visible
- Open the generated multi-file plot and confirm:
  - series colors are the first three palette colors in the exact locked order
  - the three lines are visually separable on white background
- Open the generated comparison CSV and confirm:
  - the final column header is `Короткое замыкание`
  - the last column is filled only with plain integer-like hour values or left empty

## Acceptance Criteria

- `uv run pytest -q` passes.
- Plot CLI no longer renders the startup tail.
- Plot CLI uses only major gridlines.
- Plot CLI uses the fixed 8-color palette in the exact locked order.
- Plot CLI rejects `>8` files with a clear error.
- Comparison CSV contains a trailing `Короткое замыкание` column.
- Short-circuit detection is based on the formal earliest-event algorithm above.
- Short-circuit values are rounded to multiples of 5 with half-up behavior and written without a unit suffix.

## Explicit Assumptions

- The formal algorithm is the source of truth, even if it disagrees with example numbers previously mentioned in chat.
- `Короткое замыкание` uses public units:
  - event detection runs on hours and `mV`
  - stored output is integer hours
- The first phase is palette work; implementation order must not be rearranged.
- README updates are optional follow-up and are not required for acceptance of this task unless the implementing agent chooses to add them after all tests pass.
