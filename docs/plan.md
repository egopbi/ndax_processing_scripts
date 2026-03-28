# План PoC с `uv` только для разработки и `requirements.txt` для Windows

## Summary

- PoC реализуется на `Python 3.12` с `NewareNDA`, `pandas`, `matplotlib`.
- Исполняемых скриптов будет 3:
  - `scripts/health_check_ndax.py`
  - `scripts/generate_plot_poc.py`
  - `scripts/generate_csv_poc.py`
- Самое первое действие после одобрения плана: сохранить этот план в `docs/plan.md`.
- `uv` используется только на этапе разработки на macOS. Для Windows runtime и для README целевым контрактом считается `requirements.txt`, а не `uv`, `pyproject.toml` или `uv.lock`.

## Implementation Changes

- Локально на macOS поднять dev-окружение через `uv` и ставить зависимости командами `uv add ...`; считать изменения в `pyproject.toml` и `uv.lock` чисто dev-артефактами.
  - macOS: `uv add NewareNDA pandas matplotlib pytest`
  - Windows: не использовать `uv`; позже ставить зависимости только из `requirements.txt`
- Вынести общую логику в пакет `table_data_extraction`:
  - `reader`: чтение `NDAX` в `DataFrame`
  - `health`: диагностика файла и проверка колонок
  - `config`: hardcoded PoC-настройки
  - `plotting`: генерация `jpg`
  - `export`: генерация CSV-среза
- Оставить `main.py` вне acceptance-path; входные точки PoC только в `scripts/`.
- Порядок реализации:
  1. Сохранить план в `docs/plan.md`.
  2. На macOS установить dev-зависимости через `uv`.
  3. Реализовать `reader` и `scripts/health_check_ndax.py`.
  4. Прогнать health check на `example.ndax`, зафиксировать точные имена demo-колонок в `config.py`.
  5. Реализовать `scripts/generate_plot_poc.py`.
  6. Реализовать `scripts/generate_csv_poc.py`.
  7. Прогнать тесты в dev-окружении.
  8. В конце экспортировать runtime-зависимости в `requirements.txt` и уже от него писать Windows-инструкции.

## Public Interfaces

- Health check:
  - Windows: `py scripts\health_check_ndax.py`
  - macOS dev: `uv run python scripts/health_check_ndax.py`
  - Поведение: проверка наличия файла, чтение через `NewareNDA`, проверка на непустой `DataFrame`, вывод числа строк и полного списка колонок, отдельный статус по demo-колонкам.
- Demo-график:
  - Windows: `py scripts\generate_plot_poc.py`
  - macOS dev: `uv run python scripts/generate_plot_poc.py`
  - Поведение: hardcoded `example.ndax`, график `время -> напряжение`, выход `output/poc_plot.jpg`, подписи осей `<величина> (<единица>)`, легенда по имени файла.
- Demo-CSV:
  - Windows: `py scripts\generate_csv_poc.py`
  - macOS dev: `uv run python scripts/generate_csv_poc.py`
  - Поведение: экспорт всех строк по demo-колонкам `время, напряжение, ток, емкость`, пропуск только реально отсутствующих колонок, выход `output/poc_table.csv`, параметры `sep=';'`, `encoding='utf-8-sig'`, `index=False`.
- Установка зависимостей для конечного Windows-окружения после экспорта `requirements.txt`:
  - Windows: `py -m pip install -r requirements.txt`
  - macOS: `python3 -m pip install -r requirements.txt`

## Test Plan

- Автотест: `load_ndax_dataframe()` возвращает непустой `DataFrame`.
- Автотест: health check проходит на `example.ndax` и возвращает непустой список колонок.
- Автотест: health check корректно сообщает об отсутствии обязательной demo-колонки.
- Автотест: генерация графика создает непустой `jpg`.
- Автотест: генерация CSV создает файл с ожидаемыми колонками, `;` и BOM.
- Автотест: пути через `Path` работают в директории с пробелами.
- Команды проверки:
  - Windows: `py -m pytest`
  - macOS dev: `uv run pytest`
- Финальный экспорт зависимостей:
  - Windows: использовать уже готовый `requirements.txt`
  - macOS dev: `uv export --format requirements-txt -o requirements.txt`

## Assumptions

- `uv` нужен только разработчику на macOS; конечные пользователи Windows с ним не работают.
- `pyproject.toml` и `uv.lock` допустимы как dev-артефакты, но не являются частью runtime-процесса и не должны фигурировать в пользовательских Windows-инструкциях.
- Для поставки на Windows итоговым артефактом зависимостей считается `requirements.txt`.
- PoC не повторяет структуру `example_table.csv`; это прямой срез исходного `DataFrame`.
- PoC остается hardcoded: без CLI-аргументов, без сравнения нескольких файлов и без пользовательских диапазонов.
