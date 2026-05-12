@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "PYTHON_CMD="
set "VENV_PY=%~dp0.venv\Scripts\python.exe"
set "APP_NAME=ICO_Maker"

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

if not exist "%VENV_PY%" (
    echo [1/5] Creating virtual environment...
    call %PYTHON_CMD% -m venv .venv
    if errorlevel 1 goto :fail
) else (
    echo [1/5] Virtual environment already exists.
)

echo [2/5] Upgrading pip...
call "%VENV_PY%" -m pip install --upgrade pip
if errorlevel 1 goto :fail

echo [3/5] Installing app requirements...
call "%VENV_PY%" -m pip install --no-cache-dir --force-reinstall -r requirements.txt
if errorlevel 1 goto :fail

echo [4/5] Installing build tools...
call "%VENV_PY%" -m pip install --no-cache-dir --upgrade pyinstaller
if errorlevel 1 goto :fail

echo [5/5] Building exe...
"%VENV_PY%" "%~dp0build_exe.py"
if errorlevel 1 goto :fail

echo.
echo Build complete.
echo Exe file:
echo %~dp0dist\%APP_NAME%.exe
echo Output folders created by the exe will be placed next to the exe file.
echo.
pause
exit /b 0

:fail
echo.
echo Build failed. Check the messages above.
echo.
pause
exit /b 1