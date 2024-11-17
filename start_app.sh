#!/bin/bash
source .venv/bin/activate

if [ -f "app.pid" ]; then
    echo "App's already runned!"
    exit 1
fi

nohup python main.py > app.log 2>&1 &
echo $! > app.pid
echo "App's launched, PID $(cat app.pid)"
