"""Single entry point: native WinForms OH plus RPA desktop window. No server."""
from pathlib import Path
import sys
import site
import subprocess

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
if sys.prefix == sys.base_prefix and (ROOT/'.deps').is_dir():
    site.addsitedir(str(ROOT/'.deps'))


def main():
    # pywinauto also enables per-monitor awareness. Set it before Tk creates
    # any HWND so the worker cannot change scaling after the UI is laid out.
    import ctypes
    try:ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except AttributeError:ctypes.windll.user32.SetProcessDPIAware()
    import tkinter as tk
    from oh_desktop.store import initialize
    from oh_desktop.launcher import launch
    from rpa_tool.app import ReceptionApp
    if not (ROOT/'demo'/'patients.json').exists():
        from scripts.generate_demo import main as generate
        generate()
    initialize()
    process = launch()
    window = tk.Tk()
    app = ReceptionApp(window, process_id=process.pid)
    try:
        window.mainloop()
    finally:
        app.stop.set(); app.shutdown.set()
        app.worker_thread.join(timeout=7)
        if process.poll() is None:
            import ctypes
            from ctypes import wintypes
            callback=ctypes.WINFUNCTYPE(wintypes.BOOL,wintypes.HWND,wintypes.LPARAM)
            def close_owned(hwnd,_):
                pid=wintypes.DWORD()
                ctypes.windll.user32.GetWindowThreadProcessId(hwnd,ctypes.byref(pid))
                if pid.value==process.pid:ctypes.windll.user32.PostMessageW(hwnd,0x0010,0,0)
                return True
            ctypes.windll.user32.EnumWindows(callback(close_owned),0)
            try:process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.terminate();process.wait(timeout=3)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
