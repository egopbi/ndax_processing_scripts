@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if errorlevel 1 (
    echo Команда py не найдена. Установите Python for Windows и включите Add python.exe to PATH.
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo Создаю виртуальное окружение .venv...
    py -m venv .venv
    if errorlevel 1 (
        echo Не удалось создать виртуальное окружение .venv.
        exit /b 1
    )
)

echo Обновляю pip...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 (
    echo Не удалось обновить pip.
    exit /b 1
)

echo Устанавливаю зависимости проекта...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    echo Не удалось установить зависимости из requirements.txt.
    exit /b 1
)

echo.
echo Установка завершена.
echo Для построения графика используйте:
echo .\plot_ndax.cmd --files examples\example1_1.ndax --y-column Voltage
echo.
echo Для построения сравнительной таблицы используйте:
echo .\build_comparison_table.cmd --files examples\example1_1.ndax --y-column Voltage --anchor-x 0.5

exit /b 0
