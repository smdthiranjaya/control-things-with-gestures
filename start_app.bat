@echo off
echo Starting Gesture Control Dashboard...

cd /d "%~dp0"

REM Activate virtual environment
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
)

REM Auto-restart on exit code 42
:start
echo Starting Flask application...
python app.py
if %errorlevel% equ 42 (
    echo Backend restart requested...
    timeout /t 2 /nobreak >nul
    goto start
)

if %errorlevel% neq 0 (
    echo Application stopped with error code %errorlevel%
    pause
)
