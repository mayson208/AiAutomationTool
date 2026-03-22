@echo off
title STUDIO — AI YouTube Automation
cd /d "%~dp0"
echo.
echo  ================================================
echo   STUDIO — AI YouTube Automation Dashboard
echo  ================================================
echo.
echo  Starting Flask server on http://localhost:5000
echo  Press Ctrl+C to stop.
echo.
python app.py
pause
