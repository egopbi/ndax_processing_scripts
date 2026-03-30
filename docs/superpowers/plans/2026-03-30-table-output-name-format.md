# Table Output Name Format Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Change the auto-generated comparison table filename so it no longer includes `anchor-x` and instead uses a short normalized quantity name plus a dashed timestamp.

**Architecture:** Update the table output-path builder to derive a short quantity slug from the resolved Y column, reuse the dashed timestamp style already used for plots, and keep custom `--output` behavior unchanged. Adjust focused tests and README text that mention the old table filename format.

**Tech Stack:** Python 3.12, pathlib, pytest, existing CLI scripts and docs.

---

## File Structure

- Modify: `table_data_extraction/output_paths.py`
- Modify: `tests/test_output_paths.py`
- Modify if needed: `README.md`
- Verify: `tests/test_table_cli.py`

## Phase 1: Update Auto-Generated Table Filename

### Task 1: Rename default table outputs to `table_<quantity>_YYYY-MM-DD_HH-MM-SS.csv`

**Files:**
- Modify: `table_data_extraction/output_paths.py`
- Modify: `tests/test_output_paths.py`
- Modify if needed: `README.md`
- Verify: `tests/test_table_cli.py`

- [ ] **Step 1: Write or update the failing tests**

Update tests so they assert all of the following:

```python
def test_default_table_output_path_uses_new_filename_template() -> None:
    timestamp = datetime(2026, 3, 29, 16, 7, 22)

    output_path = default_table_output_path(
        resolved_y_column="Voltage",
        anchor_x="0.5",
        timestamp=timestamp,
    )

    assert output_path.name == "table_voltage_2026-03-29_16-07-22.csv"


def test_default_table_output_path_strips_units_from_quantity_name() -> None:
    timestamp = datetime(2026, 3, 29, 16, 7, 22)

    output_path = default_table_output_path(
        resolved_y_column="Current(mA)",
        anchor_x="0.5",
        timestamp=timestamp,
    )

    assert output_path.name == "table_current_2026-03-29_16-07-22.csv"
```

Also keep one test for a snake_case quantity like `Charge_Capacity(mAh)` so the expected filename becomes:

```python
"table_charge_capacity_2026-03-29_16-07-22.csv"
```

- [ ] **Step 2: Run focused tests to verify they fail**

Run:
- `uv run pytest -q tests/test_output_paths.py`

Expected:
- FAIL because the current code still includes `_at_<anchor>` and uses the compact timestamp format.

- [ ] **Step 3: Implement the minimal code change**

Update `table_data_extraction/output_paths.py` so:

```python
def default_table_output_path(...):
    ...
    filename = f"table_{normalized_quantity}_{dashed_timestamp}.csv"
```

Implement a small helper that converts the resolved Y column to a short quantity slug:

```python
Voltage -> voltage
Current(mA) -> current
Charge_Capacity(mAh) -> charge_capacity
Discharge_Capacity(mAh) -> discharge_capacity
```

For any other column, fall back to a safe normalized base name without units.

- [ ] **Step 4: Update user-facing docs only where they mention the old filename**

If `README.md` still mentions `table_<quantity>_at_<anchor>_...`, update that example to the new format.

- [ ] **Step 5: Run focused regressions**

Run:
- `uv run pytest -q tests/test_output_paths.py tests/test_table_cli.py`

Expected: PASS.
