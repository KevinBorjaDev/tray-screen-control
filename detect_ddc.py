"""
Script para detectar soporte DDC/CI y controlar monitores.
Uso:
  python detect_ddc.py              -> Detectar monitores y mostrar info
  python detect_ddc.py --set-input  -> Cambiar entrada del monitor
"""

import sys
from monitorcontrol import get_monitors
from monitorcontrol.monitorcontrol import InputSource

INPUT_SOURCE_NAMES = {
    1: "VGA-1",
    2: "VGA-2",
    3: "DVI-1",
    4: "DVI-2",
    5: "Composite Video 1",
    6: "Composite Video 2",
    7: "S-Video-1",
    8: "S-Video-2",
    9: "Tuner-1",
    10: "Tuner-2",
    11: "Tuner-3",
    12: "Component Video 1",
    13: "Component Video 2",
    14: "Component Video 3",
    15: "DisplayPort-1",
    16: "DisplayPort-2",
    17: "HDMI-1",
    18: "HDMI-2",
}


def detect_monitors():
    monitors = get_monitors()
    if not monitors:
        print("No se detectaron monitores con DDC/CI.")
        print("Posibles causas:")
        print("  - El monitor no soporta DDC/CI")
        print("  - DDC/CI esta desactivado en el menu OSD del monitor")
        print("  - El cable/adaptador no transmite senales DDC")
        return []

    print(f"Se detectaron {len(monitors)} monitor(es) con DDC/CI:\n")

    for i, monitor in enumerate(monitors):
        print(f"--- Monitor {i + 1} ---")
        try:
            with monitor:
                # Brillo
                try:
                    brightness = monitor.get_luminance()
                    print(f"  Brillo: {brightness}%")
                except Exception:
                    print("  Brillo: no disponible")

                # Contraste
                try:
                    contrast = monitor.get_contrast()
                    print(f"  Contraste: {contrast}%")
                except Exception:
                    print("  Contraste: no disponible")

                # Entrada actual
                try:
                    input_source = monitor.get_input_source()
                    val = input_source.value if hasattr(input_source, "value") else int(input_source)
                    name = INPUT_SOURCE_NAMES.get(val, f"Desconocido ({val})")
                    print(f"  Entrada actual: {name} (valor: {val})")
                except Exception as e:
                    print(f"  Entrada actual: no se pudo leer ({e})")

                # VCP capabilities raw
                try:
                    caps = monitor.get_vcp_capabilities()
                    if "inputs" in caps:
                        print(f"  Entradas soportadas: {caps['inputs']}")
                except Exception:
                    pass

        except Exception as e:
            print(f"  Error al comunicarse con el monitor: {e}")
        print()

    return monitors


def change_input(monitors):
    if not monitors:
        print("No hay monitores disponibles.")
        return

    print("Entradas disponibles:")
    for val, name in sorted(INPUT_SOURCE_NAMES.items()):
        print(f"  {val:2d} = {name}")

    print()
    monitor_idx = 0
    if len(monitors) > 1:
        monitor_idx = int(input(f"Selecciona monitor (1-{len(monitors)}): ")) - 1

    source = int(input("Ingresa el numero de entrada deseada: "))

    try:
        with monitors[monitor_idx]:
            monitors[monitor_idx].set_input_source(InputSource(source))
        print(f"Entrada cambiada a {INPUT_SOURCE_NAMES.get(source, source)}")
    except Exception as e:
        print(f"Error al cambiar entrada: {e}")


if __name__ == "__main__":
    print("=== Deteccion DDC/CI ===\n")
    monitors = detect_monitors()

    if "--set-input" in sys.argv and monitors:
        change_input(monitors)
