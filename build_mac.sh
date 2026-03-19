#!/bin/bash
# Build para macOS - genera ScreenControl.app y lo agrega al inicio

set -e

echo "=== Instalando dependencias ==="
pip3 install monitorcontrol Pillow pystray pyinstaller

echo "=== Generando ScreenControl.app ==="
pyinstaller --onefile --windowed \
    --name "ScreenControl" \
    --add-data "icon.ico:." \
    screen_control.py

echo "=== Build completo: dist/ScreenControl.app ==="

# Agregar al inicio automatico de macOS (Login Items via osascript)
read -p "Agregar al inicio automatico? (s/n): " answer
if [ "$answer" = "s" ]; then
    APP_PATH="$(pwd)/dist/ScreenControl.app"
    osascript -e "tell application \"System Events\" to make login item at end with properties {path:\"$APP_PATH\", hidden:false}"
    echo "Agregado al inicio automatico de macOS."
fi
