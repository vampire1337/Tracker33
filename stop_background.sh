#!/bin/bash

echo "Stopping Tracker33 server..."

if [ -f "server.pid" ]; then
    PID=$(cat server.pid)
    if ps -p $PID > /dev/null; then
        echo "Killing process with PID: $PID"
        kill $PID
        echo "Server stopped."
    else
        echo "Process with PID $PID not found. The server might not be running."
    fi
    rm server.pid
else
    echo "PID file not found. The server might not be running."
fi 