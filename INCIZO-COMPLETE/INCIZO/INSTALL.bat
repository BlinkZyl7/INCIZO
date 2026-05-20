@echo off
title INCIZO — Setup
color 0A
cls
echo.
echo  +---------------------------------+
echo  ^|  I N C I Z O  v1.0             ^|
echo  ^|  Cut through the noise.        ^|
echo  +---------------------------------+
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  ERROR: Python not found.
    echo.
    echo  1. Go to: https://python.org/downloads
    echo  2. Download and install Python
    echo  3. CHECK "Add Python to PATH" during install
    echo  4. Restart your PC and run this again
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version') do set PYVER=%%i
echo  Found: %PYVER%
echo.
echo  Installing required packages...
echo.

pip install anthropic pillow pyautogui --quiet
if %errorlevel% neq 0 (
    pip install anthropic pillow pyautogui --quiet --user
)

echo.
echo  +---------------------------------+
echo  ^|  Setup complete!               ^|
echo  +---------------------------------+
echo.
echo  Opening your INCIZO dashboard...
start "" "INCIZO-dashboard.html"
echo.
echo  Launching AI watcher...
echo  (Get your free API key at console.anthropic.com)
echo  (Paste it in the Settings tab when the app opens)
echo.
python hyro_ai_pro.py
pause
