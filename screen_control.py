"""
Screen Control - Cambia la entrada de tus monitores via DDC/CI.
Funciona en Windows y macOS.

Uso: python screen_control.py
"""

import os
import platform
import re
import sys
import threading
import tkinter as tk
from tkinter import ttk, messagebox

from monitorcontrol import get_monitors

IS_WINDOWS = platform.system() == "Windows"
IS_MAC = platform.system() == "Darwin"

# PyInstaller guarda archivos extra en _MEIPASS cuando es .exe empaquetado
if getattr(sys, "frozen", False):
    APP_DIR = sys._MEIPASS
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))

INPUT_SOURCES = {
    1: "VGA-1",
    2: "VGA-2",
    3: "DVI-1",
    4: "DVI-2",
    5: "Composite 1",
    6: "Composite 2",
    7: "S-Video-1",
    8: "S-Video-2",
    9: "Tuner-1",
    10: "Tuner-2",
    11: "Tuner-3",
    12: "Component 1",
    13: "Component 2",
    14: "Component 3",
    15: "DisplayPort-1",
    16: "DisplayPort-2",
    17: "HDMI-1",
    18: "HDMI-2",
}

SHORT_NAMES = {
    1: "VGA-1", 2: "VGA-2", 3: "DVI-1", 4: "DVI-2",
    15: "DP-1", 16: "DP-2", 17: "HDMI-1", 18: "HDMI-2",
}


def get_available_inputs_windows():
    """Consulta las entradas disponibles de cada monitor via Windows DDC API."""
    import ctypes
    from ctypes import wintypes

    dxva2 = ctypes.windll.dxva2
    results = {}
    handles = []

    def callback(hmon, hdc, lprect, lparam):
        count = wintypes.DWORD()
        dxva2.GetNumberOfPhysicalMonitorsFromHMONITOR(hmon, ctypes.byref(count))
        if count.value > 0:

            class PHYSICAL_MONITOR(ctypes.Structure):
                _fields_ = [
                    ("hPhysicalMonitor", wintypes.HANDLE),
                    ("szPhysicalMonitorDescription", wintypes.WCHAR * 128),
                ]

            arr = (PHYSICAL_MONITOR * count.value)()
            dxva2.GetPhysicalMonitorsFromHMONITOR(hmon, count.value, arr)
            for pm in arr:
                handles.append((pm.hPhysicalMonitor, pm.szPhysicalMonitorDescription))
        return True

    MONITORENUMPROC = ctypes.WINFUNCTYPE(
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_ulong),
        ctypes.POINTER(ctypes.c_ulong),
        ctypes.POINTER(wintypes.RECT),
        ctypes.POINTER(ctypes.c_ulong),
    )
    ctypes.windll.user32.EnumDisplayMonitors(None, None, MONITORENUMPROC(callback), 0)

    for i, (handle, desc) in enumerate(handles):
        cap_len = wintypes.DWORD()
        if dxva2.GetCapabilitiesStringLength(handle, ctypes.byref(cap_len)):
            buf = (ctypes.c_char * (cap_len.value + 1))()
            if dxva2.CapabilitiesRequestAndCapabilitiesReply(handle, buf, cap_len):
                caps_str = buf.value.decode("ascii", errors="replace")
                match = re.search(r"60\(([^)]+)\)", caps_str)
                if match:
                    hex_vals = match.group(1).split()
                    results[i] = [int(v, 16) for v in hex_vals if v.strip()]
        dxva2.DestroyPhysicalMonitor(handle)

    return results


def get_available_inputs():
    if IS_WINDOWS:
        return get_available_inputs_windows()
    return {}


# --- Brightness Popup ---

class BrightnessPopup(tk.Toplevel):
    """Ventana pequena de control de brillo que aparece cerca del tray."""

    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.title("Brillo")
        self.resizable(False, False)
        self.overrideredirect(True)  # Sin barra de titulo
        self.configure(bg="#2d2d2d")
        self.attributes("-topmost", True)

        # Borde redondeado simulado
        self.border = tk.Frame(self, bg="#404040", padx=1, pady=1)
        self.border.pack(fill="both", expand=True)

        self.inner = tk.Frame(self.border, bg="#2d2d2d")
        self.inner.pack(fill="both", expand=True, padx=1, pady=1)

        # Header
        header = tk.Frame(self.inner, bg="#2d2d2d")
        header.pack(fill="x", padx=10, pady=(8, 4))
        tk.Label(header, text="Brillo", font=("Segoe UI", 10, "bold"),
                 bg="#2d2d2d", fg="white").pack(side="left")

        self.sliders = []
        self._build_sliders()

        # Cerrar al perder foco
        self.bind("<FocusOut>", self._on_focus_out)

        # Posicionar cerca del tray (esquina inferior derecha)
        self.update_idletasks()
        w = max(self.winfo_reqwidth(), 280)
        h = self.winfo_reqheight()
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        # Arriba del tray, esquina inferior derecha
        x = screen_w - w - 12
        y = screen_h - h - 50
        self.geometry(f"{w}x{h}+{x}+{y}")

        self.focus_force()

    def _build_sliders(self):
        monitors = get_monitors()
        if not monitors:
            tk.Label(self.inner, text="Sin monitores", bg="#2d2d2d", fg="gray",
                     font=("Segoe UI", 9)).pack(padx=10, pady=8)
            return

        for i, mon in enumerate(monitors):
            frame = tk.Frame(self.inner, bg="#2d2d2d")
            frame.pack(fill="x", padx=10, pady=(4, 8))

            lbl = tk.Label(frame, text=f"Monitor {i + 1}", bg="#2d2d2d", fg="#aaaaaa",
                           font=("Segoe UI", 9))
            lbl.pack(anchor="w")

            slider_frame = tk.Frame(frame, bg="#2d2d2d")
            slider_frame.pack(fill="x")

            val_label = tk.Label(slider_frame, text="--", bg="#2d2d2d", fg="white",
                                 font=("Segoe UI", 9), width=4)
            val_label.pack(side="right")

            slider = ttk.Scale(slider_frame, from_=0, to=100, orient="horizontal",
                               command=lambda v, m=mon, vl=val_label, idx=i: self._on_slide(v, m, vl, idx))
            slider.pack(side="left", fill="x", expand=True, padx=(0, 4))

            self.sliders.append((mon, slider, val_label, lbl))

            # Leer brillo actual en hilo
            threading.Thread(target=self._read_brightness, args=(mon, slider, val_label, lbl), daemon=True).start()

    def _read_brightness(self, monitor, slider, val_label, name_label):
        try:
            with monitor:
                b = monitor.get_luminance()
            self.after(0, lambda: self._set_slider(slider, val_label, b))
        except Exception:
            self.after(0, lambda: val_label.config(text="--"))
            self.after(0, lambda: name_label.config(fg="#555555"))

    def _set_slider(self, slider, val_label, value):
        slider.set(value)
        val_label.config(text=f"{value}%")

    def _on_slide(self, value, monitor, val_label, monitor_idx):
        brightness = int(float(value))
        val_label.config(text=f"{brightness}%")

        # Debounce: solo enviar si no hay un envio pendiente
        if not hasattr(self, "_pending"):
            self._pending = {}
        self._pending[monitor_idx] = brightness

        # Usar after para no enviar en cada pixel del slider
        if not hasattr(self, "_after_ids"):
            self._after_ids = {}
        if monitor_idx in self._after_ids:
            self.after_cancel(self._after_ids[monitor_idx])
        self._after_ids[monitor_idx] = self.after(
            150, lambda: self._send_brightness(monitor, monitor_idx)
        )

    def _send_brightness(self, monitor, monitor_idx):
        brightness = self._pending.get(monitor_idx)
        if brightness is None:
            return
        threading.Thread(target=self._do_set_brightness, args=(monitor, brightness), daemon=True).start()

    def _do_set_brightness(self, monitor, brightness):
        try:
            with monitor:
                monitor.set_luminance(brightness)
        except Exception:
            pass

    def _on_focus_out(self, event):
        # Pequeño delay para evitar cerrar por transiciones internas
        self.after(200, self._check_focus)

    def _check_focus(self):
        try:
            focused = self.focus_get()
            if focused is None or not str(focused).startswith(str(self)):
                self.destroy()
        except Exception:
            self.destroy()


# --- System Tray ---

def create_tray_icon_image():
    """Crea un icono de monitor con PIL (usado en macOS)."""
    from PIL import Image, ImageDraw
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([4, 6, 60, 42], radius=3, fill="#1E88E5", outline="#0D47A1", width=2)
    draw.rectangle([10, 12, 54, 36], fill="#BBDEFB")
    draw.polygon([(22, 24), (30, 18), (30, 30)], fill="#0D47A1")
    draw.polygon([(42, 24), (34, 18), (34, 30)], fill="#0D47A1")
    draw.rectangle([28, 42, 36, 48], fill="#0D47A1")
    draw.rounded_rectangle([20, 48, 44, 54], radius=2, fill="#0D47A1")
    return img


class TrayWindows:
    """System tray usando la API nativa Win32."""

    def __init__(self, app):
        self.app = app
        self._click_pending = False

    def start(self):
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        import ctypes
        from ctypes import wintypes

        WM_USER = 0x0400
        WM_TRAYICON = WM_USER + 1
        WM_COMMAND = 0x0111
        WM_DESTROY = 0x0002
        WM_LBUTTONUP = 0x0202
        WM_RBUTTONUP = 0x0205
        WM_LBUTTONDBLCLK = 0x0203
        NIM_ADD = 0x00000000
        NIM_DELETE = 0x00000002
        NIF_ICON = 0x00000002
        NIF_MESSAGE = 0x00000001
        NIF_TIP = 0x00000004
        IDI_APPLICATION = 32512
        TPM_LEFTALIGN = 0x0000
        ID_OPEN = 1
        ID_QUIT = 2

        user32 = ctypes.windll.user32
        shell32 = ctypes.windll.shell32
        kernel32 = ctypes.windll.kernel32

        # Tiempo de doble click del sistema
        dblclick_time = user32.GetDoubleClickTime()

        class NOTIFYICONDATA(ctypes.Structure):
            _fields_ = [
                ("cbSize", wintypes.DWORD),
                ("hWnd", wintypes.HWND),
                ("uID", wintypes.UINT),
                ("uFlags", wintypes.UINT),
                ("uCallbackMessage", wintypes.UINT),
                ("hIcon", wintypes.HICON),
                ("szTip", wintypes.WCHAR * 128),
            ]

        WNDPROC = ctypes.WINFUNCTYPE(
            ctypes.c_long, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM
        )

        app = self.app
        tray = self

        def wnd_proc(hwnd, msg, wparam, lparam):
            if msg == WM_TRAYICON:
                if lparam == WM_LBUTTONUP:
                    # Esperar para ver si viene doble click
                    tray._click_pending = True
                    app.after(dblclick_time + 50, lambda: tray._handle_single_click())
                elif lparam == WM_LBUTTONDBLCLK:
                    # Cancelar el single click pendiente
                    tray._click_pending = False
                    app.after(0, app.restore_window)
                elif lparam == WM_RBUTTONUP:
                    menu = user32.CreatePopupMenu()
                    user32.AppendMenuW(menu, 0, ID_OPEN, "Abrir")
                    user32.AppendMenuW(menu, 0x0800, 0, None)
                    user32.AppendMenuW(menu, 0, ID_QUIT, "Salir")
                    pt = wintypes.POINT()
                    user32.GetCursorPos(ctypes.byref(pt))
                    user32.SetForegroundWindow(hwnd)
                    user32.TrackPopupMenu(menu, TPM_LEFTALIGN, pt.x, pt.y, 0, hwnd, None)
                    user32.DestroyMenu(menu)
            elif msg == WM_COMMAND:
                cmd = wparam & 0xFFFF
                if cmd == ID_OPEN:
                    app.after(0, app.restore_window)
                elif cmd == ID_QUIT:
                    nid = NOTIFYICONDATA()
                    nid.cbSize = ctypes.sizeof(nid)
                    nid.hWnd = hwnd
                    nid.uID = 1
                    shell32.Shell_NotifyIconW(NIM_DELETE, ctypes.byref(nid))
                    user32.DestroyWindow(hwnd)
                    app.after(0, app.destroy)
            elif msg == WM_DESTROY:
                user32.PostQuitMessage(0)
            return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

        self._wnd_proc = WNDPROC(wnd_proc)
        hinstance = kernel32.GetModuleHandleW(None)
        class_name = "ScreenControlTray"

        class WNDCLASSW(ctypes.Structure):
            _fields_ = [
                ("style", wintypes.UINT),
                ("lpfnWndProc", WNDPROC),
                ("cbClsExtra", ctypes.c_int),
                ("cbWndExtra", ctypes.c_int),
                ("hInstance", wintypes.HINSTANCE),
                ("hIcon", wintypes.HICON),
                ("hCursor", wintypes.HANDLE),
                ("hbrBackground", wintypes.HBRUSH),
                ("lpszMenuName", wintypes.LPCWSTR),
                ("lpszClassName", wintypes.LPCWSTR),
            ]

        wc = WNDCLASSW()
        wc.lpfnWndProc = self._wnd_proc
        wc.hInstance = hinstance
        wc.lpszClassName = class_name
        user32.RegisterClassW(ctypes.byref(wc))

        hwnd = user32.CreateWindowExW(
            0, class_name, "Screen Control Tray", 0,
            0, 0, 0, 0, None, None, hinstance, None,
        )

        icon_path = os.path.join(APP_DIR, "icon.ico")
        IMAGE_ICON = 1
        LR_LOADFROMFILE = 0x0010
        LR_DEFAULTSIZE = 0x0040
        hicon = user32.LoadImageW(None, icon_path, IMAGE_ICON, 0, 0, LR_LOADFROMFILE | LR_DEFAULTSIZE)
        if not hicon:
            hicon = user32.LoadIconW(None, IDI_APPLICATION)

        nid = NOTIFYICONDATA()
        nid.cbSize = ctypes.sizeof(nid)
        nid.hWnd = hwnd
        nid.uID = 1
        nid.uFlags = NIF_ICON | NIF_MESSAGE | NIF_TIP
        nid.uCallbackMessage = WM_TRAYICON
        nid.hIcon = hicon
        nid.szTip = "Screen Control"
        shell32.Shell_NotifyIconW(NIM_ADD, ctypes.byref(nid))

        msg = wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))

    def _handle_single_click(self):
        if self._click_pending:
            self._click_pending = False
            self.app.show_brightness_popup()


class TrayMac:
    """System tray usando pystray (macOS menu bar)."""

    def __init__(self, app):
        self.app = app
        self.icon = None

    def start(self):
        import pystray
        menu = pystray.Menu(
            pystray.MenuItem("Brillo", self._brightness),
            pystray.MenuItem("Abrir", self._show, default=True),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Salir", self._quit),
        )
        self.icon = pystray.Icon("screen_control", create_tray_icon_image(), "Screen Control", menu)
        threading.Thread(target=self.icon.run, daemon=True).start()

    def _brightness(self, icon=None, item=None):
        self.app.after(0, self.app.show_brightness_popup)

    def _show(self, icon=None, item=None):
        self.app.after(0, self.app.restore_window)

    def _quit(self, icon=None, item=None):
        if self.icon:
            self.icon.stop()
        self.app.after(0, self.app.destroy)


# --- GUI ---

class MonitorCard(ttk.LabelFrame):
    """Widget que muestra info y controles de un monitor."""

    def __init__(self, parent, index, monitor, available_inputs=None, **kwargs):
        super().__init__(parent, text=f"  Monitor {index + 1}  ", **kwargs)
        self.monitor = monitor
        self.index = index
        self.available = False
        self.supported_inputs = available_inputs or []

        self.info_frame = ttk.Frame(self)
        self.info_frame.pack(fill="x", padx=12, pady=(8, 4))

        self.lbl_status = ttk.Label(self.info_frame, text="Detectando...", font=("Segoe UI", 9))
        self.lbl_status.pack(anchor="w")

        self.lbl_brightness = ttk.Label(self.info_frame, text="", font=("Segoe UI", 9))
        self.lbl_brightness.pack(anchor="w")

        self.lbl_input = ttk.Label(self.info_frame, text="", font=("Segoe UI", 10, "bold"))
        self.lbl_input.pack(anchor="w", pady=(2, 0))

        self.btn_frame = ttk.Frame(self)
        self.btn_frame.pack(fill="x", padx=12, pady=(4, 10))

        self._create_buttons()
        self.load_info()

    def _create_buttons(self):
        for widget in self.btn_frame.winfo_children():
            widget.destroy()

        if self.supported_inputs:
            for val in self.supported_inputs:
                label = SHORT_NAMES.get(val, INPUT_SOURCES.get(val, f"#{val}"))
                btn = ttk.Button(
                    self.btn_frame,
                    text=label,
                    width=8,
                    command=lambda v=val: self.set_input(v),
                )
                btn.pack(side="left", padx=2, pady=2)
        else:
            ttk.Label(self.btn_frame, text="Sin entradas detectadas", foreground="gray").pack(anchor="w")

    def load_info(self):
        threading.Thread(target=self._read_monitor, daemon=True).start()

    def _read_monitor(self):
        brightness_text = ""
        input_text = "Entrada: desconocida"
        status = ""

        try:
            with self.monitor:
                self.available = True
                try:
                    b = self.monitor.get_luminance()
                    c = self.monitor.get_contrast()
                    brightness_text = f"Brillo: {b}%  |  Contraste: {c}%"
                except Exception:
                    brightness_text = "Brillo/Contraste: no disponible"

                try:
                    raw = self.monitor.get_input_source()
                    val = raw.value if hasattr(raw, "value") else int(raw)
                    name = INPUT_SOURCES.get(val, f"Desconocido ({val})")
                    input_text = f"Entrada actual:  {name}"
                except Exception:
                    input_text = "Entrada: no se pudo leer"

                status = "DDC/CI activo"
        except Exception as e:
            status = f"Sin respuesta DDC/CI ({e})"
            self.available = False

        self.after(0, lambda: self._update_ui(status, brightness_text, input_text))

    def _update_ui(self, status, brightness, input_src):
        color = "green" if self.available else "gray"
        self.lbl_status.config(text=status, foreground=color)
        self.lbl_brightness.config(text=brightness)
        self.lbl_input.config(text=input_src)

    def set_input(self, source_val):
        if not self.available:
            messagebox.showwarning("No disponible", "Este monitor no responde a DDC/CI.")
            return
        name = INPUT_SOURCES.get(source_val, str(source_val))
        threading.Thread(target=self._do_set_input, args=(source_val, name), daemon=True).start()

    def _do_set_input(self, source_val, name):
        try:
            with self.monitor:
                self.monitor.set_input_source(source_val)
            self.after(0, lambda: self.lbl_input.config(text=f"Entrada actual:  {name}"))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Error", f"No se pudo cambiar a {name}:\n{e}"))


class ScreenControlApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Screen Control")
        self.resizable(False, False)
        self.configure(bg="#f0f0f0")

        # Icono de la ventana
        icon_path = os.path.join(APP_DIR, "icon.ico")
        if IS_WINDOWS and os.path.exists(icon_path):
            self.iconbitmap(icon_path)

        self._tray = None
        self._brightness_popup = None
        self.protocol("WM_DELETE_WINDOW", self.minimize_to_tray)

        # Header
        header = ttk.Frame(self)
        header.pack(fill="x", padx=16, pady=(12, 4))

        ttk.Label(header, text="Screen Control", font=("Segoe UI", 16, "bold")).pack(side="left")
        self.btn_refresh = ttk.Button(header, text="Actualizar", command=self.refresh)
        self.btn_refresh.pack(side="right")
        ttk.Label(header, text="Cambio de entrada via DDC/CI", font=("Segoe UI", 9), foreground="gray").pack(
            side="left", padx=(10, 0)
        )

        # Container para monitores
        self.container = ttk.Frame(self)
        self.container.pack(fill="both", expand=True, padx=16, pady=(4, 16))

        self.cards = []
        self.load_monitors()
        self.center_window()

    def center_window(self):
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"+{x}+{y}")

    def load_monitors(self):
        for card in self.cards:
            card.destroy()
        self.cards.clear()

        try:
            monitors = get_monitors()
        except Exception as e:
            ttk.Label(self.container, text=f"Error: {e}").pack(pady=20)
            return

        if not monitors:
            ttk.Label(
                self.container,
                text="No se detectaron monitores con DDC/CI.\nVerifica que DDC/CI este habilitado en el menu OSD.",
                font=("Segoe UI", 10),
                justify="center",
            ).pack(pady=20)
            return

        available = get_available_inputs()

        for i, mon in enumerate(monitors):
            inputs = available.get(i, [])
            card = MonitorCard(self.container, i, mon, available_inputs=inputs, padding=4)
            card.pack(fill="x", pady=4)
            self.cards.append(card)

    def refresh(self):
        self.load_monitors()

    def minimize_to_tray(self):
        self.withdraw()
        if self._tray is None:
            if IS_WINDOWS:
                self._tray = TrayWindows(self)
            else:
                self._tray = TrayMac(self)
            self._tray.start()

    def restore_window(self):
        # Cerrar popup de brillo si esta abierto
        if self._brightness_popup and self._brightness_popup.winfo_exists():
            self._brightness_popup.destroy()
            self._brightness_popup = None
        self.deiconify()
        self.lift()
        self.focus_force()

    def show_brightness_popup(self):
        # Si ya hay uno abierto, cerrarlo
        if self._brightness_popup and self._brightness_popup.winfo_exists():
            self._brightness_popup.destroy()
            self._brightness_popup = None
            return
        self._brightness_popup = BrightnessPopup(self)


if __name__ == "__main__":
    app = ScreenControlApp()
    app.mainloop()
