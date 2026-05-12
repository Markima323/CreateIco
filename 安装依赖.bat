@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "PYTHON_CMD="

where py >nul 2>nul
if not errorlevel 1 set "PYTHON_CMD=py -3"

if not defined PYTHON_CMD (
    where python >nul 2>nul
    if not errorlevel 1 set "PYTHON_CMD=python"
)

if not defined PYTHON_CMD (
    echo Python 3 was not found.
    echo Install Python 3 and run this file again.
    echo.
    pause
    exit /b 1
)

echo [1/3] Creating virtual environment...
call %PYTHON_CMD% -m venv --clear .venv
if errorlevel 1 goto :fail

echo [2/3] Upgrading pip...
call ".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto :fail

echo [3/3] Installing requirements...
call ".venv\Scripts\python.exe" -m pip install --no-cache-dir --force-reinstall -r requirements.txt
if errorlevel 1 goto :fail

echo.
echo Install complete.
echo Run the launcher batch file to start the app.
echo.
pause
exit /b 0

:fail
echo.
echo Install failed. Check the error output above.
echo.
pause
exit /b 1
