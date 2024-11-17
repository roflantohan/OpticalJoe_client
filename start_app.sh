#!/bin/bash
# Путь к папке с виртуальным окружением
VENV_PATH="./.venv"
# Путь к вашему Python-приложению
APP_PATH="./main.py"

source .venv/bin/activate

# Проверяем, запущено ли приложение уже
if [ -f "app.pid" ]; then
    echo "Приложение уже запущено!"
    exit 1
fi

# Запускаем приложение в фоновом режиме и записываем его PID в файл
nohup python main.py > app.log 2>&1 &
echo $! > app.pid
echo "App is launched PID $(cat app.pid)"
