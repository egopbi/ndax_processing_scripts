# README Python3 And Prod Requirements Design

**Date:** 2026-03-30

## Goal

Обновить пользовательскую документацию и packaging-конфигурацию так, чтобы:

- в `README.md` использовались команды, которые реально работают на соответствующей ОС, без `uv`;
- для macOS и Windows была добавлена простая инструкция по установке Python 3.13;
- `requirements.txt` содержал только production-зависимости;
- dev-зависимости не попадали в production-установку.

## Scope

В scope входят только:

- `README.md`
- `requirements.txt`
- `pyproject.toml` при необходимости, если потребуется уточнить группировку зависимостей

Не входит в scope:

- изменение Python-кода
- изменение CLI-контрактов
- перестройка lockfile без причины

## Intended Behavior

### README

- macOS-команды должны использовать `python3`
- Windows-команды должны использовать рабочий для Windows launcher, то есть `py`
- команды установки зависимостей должны использовать `python3 -m pip install -r requirements.txt` для macOS и `py -m pip install -r requirements.txt` для Windows
- README должен объяснять, как установить Python 3.13 на обе системы простыми шагами

### Dependencies

- `pyproject.toml` должен содержать runtime-зависимости в `[project].dependencies`
- dev-зависимости должны жить в dev-секции, а не в production-списке
- `requirements.txt` должен быть production-only и не включать `pytest` и его dev-related зависимости

## Verification

Изменение считается корректным, если:

- в `README.md` больше нет пользовательских команд с `uv run`
- install-команды соответствуют новой стратегии запуска
- `requirements.txt` не содержит `pytest`, `pluggy`, `iniconfig`, `pygments`
- `pyproject.toml` не содержит dev-зависимости в production-секции
