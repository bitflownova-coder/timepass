@echo off
setlocal

set SCRIPT_DIR=%~dp0
for %%I in ("%SCRIPT_DIR%..") do set PROJECT_ROOT=%%~fI
set PYTHON_EXE=%PROJECT_ROOT%\venv\Scripts\python.exe
set BACKUP_SCRIPT=%PROJECT_ROOT%\scripts\backup.py

set TASK_TIME=%1
if "%TASK_TIME%"=="" set TASK_TIME=02:00

set TASK_NAME=%2
if "%TASK_NAME%"=="" set TASK_NAME=SmartDocAIBackup

if not exist "%PYTHON_EXE%" (
  echo Python not found: %PYTHON_EXE%
  exit /b 1
)

schtasks /Create /SC DAILY /TN "%TASK_NAME%" /TR "\"%PYTHON_EXE%\" \"%BACKUP_SCRIPT%\"" /ST %TASK_TIME% /F
if %ERRORLEVEL% NEQ 0 (
  echo Failed to create task.
  exit /b 1
)

schtasks /Query /TN "%TASK_NAME%" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
  echo Scheduled backup task created: %TASK_NAME% at %TASK_TIME%
) else (
  echo Task creation reported success but could not verify.
)

endlocal
