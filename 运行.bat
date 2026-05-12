@echo off
setlocal EnableExtensions
cd /d "%~dp0"

if not exist "%~dp0.venv\Scripts\python.exe" (
    echo Local virtual environment was not found.
    echo Run the install batch file first.
    echo.
    pause
    exit /b 1
)

if exist "%~dp0.venv\Scripts\pythonw.exe" (
    start "" "%~dp0.venv\Scripts\pythonw.exe" "%~dp0ico_maker_gui.pyw"
) else (
    start "" "%~dp0.venv\Scripts\python.exe" "%~dp0ico_maker_gui.pyw"
)