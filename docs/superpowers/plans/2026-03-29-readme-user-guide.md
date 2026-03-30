# README User Guide Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rewrite `README.md` into a clear end-user guide that explains setup, commands, flags, examples, table logic, short-circuit logic, and YAML settings without overwhelming new users.

**Architecture:** Keep all changes inside `README.md`. Structure the document so the top of the file is beginner-friendly and action-oriented, while deeper sections cover command reference, algorithm explanations, and YAML configuration. All statements must match the current scripts and config exactly.

**Tech Stack:** Markdown, current Python CLI scripts (`argparse`), current `project_config.yaml`.

---

## File Structure

- Modify: `README.md`
- Read for accuracy: `scripts/plot_ndax.py`
- Read for accuracy: `scripts/build_comparison_table.py`
- Read for accuracy: `scripts/health_check_ndax.py`
- Read for accuracy: `scripts/generate_plot_poc.py`
- Read for accuracy: `scripts/generate_csv_poc.py`
- Read for accuracy: `table_data_extraction/extrema.py`
- Read for accuracy: `table_data_extraction/short_circuit.py`
- Read for accuracy: `project_config.yaml`

## Phase 1: Rewrite README

### Task 1: Replace the current README with a user-focused guide

**Files:**
- Modify: `README.md`
- Read for accuracy: `scripts/plot_ndax.py`
- Read for accuracy: `scripts/build_comparison_table.py`
- Read for accuracy: `scripts/health_check_ndax.py`
- Read for accuracy: `scripts/generate_plot_poc.py`
- Read for accuracy: `scripts/generate_csv_poc.py`
- Read for accuracy: `table_data_extraction/extrema.py`
- Read for accuracy: `table_data_extraction/short_circuit.py`
- Read for accuracy: `project_config.yaml`

- [ ] **Step 1: Read the live command surfaces and config**

Verify the current behavior from:

```text
scripts/plot_ndax.py
scripts/build_comparison_table.py
scripts/health_check_ndax.py
scripts/generate_plot_poc.py
scripts/generate_csv_poc.py
table_data_extraction/extrema.py
table_data_extraction/short_circuit.py
project_config.yaml
```

Capture the real flag names, which ones are required, default values, units, and the current YAML fields.

- [ ] **Step 2: Replace README structure**

Rewrite `README.md` so it has this section order:

```markdown
# <clear Russian title>

## Что делает этот проект
## Подготовка к запуску
## Основные команды
## Быстрые примеры
## Подробно: построение графика
## Подробно: построение таблицы
## Подробно: проверка файла
## Вспомогательные команды
## Как рассчитываются 6 точек таблицы
## Как определяется точка короткого замыкания
## Настройка project_config.yaml
## Частые вопросы и ошибки
```

The opening sections must stay short and practical. Detailed logic goes only in the lower half of the file.

- [ ] **Step 3: Document each command accurately**

For `plot_ndax.py`, `build_comparison_table.py`, and `health_check_ndax.py`, describe:

```markdown
- purpose of the command
- exact launch command on macOS
- exact launch command on Windows
- required arguments
- optional arguments
- which values are accepted by each flag
- what units those values use
- where output is saved by default
```

Also include several concrete examples for each major command, including:

```markdown
- one-file plot
- multi-file plot
- plot with --x-min/--x-max/--y-min/--y-max
- table for one file
- table for multiple files
- examples with --labels
- examples with --output
```

- [ ] **Step 4: Explain table and short-circuit logic in user language**

Describe the algorithms without code jargon:

```markdown
- anchor-x picks the reference position on the X axis
- the script searches nearest anchor position
- to the left of anchor it searches max -> min -> max
- to the right of anchor it searches min -> max -> min
- these become +U_l, +U_m, +U_r, -U_l, -U_m, -U_r
- short circuit is detected either by a threshold event or by waveform amplitude collapse
- the reported short-circuit value is rounded to the nearest 5 hours using half-up rounding
```

- [ ] **Step 5: Explain YAML settings**

Describe every current setting in `project_config.yaml`:

```markdown
paths.output_dir
plot.palette
plot.defaults.x_column
plot.defaults.y_column
plot.defaults.x_limits
plot.defaults.y_limits
csv.defaults.columns
```

For each setting, explain:

```markdown
- what it changes
- what kind of value it expects
- when a normal user might want to edit it
- when it is better not to change it
```

- [ ] **Step 6: Verify the README against live CLI help and current config**

Run:

- `uv run python scripts/plot_ndax.py --help`
- `uv run python scripts/build_comparison_table.py --help`
- `uv run python scripts/health_check_ndax.py --help`

Check that the README matches:

- flag names
- required vs optional status
- default values
- output behavior

- [ ] **Step 7: Perform a final readability pass**

Confirm all of the following:

- the first screen of README is not overloaded
- Russian wording is suitable for a non-technical user
- there are no references to removed config fields
- examples use realistic `.ndax` paths and values
- the document reads as a guide, not as internal developer notes
