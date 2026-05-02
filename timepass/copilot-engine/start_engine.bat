@echo off
REM ============================================
REM  Copilot Engine - Setup & Launch
REM ============================================

echo.
echo ========================================
echo   Copilot Engine Setup
echo ========================================
echo.

cd /d "%~dp0"

REM 1. Check Python
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python not found. Install Python 3.10+
    exit /b 1
)

REM 2. Create virtual environment if missing
if not exist ".venv" (
    echo [1/3] Creating virtual environment...
    python -m venv .venv
    echo       Done.
) else (
    echo [1/3] Virtual environment exists.
)

REM 3. Install dependencies
echo [2/3] Installing dependencies...
call .venv\Scripts\pip install -r requirements.txt --quiet
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: pip install failed
    exit /b 1
)
echo       Done.

REM 4. Start engine
echo [3/3] Starting Copilot Engine...
echo.
echo   Server: http://127.0.0.1:7779
echo   Docs:   http://127.0.0.1:7779/docs
echo   Press Ctrl+C to stop.
echo.
call .venv\Scripts\python run.py
