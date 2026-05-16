@echo off
REM SmartHelmetGuard - Windows Launcher Script
REM This script sets up the environment and launches the dashboard

echo.
echo ====================================
echo SmartHelmetGuard - Helmet Detector
echo ====================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org/
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/update requirements
echo Installing dependencies...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo WARNING: Some dependencies may have failed to install
    echo Continuing anyway...
)

REM Run dashboard
echo.
echo Starting SmartHelmetGuard Dashboard...
echo.
echo Dashboard will open at: http://localhost:8501
echo Press Ctrl+C to stop
echo.

streamlit run dashboard.py

pause
