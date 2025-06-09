#!/bin/bash

# AI Checkout Automation - Python Backend Startup Script
# This script starts the Python Flask server for the browser extension

echo "Starting AI Checkout Automation Python Backend..."
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed or not in PATH"
    echo "Please install Python 3.8+ from your package manager or https://www.python.org/downloads/"
    exit 1
fi

echo "Python version:"
python3 --version
echo

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo "ERROR: requirements.txt not found"
    echo "Please run this script from the python-backend directory"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
    
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to create virtual environment"
        echo "Please check your Python installation"
        exit 1
    fi
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing/updating Python dependencies..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies"
    echo "Please check your Python and pip installation"
    exit 1
fi

echo
echo "Dependencies installed successfully!"
echo

# Start the Flask server
echo "Starting Flask server on http://localhost:5000"
echo
echo "IMPORTANT: Keep this terminal open while using the browser extension"
echo "Press Ctrl+C to stop the server"
echo

python server.py

echo
echo "Server stopped."
