@echo off
title INCIZO
start "" "INCIZO-dashboard.html"
python hyro_ai_pro.py
if %errorlevel% neq 0 (
    echo.
    echo  Could not launch. Run INSTALL.bat first.
    pause
)
