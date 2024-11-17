#!/bin/bash

if [ ! -f "app.pid" ]; then
    echo "PID-file not found."
    exit 1
fi

PID=$(cat app.pid)

pkill -TERM -P $PID

kill $PID

if [ $? -eq 0 ]; then
    echo "App with PID $PID is finished."
    rm app.pid
else
    echo "Error, PID $PID."
    exit 1
fi
