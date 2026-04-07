@echo off
REM Keep-Alive Script Runner for Windows
REM Double-click this file to start the keep-alive service

echo ========================================
echo Kuraz AI Keep-Alive Service
echo ========================================
echo.

REM Set your Render backend URL here
set BACKEND_URL=https://kuraz-ai-backend.onrender.com

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://python.org
    pause
    exit /b 1
)

REM Install requests if not already installed
echo Installing dependencies...
pip install requests >nul 2>&1

echo.
echo Starting keep-alive service...
echo Target: %BACKEND_URL%
echo Press Ctrl+C to stop
echo.

REM Run the keep-alive script
python keep_alive.py

pause
