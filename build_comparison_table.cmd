@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Виртуальное окружение не найдено. Сначала запустите setup_windows.cmd.
    exit /b 1
)

".venv\Scripts\python.exe" "scripts\build_comparison_table.py" %*
exit /b %errorlevel%
