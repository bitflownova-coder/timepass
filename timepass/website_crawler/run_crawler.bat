@echo off
cd /d "%~dp0"
title Website Crawler
echo ==================================================
echo           Starting Website Crawler
echo ==================================================
echo.
echo Please wait for the server to start...
echo Once started, open your browser to: http://127.0.0.1:5000
echo.
echo Press Ctrl+C to stop the server.
echo.

python app.py

if %errorlevel% neq 0 (
    echo.
    echo Error: The application crashed or failed to start.
    echo Ensure Python is installed and dependencies are satisfied.
    echo.
    pause
)
