"""Mở công cụ RPA. OHDemo.exe phải được mở riêng; RPA tự nối vào cửa sổ OHDemo và chạy nền."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    import ctypes
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except (AttributeError, OSError):
        ctypes.windll.user32.SetProcessDPIAware()
    import tkinter as tk
    from rpa_tool.app import ReceptionApp
    window = tk.Tk()
    app = ReceptionApp(window)
    try:
        window.mainloop()
    finally:
        app.stop.set()
        app.shutdown.set()
        app.worker_thread.join(timeout=7)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
