# NDAX Table Data Extraction

PoC-проект для чтения `example.ndax`, проверки доступных колонок, построения demo-графика и выгрузки demo-CSV.

## Стек

- Python 3.12
- NewareNDA
- pandas
- matplotlib

## Структура проекта

- `scripts/` — исполняемые PoC-скрипты
- `table_data_extraction/` — общая логика чтения, проверки, графика и CSV
- `tests/` — автотесты `pytest`
- `docs/` — план и заметки по совместимости
- `output/` — сгенерированные артефакты PoC

## Установка зависимостей

Windows:

```bash
py -m pip install -r requirements.txt
```

macOS:

```bash
uv sync
```

## Проверка файла NDAX

Windows:

```bash
py scripts\health_check_ndax.py
```

macOS:

```bash
uv run python scripts/health_check_ndax.py
```

Скрипт печатает число строк, список колонок и статус demo-колонок для графика и CSV.

## Построение demo-графика

Windows:

```bash
py scripts\generate_plot_poc.py
```

macOS:

```bash
uv run python scripts/generate_plot_poc.py
```

Результат сохраняется в `output/poc_plot.jpg`.

## Выгрузка demo-CSV

Windows:

```bash
py scripts\generate_csv_poc.py
```

macOS:

```bash
uv run python scripts/generate_csv_poc.py
```

Результат сохраняется в `output/poc_table.csv`.

## Тесты

Windows:

```bash
py -m pytest
```

macOS:

```bash
uv run pytest
```
