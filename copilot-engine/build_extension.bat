@echo off
REM ============================================
REM  Copilot Engine - Extension Build & Package
REM ============================================

echo.
echo ========================================
echo   Copilot Engine Extension Builder
echo ========================================
echo.

cd /d "%~dp0extension"

REM 1. Install dependencies
echo [1/4] Installing dependencies...
call npm install --silent
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: npm install failed
    exit /b 1
)
echo       Done.

REM 2. Compile TypeScript
echo [2/4] Compiling TypeScript...
call npx webpack --mode production 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Webpack build failed
    exit /b 1
)
echo       Done.

REM 3. Package VSIX
echo [3/4] Packaging VSIX...
call npx vsce package --no-dependencies 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: VSIX packaging failed. Try: npm install -g @vscode/vsce
    exit /b 1
)
echo       Done.

REM 4. Show result
echo [4/4] Locating package...
for %%f in (*.vsix) do (
    echo.
    echo ========================================
    echo   SUCCESS: %%f
    echo ========================================
    echo.
    echo Install with:
    echo   code --install-extension %%f
    echo.
)

cd /d "%~dp0"
