#!/bin/bash
# Bytestorm AI - Complete Application Launcher
# This script starts both the main application and the checkout automation server

echo "==================================================="
echo "Bytestorm AI - Complete Application Launcher"
echo "==================================================="

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Start the main application in a new terminal
echo "Starting main application in a new terminal..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    osascript -e "tell app \"Terminal\" to do script \"cd '$SCRIPT_DIR' && ./run.sh\""
else
    # Linux - try different terminal emulators
    if command -v gnome-terminal &> /dev/null; then
        gnome-terminal -- bash -c "cd '$SCRIPT_DIR' && ./run.sh; exec bash"
    elif command -v xterm &> /dev/null; then
        xterm -e "cd '$SCRIPT_DIR' && ./run.sh; exec bash" &
    elif command -v konsole &> /dev/null; then
        konsole -e "cd '$SCRIPT_DIR' && ./run.sh; exec bash" &
    else
        echo "Could not find a suitable terminal emulator. Please run the applications manually."
        exit 1
    fi
fi

# Give the first terminal a moment to start
sleep 2

# Start the checkout automation server in a new terminal
echo "Starting checkout automation server in a new terminal..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    osascript -e "tell app \"Terminal\" to do script \"cd '$SCRIPT_DIR/checkout_automation_extension/python-backend' && ./start_server.sh\""
else
    # Linux - try different terminal emulators
    if command -v gnome-terminal &> /dev/null; then
        gnome-terminal -- bash -c "cd '$SCRIPT_DIR/checkout_automation_extension/python-backend' && ./start_server.sh; exec bash"
    elif command -v xterm &> /dev/null; then
        xterm -e "cd '$SCRIPT_DIR/checkout_automation_extension/python-backend' && ./start_server.sh; exec bash" &
    elif command -v konsole &> /dev/null; then
        konsole -e "cd '$SCRIPT_DIR/checkout_automation_extension/python-backend' && ./start_server.sh; exec bash" &
    else
        echo "Could not find a suitable terminal emulator. Please run the applications manually."
        exit 1
    fi
fi

echo "Both applications have been started in separate terminals."
echo "Main application URL: http://localhost:3000"
echo "Checkout automation server URL: http://localhost:5000"
