@echo off
REM Bytestorm AI Product Recommendation System Launcher
REM This script activates the virtual environment, installs requirements, and starts the app

echo ======================================================
echo Bytestorm AI Product Recommendation System Launcher
echo ======================================================

REM Check if virtual environment exists, create if not
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate

REM Install requirements
echo Installing requirements...
pip install -r requirements.txt

REM Set default Voyage API Key
echo Setting default Voyage API Key...
set VOYAGE_API_KEY=pa-XQAgthfL8fQaoJWkagJgqOj6BTRbRlTKW-z-W_FLaDq

REM Prompt to override Voyage API Key (optional)
set /p VOYAGE_API_KEY_INPUT="Enter Voyage API Key (or press Enter to use default): "
if not "%VOYAGE_API_KEY_INPUT%"=="" (
    echo Setting custom Voyage API Key...
    set VOYAGE_API_KEY=%VOYAGE_API_KEY_INPUT%
)

REM Start the application
echo Starting main application...
echo Open http://localhost:3000 in your browser
python app.py

REM Deactivate environment (this will only run if the app is stopped)
call deactivate
