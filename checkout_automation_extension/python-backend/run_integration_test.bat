@echo off
REM AI Checkout Automation - Integration Test Runner
REM This script runs the complete integration test suite

echo ========================================
echo AI Checkout Automation Integration Test
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Check if we're in the right directory
if not exist "integration_test.py" (
    echo ERROR: integration_test.py not found
    echo Please run this script from the python-backend directory
    pause
    exit /b 1
)

REM Install requests if not already installed
echo Installing test dependencies...
pip install requests >nul 2>&1

REM Run the integration test
echo.
echo Running integration test suite...
echo.
python integration_test.py

echo.
echo Integration test completed.
pause
