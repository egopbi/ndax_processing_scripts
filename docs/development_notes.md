# Development Notes

## Python And Tooling Policy

- Public docs and package metadata must state `Python >= 3.12`.
- `.python-version` remains `3.12`.
- Keep the public README Windows-first. Do not add macOS setup blocks back into `README.md`.

## Config Notes

`project_config.yaml` is the checked-in config contract. `table_data_extraction.project_config` owns schema validation, caching, and safe loading for the rest of the codebase.

If a change adds or renames config keys, update:

- `project_config.yaml`
- `table_data_extraction.project_config`
- affected tests

## Repo Hygiene

- Do not revive legacy files such as `main.py`, `Project_idea.md`, or public PoC scripts.
- The canonical durable docs are `docs/project_overview.md`, `docs/architecture.md`, and `docs/development_notes.md`.
- Historical plans and specs should not be reintroduced into git as durable repo docs.
- Local temporary planning files are not canonical docs.
- Keep the canonical technical docs compact and durable enough for future coding agents to recover the current entrypoints and config model quickly.

## Focused Verification

For documentation and repo-shape changes, run at minimum:

- `uv run pytest tests/test_documentation_policy.py -q`
- `uv run pytest tests/test_windows_launchers.py -q`
