#!/bin/bash
# Bytestorm AI Product Recommendation System Launcher
# This script activates the virtual environment, installs requirements, and starts the app

echo "======================================================"
echo "Bytestorm AI Product Recommendation System Launcher"
echo "======================================================"

# Check if virtual environment exists, create if not
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt

# Set default Voyage API Key
echo "Setting default Voyage API Key..."
export VOYAGE_API_KEY="pa-XQAgthfL8fQaoJWkagJgqOj6BTRbRlTKW-z-W_FLaDq"

# Prompt to override Voyage API Key (optional)
read -p "Enter Voyage API Key (or press Enter to use default): " VOYAGE_API_KEY_INPUT
if [ ! -z "$VOYAGE_API_KEY_INPUT" ]; then
    echo "Setting custom Voyage API Key..."
    export VOYAGE_API_KEY="$VOYAGE_API_KEY_INPUT"
fi

# Start the application
echo "Starting main application..."
echo "Open http://localhost:3000 in your browser"
python app.py

# Deactivate environment (this will only run if the app is stopped)
deactivate
