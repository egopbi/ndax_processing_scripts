@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Виртуальное окружение не найдено. Сначала запустите setup_windows.cmd.
    exit /b 1
)

".venv\Scripts\python.exe" "scripts\convert_ndax.py" %*
exit /b %errorlevel%
