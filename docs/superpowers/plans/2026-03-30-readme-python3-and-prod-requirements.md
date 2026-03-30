# README Python3 And Prod Requirements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Switch user-facing documentation to OS-appropriate non-`uv` commands and make `requirements.txt` production-only.

**Architecture:** Keep code untouched. Update `README.md` to use `python3` on macOS and `py` on Windows, add Python 3.13 installation guidance, and trim `requirements.txt` to runtime dependencies only. Change `pyproject.toml` only if verification shows a dev dependency is still misplaced.

**Tech Stack:** Markdown, TOML, pip requirements, current CLI scripts.

---

## File Structure

- Modify: `README.md`
- Modify: `requirements.txt`
- Modify only if needed: `pyproject.toml`
- Read for accuracy: `scripts/plot_ndax.py`
- Read for accuracy: `scripts/build_comparison_table.py`
- Read for accuracy: `scripts/health_check_ndax.py`

## Phase 1: Documentation And Packaging Cleanup

### Task 1: Replace `uv` user commands and make requirements production-only

**Files:**
- Modify: `README.md`
- Modify: `requirements.txt`
- Modify only if needed: `pyproject.toml`

- [ ] **Step 1: Verify current command surface and dependency placement**

Inspect:

```text
README.md
requirements.txt
pyproject.toml
scripts/plot_ndax.py
scripts/build_comparison_table.py
scripts/health_check_ndax.py
```

Confirm which commands are shown to users, which dependency groups exist, and which packages in `requirements.txt` are clearly dev-only.

- [ ] **Step 2: Rewrite README commands**

Update `README.md` so:

```text
macOS examples use `python3 ...`
Windows examples use `py ...`
installation uses `python3 -m pip install -r requirements.txt` on macOS
installation uses `py -m pip install -r requirements.txt` on Windows
```

Also add a short beginner-friendly subsection for each OS explaining how to install Python 3.13.

- [ ] **Step 3: Clean production requirements**

Remove clearly dev-only packages from `requirements.txt`, including:

```text
pytest
pluggy
iniconfig
pygments
```

Keep runtime requirements needed by the shipped CLI tools.

- [ ] **Step 4: Update `pyproject.toml` only if needed**

If inspection shows any dev dependency still sits in `[project].dependencies`, move it into the dev section. If `pyproject.toml` is already correct, leave it unchanged.

- [ ] **Step 5: Verify**

Run:

- `rg -n "uv run|uv sync" README.md`
- `rg -n "pytest|pluggy|iniconfig|pygments" requirements.txt`
- `sed -n '1,220p' pyproject.toml`

Expected:

- no user-facing `uv` commands remain in README
- no dev-only pytest packages remain in `requirements.txt`
- `pyproject.toml` keeps production and dev dependencies separated
