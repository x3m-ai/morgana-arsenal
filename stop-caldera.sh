#!/bin/bash
# Stop Caldera server gracefully by sending SIGINT (Ctrl+C)
echo "Stopping Caldera server gracefully..."
PID=$(ps aux | grep "[p]ython3.*server.py" | grep morgana-arsenal | awk '{print $2}')
if [ -z "$PID" ]; then
    echo "No Caldera server running in morgana-arsenal"
    exit 0
fi
echo "Sending SIGINT to PID $PID..."
kill -INT $PID
sleep 3
if ps -p $PID > /dev/null 2>&1; then
    echo "Server still running, forcing shutdown..."
    kill -9 $PID
else
    echo "Server stopped gracefully"
fi
