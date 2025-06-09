@echo off
REM AI Checkout Automation - Python Backend Startup Script
REM This script starts the Python Flask server for the browser extension

echo Starting AI Checkout Automation Python Backend...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Python version:
python --version
echo.

REM Check if we're in the right directory
if not exist "requirements.txt" (
    echo ERROR: requirements.txt not found
    echo Please run this script from the python-backend directory
    pause
    exit /b 1
)

REM Create a virtual environment if it doesn't exist
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo Virtual environment created.
)

REM Activate virtual environment and install dependencies
echo Activating virtual environment and installing/updating dependencies...
call .venv\Scripts\activate.bat
pip install -r requirements.txt

if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    echo Please check your Python and pip installation, and ensure the virtual environment was activated.
    pause
    exit /b 1
)

echo.
echo Dependencies installed successfully into the virtual environment!
echo.

REM Start the Flask server
echo Starting Flask server on http://localhost:5000
echo.
echo IMPORTANT: Keep this window open while using the browser extension
echo Press Ctrl+C to stop the server
echo.

python server.py

echo.
echo Server stopped.
call .venv\Scripts\deactivate.bat
pause
