"""Agrega ScreenControl.exe al inicio automatico de Windows."""

import os
import shutil

def install():
    exe_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dist", "ScreenControl.exe")
    startup_dir = os.path.join(os.environ["APPDATA"], "Microsoft", "Windows", "Start Menu", "Programs", "Startup")
    dest = os.path.join(startup_dir, "ScreenControl.exe")

    if not os.path.exists(exe_path):
        print(f"No se encontro: {exe_path}")
        print("Primero genera el .exe con PyInstaller.")
        return

    shutil.copy2(exe_path, dest)
    print(f"Copiado a: {dest}")
    print("ScreenControl se iniciara automaticamente con Windows.")

def uninstall():
    startup_dir = os.path.join(os.environ["APPDATA"], "Microsoft", "Windows", "Start Menu", "Programs", "Startup")
    dest = os.path.join(startup_dir, "ScreenControl.exe")
    if os.path.exists(dest):
        os.remove(dest)
        print("Eliminado del inicio automatico.")
    else:
        print("No estaba instalado en el inicio.")

if __name__ == "__main__":
    import sys
    if "--uninstall" in sys.argv:
        uninstall()
    else:
        install()
