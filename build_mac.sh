#!/bin/bash
# Build para macOS - genera ScreenControl.app y lo agrega al inicio

set -e

VENV_DIR=".venv"

# Crear entorno virtual si no existe
if [ ! -d "$VENV_DIR" ]; then
    echo "=== Creando entorno virtual ==="
    python3 -m venv "$VENV_DIR"
fi

# Activar entorno virtual
source "$VENV_DIR/bin/activate"

echo "=== Instalando dependencias ==="
pip install monitorcontrol Pillow pystray pyinstaller

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
