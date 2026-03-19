# Screen Control

Aplicacion para cambiar la entrada de monitores (HDMI, DisplayPort, etc.) via DDC/CI.
Se minimiza al system tray y puede iniciarse automaticamente con el sistema.

## Requisitos

- Python 3.10+
- Monitor con soporte DDC/CI habilitado

## Instalacion

```bash
pip install -r requirements.txt
```

### Dependencias

| Paquete          | Uso                                      |
|------------------|------------------------------------------|
| monitorcontrol   | Comunicacion DDC/CI con monitores        |
| Pillow           | Generacion del icono del tray (macOS)    |
| pystray          | System tray en macOS                     |
| pyinstaller      | Empaquetado como .exe / .app             |

## Uso

### Ejecutar desde Python

```bash
python screen_control.py
```

### Detectar monitores (CLI)

```bash
python detect_ddc.py
python detect_ddc.py --set-input
```

## Comportamiento

- Al cerrar la ventana (X), se **minimiza al system tray** en lugar de cerrarse.
- **Doble click** en el icono del tray restaura la ventana.
- **Click derecho** en el icono del tray muestra un menu con "Abrir" y "Salir".
- Solo se muestran las entradas disponibles del monitor (consultadas via VCP code 0x60).

## Build Windows (.exe)

```bash
pyinstaller --onefile --windowed --name "ScreenControl" --icon icon.ico --add-data "icon.ico;." screen_control.py
```

El ejecutable queda en `dist/ScreenControl.exe`.

### Inicio automatico (Windows)

Agregar al inicio:

```bash
python install_startup_windows.py
```

Quitar del inicio:

```bash
python install_startup_windows.py --uninstall
```

Esto copia/elimina el `.exe` de la carpeta `shell:startup`.

## Build macOS (.app)

```bash
chmod +x build_mac.sh
./build_mac.sh
```

El script genera `dist/ScreenControl.app` y ofrece agregarlo a los Login Items de macOS.

### Inicio automatico (macOS manual)

Si no lo agregaste durante el build:

```bash
osascript -e 'tell application "System Events" to make login item at end with properties {path:"/ruta/a/dist/ScreenControl.app", hidden:false}'
```

## Estructura

```
screen-control/
├── screen_control.py            # App principal con GUI
├── detect_ddc.py                # Script CLI de deteccion
├── icon.ico                     # Icono de la app
├── install_startup_windows.py   # Instalar/desinstalar del inicio (Windows)
├── build_mac.sh                 # Script de build para macOS
├── requirements.txt             # Dependencias
└── dist/
    └── ScreenControl.exe        # Ejecutable Windows
```

## Solucion de problemas

| Problema                          | Solucion                                                                 |
|-----------------------------------|--------------------------------------------------------------------------|
| No se detectan monitores          | Verificar que DDC/CI este habilitado en el menu OSD del monitor          |
| Error I2C en un monitor           | El cable o adaptador no transmite senales DDC, o el monitor no soporta DDC/CI |
| Sin entradas detectadas           | El monitor no reporta entradas en sus VCP capabilities                   |
| El icono no aparece en el tray    | Revisar los iconos ocultos (flecha ^ en la barra de tareas de Windows)   |
