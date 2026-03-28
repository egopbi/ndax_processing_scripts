# Руководство для оркестратора по реализации MVP

## Summary

- Этот документ является source of truth для реализации MVP.
- Оркестратор сам код не пишет. Каждый этап делает отдельный worker-subagent. После каждого этапа отдельный judge-subagent проверяет результат. Только после `accepted` можно переходить к следующему этапу.
- Этапы выполнять строго последовательно. Параллельно этапы не запускать.
- Цель MVP: заменить PoC двумя пользовательскими CLI-скриптами для Windows 10:
  - `scripts/plot_ndax.py`
  - `scripts/build_comparison_table.py`
- `scripts/health_check_ndax.py` оставить как вспомогательный диагностический скрипт.

## Contract для оркестратора

- На каждый этап запускать ровно 1 worker-subagent.
- После завершения worker запускать ровно 1 judge-subagent.
- Judge не редактирует файлы. Judge только читает код, запускает проверки и выдает вердикт.
- Если judge вернул blocking findings, запускать remediation-worker только на файлы текущего этапа, затем повторно запускать judge.
- Максимум 3 judge-цикла на этап. Если после 3 циклов этап не принят, остановиться и выдать blocked report.
- Перед переходом к следующему этапу judge должен явно вернуть `accepted`.
- Каждый worker в конце этапа обязан вернуть:
  - `changed_files`
  - `commands_run`
  - `tests_run`
  - `known_risks`
  - `summary`
- Каждый judge в конце этапа обязан вернуть:
  - `status: accepted|rejected`
  - `findings`
  - `commands_run`
  - `artifacts_checked`

## Stage 1. Общие CLI-утилиты и нормализация входа

- Worker files: `table_data_extraction/columns.py`, `table_data_extraction/preprocess.py`, `table_data_extraction/output_paths.py`, `tests/test_columns.py`, `tests/test_preprocess.py`, `tests/test_output_paths.py`.
- Реализовать case-insensitive resolution для всех имен колонок, вводимых пользователем.
- Нормализация имени колонки: `strip().casefold()`.
- Если совпадений нет, бросать понятную ошибку с перечислением доступных колонок.
- Если после нормализации найдено больше одного совпадения, бросать ошибку неоднозначности.
- В `preprocess.py` реализовать:
  - `trim_leading_rest_rows(df)` — удаляет только стартовый непрерывный блок `Status == "Rest"`.
  - `prepare_x_series(df, resolved_x_column)` — если колонка `Time`, возвращает кумулятивное время по `Timestamp` от первой не-`Rest` точки; если колонка не `Time`, возвращает исходную колонку без преобразования.
- Зафиксировать правило: только `Time` преобразуется в cumulative time. Все остальные `x-column` используются как есть.
- В `output_paths.py` реализовать генерацию путей по умолчанию в `output/` внутри проекта.
- Шаблон имени графика: `plot_<resolved-x>_vs_<resolved-y>_<YYYYMMDD_HHMMSS>.jpg`.
- Шаблон имени таблицы: `table_<resolved-y>_at_<anchor-x>_<YYYYMMDD_HHMMSS>.csv`.
- Санация имени: lowercase, пробелы в `_`, все кроме `[a-z0-9._-]` заменять на `_`.
- Judge checks:
  - case-insensitive resolution работает для `voltage`, `Voltage`, ` VOLTAGE `.
  - `Time` становится монотонным cumulative series.
  - `Voltage`, `Current(mA)`, `Charge/Discharge Capacity` не преобразуются в cumulative.
  - пути по умолчанию формируются внутри `output/`.
  - все новые тесты проходят.

## Stage 2. Пользовательский скрипт графика

- Worker files: `table_data_extraction/plotting.py`, `scripts/plot_ndax.py`, `tests/test_plotting_cli.py`.
- Реализовать публичный CLI:
  - `--files` обязателен, принимает 1+ путей.
  - `--y-column` обязателен.
  - `--x-column` optional, default `Time`.
  - `--labels` optional.
  - `--x-min`, `--x-max`, `--y-min`, `--y-max` optional.
  - `--output` optional.
- Если `--labels` не передан, имя линии = имя файла без расширения.
- Если `--labels` передан, число labels должно строго совпадать с числом файлов, иначе ошибка.
- Если `--output` не передан, использовать автогенерацию пути в `output/`.
- Для каждого файла:
  - читать `ndax`
  - удалять стартовый `Rest`
  - резолвить `x-column` и `y-column` без учета регистра
  - если `x-column == Time`, строить cumulative time
  - подготовить серию для общего графика
- На одном графике рисовать все образцы.
- Подписи осей всегда в формате `<величина> (<единица>)`.
- Для cumulative time подпись X фиксированная: `Cumulative Time (s)`.
- Легенда всегда в правом верхнем углу.
- Judge checks:
  - smoke-run на реальном файле: `uv run python scripts/plot_ndax.py --files example.ndax example.ndax --labels sample_a sample_b --y-column voltage`
  - smoke-run без `--output` создает файл в `output/`
  - smoke-run с явным `--output` создает файл по указанному пути
  - smoke-run с `--x-column current(ma)` работает без учета регистра
  - диапазоны `--x-min/--x-max/--y-min/--y-max` реально влияют на график
  - тесты stage 1 + stage 2 проходят

## Stage 3. Ядро поиска 6 экстремумов

- Worker files: `table_data_extraction/extrema.py`, `tests/test_extrema.py`.
- Реализовать поиск 6 точек вокруг одной anchor-x.
- Вход алгоритма:
  - подготовленный `x_series`
  - подготовленный `y_series`
  - `anchor_x`
- Якорная точка определяется как ближайшая по X к `anchor_x`.
- Слева от anchor:
  - сначала искать локальный максимум: это `+U_r`
  - левее него искать локальный минимум: это `+U_m`
  - левее него искать локальный максимум: это `+U_l`
- Справа от anchor:
  - сначала искать локальный минимум: это `-U_l`
  - правее него искать локальный максимум: это `-U_m`
  - правее него искать локальный минимум: это `-U_r`
- Локальный максимум: `y[i] >= y[i-1]` и `y[i] >= y[i+1]`, хотя бы одно строгое.
- Локальный минимум: `y[i] <= y[i-1]` и `y[i] <= y[i+1]`, хотя бы одно строгое.
- На плато брать первую подходящую точку в направлении поиска.
- Если точка не найдена, возвращать `None`, а не падать.
- Judge checks:
  - синтетическая кривая дает строго ожидаемые `+U_l/+U_m/+U_r/-U_l/-U_m/-U_r`
  - сценарий с недостающими экстремумами возвращает `None`
  - поиск anchor идет по ближайшему X
  - тесты stage 1-3 проходят

## Stage 4. Формирование сравнительной таблицы

- Worker files: `table_data_extraction/export.py`, `table_data_extraction/table_builder.py`, `tests/test_table_builder.py`.
- Реализовать сбор одной строки таблицы на один образец.
- На входе строки:
  - label образца
  - подготовленные `x/y` ряды
  - `anchor_x`
  - найденные индексы экстремумов
- Формат одной строки:
  - `name`
  - `+U_l`
  - `+U_m`
  - `+U_r`
  - `-U_l`
  - `-U_m`
  - `-U_r`
- Значение в ячейке = значение `y-column` в найденной точке.
- Если точка не найдена, в ячейке пусто.
- CSV writer должен формировать multi-row header в стиле `example_table.csv`:
  - строка 1: `name;<anchor-x>;;;;;`
  - строка 2: `;+U_l;+U_m;+U_r;-U_l;-U_m;-U_r`
- CSV сохранять как `sep=';'`, `encoding='utf-8-sig'`.
- Judge checks:
  - CSV имеет 2 header rows
  - пустые экстремумы становятся пустыми ячейками
  - row labels корректны
  - writer не пишет индекс pandas
  - тесты stage 1-4 проходят

## Stage 5. Пользовательский скрипт таблицы

- Worker files: `scripts/build_comparison_table.py`, `tests/test_table_cli.py`.
- Реализовать публичный CLI:
  - `--files` обязателен
  - `--y-column` обязателен
  - `--anchor-x` обязателен
  - `--x-column` optional, default `Time`
  - `--labels` optional
  - `--output` optional
- MVP принимает ровно одну `anchor-x` за запуск.
- Если `--labels` не передан, label = имя файла без расширения.
- Если `--output` не передан, использовать автогенерацию пути в `output/`.
- Для каждого файла:
  - читать `ndax`
  - удалять стартовый `Rest`
  - case-insensitive resolve для `x-column` и `y-column`
  - подготовить `x_series`
  - найти 6 экстремумов вокруг `anchor-x`
  - собрать строку таблицы
- Если какой-то экстремум не найден, писать warning в stderr и оставлять пустую ячейку.
- Judge checks:
  - smoke-run на реальном `example.ndax` с dynamically chosen anchor: взять медиану cumulative time и передать ее в CLI
  - smoke-run без `--output` создает CSV в `output/`
  - smoke-run с `--y-column voltage` работает без учета регистра
  - smoke-run с `--x-column current(ma)` использует колонку как есть, без cumulative transform
  - тесты stage 1-5 проходят

## Stage 6. README и очистка публичного интерфейса

- Worker files: `README.md`, при необходимости удалить или депаблишить PoC-команды из README.
- README переписать как пользовательскую инструкцию для работников лаборатории.
- Обязательно оставить отдельные блоки команд для Windows и macOS.
- Обязательно включить примеры:
  - график по 2 `ndax`
  - график с `x-column` не `Time`
  - график с диапазонами осей
  - таблица по одной `anchor-x`
  - health check при проблеме с файлом
- В README не использовать `uv` как runtime-инструмент для Windows.
- Runtime install для Windows только через `requirements.txt`.
- Judge checks:
  - README покрывает оба пользовательских скрипта
  - README не продвигает PoC-скрипты как основной интерфейс
  - README содержит явные команды для Windows
  - README содержит хотя бы 4 конкретных примера запуска

## Final Verification

- Отдельный финальный judge после stage 6 должен выполнить:
  - `uv run pytest`
  - smoke-run графика без `--output`
  - smoke-run графика с `--output`
  - smoke-run таблицы без `--output`
  - smoke-run таблицы с `--output`
  - проверку, что артефакты появляются в `output/`
  - проверку, что `requirements.txt` по-прежнему содержит только runtime-зависимости
- Если финальный judge возвращает `accepted`, оркестратор завершает работу.
- Если финальный judge возвращает `rejected`, запускать remediation-worker только на файлы, упомянутые в findings, затем повторить final judge.

## Final Report Format

- В конце оркестратор обязан выдать Markdown-отчет с разделами:
  - `Implemented`
  - `Public Commands`
  - `Files Changed`
  - `Verification`
  - `Warnings`
- В `Implemented` перечислить завершенные stages.
- В `Public Commands` перечислить финальные Windows и macOS команды для двух MVP-скриптов.
- В `Verification` перечислить все реально выполненные тесты и smoke-checks.
- В `Warnings` перечислить все remaining limitations, если они есть.
- Если работа остановилась неуспешно, вместо этого выдать blocked report с разделами:
  - `Completed Stages`
  - `Failed Stage`
  - `Blocking Findings`
  - `Recommended Next Fix`

## Assumptions

- Оркестратор работает в текущем репозитории и использует subagents как workers/judges.
- Оркестратор не редактирует код сам.
- Этапы выполняются строго последовательно.
- Только `Time` преобразуется в cumulative time.
- По умолчанию все пользовательские результаты пишутся в `output/` проекта.
