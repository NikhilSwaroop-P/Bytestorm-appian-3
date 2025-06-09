@echo off
REM AI Checkout Automation - Setup Validation Script
REM This script validates that everything is set up correctly

echo ========================================
echo AI Checkout Automation Setup Validator
echo ========================================
echo.

REM Check if Python is available
echo [1/5] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo   ❌ Python is not installed or not in PATH
    echo   Please install Python 3.8+ from https://www.python.org/downloads/
    goto :error
) else (
    echo   ✅ Python is available
    python --version
)
echo.

REM Check if we're in the right directory
echo [2/5] Checking directory structure...
if not exist "requirements.txt" (
    echo   ❌ requirements.txt not found
    echo   Please run this script from the python-backend directory
    goto :error
) else (
    echo   ✅ In correct directory
)

if not exist "server.py" (
    echo   ❌ server.py not found
    echo   Please ensure all Python backend files are present
    goto :error
) else (
    echo   ✅ Server files found
)
echo.

REM Check if Google API key is set
echo [3/5] Checking environment variables...
if "%GOOGLE_API_KEY%"=="" (
    echo   ⚠️  GOOGLE_API_KEY environment variable not set
    echo   You'll need to set this before running the server:
    echo   set GOOGLE_API_KEY=your_api_key_here
) else (
    echo   ✅ GOOGLE_API_KEY is set
)
echo.

REM Install dependencies
echo [4/5] Installing Python dependencies...
pip install -r requirements.txt >nul 2>&1
if errorlevel 1 (
    echo   ❌ Failed to install dependencies
    echo   Please check your pip installation
    goto :error
) else (
    echo   ✅ Dependencies installed successfully
)
echo.

REM Test basic imports
echo [5/5] Testing Python imports...
python -c "import flask, flask_cors, google.generativeai; print('  ✅ All required packages imported successfully')" 2>nul
if errorlevel 1 (
    echo   ❌ Some required packages failed to import
    echo   Please check the error messages above
    goto :error
)
echo.

echo ========================================
echo ✅ Setup validation completed successfully!
echo ========================================
echo.
echo You can now start the server with:
echo   start_server.bat
echo.
echo Or test the backend with:
echo   python test_backend.py
echo.
pause
exit /b 0

:error
echo.
echo ========================================
echo ❌ Setup validation failed!
echo ========================================
echo Please fix the issues above and try again.
echo.
pause
exit /b 1
