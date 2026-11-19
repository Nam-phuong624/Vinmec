"""Cửa sổ RPA: nạp danh sách bung gói của ngày hôm nay và tự điền vào OHDemo.exe ở luồng nền.

Mỗi dòng: tìm theo họ tên → có (trùng năm sinh) thì cập nhật theo Excel, chưa có thì tạo PID mới rồi bổ sung thông tin.
"""
import queue
import threading
import time
import tkinter as tk
from datetime import date
from tkinter import messagebox, ttk
from shared.excel import ERROR_FILE, day_folder, find_daily_file, read_daily, write_errors
from shared.identity import ReviewRequired
from rpa_tool.contracts import audit
from rpa_tool import audit_trail, hau_kiem, journal
from rpa_tool.runner import run_rows
from shared import paths

STATUS = 'Trạng thái RPA'
MANUAL = 'Cần điền tay'


class ReceptionApp:
    def __init__(self, root, auto_run=True):
        self.root = root
        self.auto_run = auto_run
        self.commands, self.events = queue.Queue(), queue.Queue()
        self.stop = threading.Event()
        self.shutdown = threading.Event()
        self.header, self.rows, self.path = [], [], None
        self.running = False
        self.ready = False
        self.root.title('RPA · Tiếp đón khám sức khỏe — DEMO')
        self.root.geometry('1180x640')
        self.root.minsize(760, 420)
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TFrame', background='#f4f7f8')
        style.configure('TLabel', background='#f4f7f8', foreground='#243947', font=('Segoe UI', 10))
        style.configure('Title.TLabel', font=('Segoe UI', 19, 'bold'), foreground='#176b78')
        style.configure('TButton', font=('Segoe UI', 10), padding=7)
        body = ttk.Frame(root, padding=16)
        body.pack(fill='both', expand=True)
        ttk.Label(body, text='RPA · Danh sách bung gói trong ngày', style='Title.TLabel').pack(anchor='w')
        ttk.Label(body, text='MÔ PHỎNG · DỮ LIỆU GIẢ', foreground='#956615').pack(anchor='w', pady=(2, 10))

        self.source = tk.StringVar(value='Chưa nạp danh sách.')
        ttk.Label(body, textvariable=self.source, wraplength=1100, justify='left').pack(fill='x')
        row = ttk.Frame(body)
        row.pack(fill='x', pady=8)
        self.reload_button = ttk.Button(row, text='Nạp lại danh sách', command=self.load)
        self.reload_button.pack(side='left')
        self.run_button = ttk.Button(row, text='Chạy RPA', command=self.start_run, state='disabled')
        self.run_button.pack(side='left', padx=6)
        self.stop_button = ttk.Button(row, text='Dừng', command=self.cancel, state='disabled')
        self.stop_button.pack(side='left')
        self.audit_button = ttk.Button(row, text='Đối soát (chỉ đọc)', command=self.start_audit, state='disabled')
        self.audit_button.pack(side='left', padx=(18, 6))
        self.restore_button = ttk.Button(row, text='Khôi phục lượt chạy…', command=self.start_restore, state='disabled')
        self.restore_button.pack(side='left')

        self.status = tk.StringVar(value='Đang chờ OHDemo.exe… (hãy mở OHDemo.exe)')
        ttk.Label(body, textvariable=self.status, wraplength=1100, foreground='#176b78', justify='left').pack(fill='x', pady=(0, 8))

        frame = ttk.Frame(body)
        frame.pack(fill='both', expand=True)
        self.tree = ttk.Treeview(frame, show='headings', selectmode='browse')
        ys = ttk.Scrollbar(frame, orient='vertical', command=self.tree.yview)
        xs = ttk.Scrollbar(frame, orient='horizontal', command=self.tree.xview)
        self.tree.configure(yscrollcommand=ys.set, xscrollcommand=xs.set)
        ys.pack(side='right', fill='y')
        xs.pack(side='bottom', fill='x')
        self.tree.pack(side='left', fill='both', expand=True)

        self.root.protocol('WM_DELETE_WINDOW', self.close)
        self.worker_thread = threading.Thread(target=self.worker, daemon=True)
        self.worker_thread.start()
        self.load()
        self.root.after(100, self.poll)

    # ---- danh sách -------------------------------------------------------------------------
    def load(self):
        if self.running:
            return
        self.tree.delete(*self.tree.get_children())
        self.header, self.rows, self.path = [], [], None
        try:
            self.path = find_daily_file()
            self.header, self.rows = read_daily(self.path)
        except (ReviewRequired, OSError, KeyError) as exc:
            self.source.set(f'Không nạp được danh sách ngày {date.today():%d-%m-%Y}: {exc}')
            self.run_button.configure(state='disabled')
            return
        columns = [STATUS] + self.header
        self.tree.configure(columns=columns)
        for name in columns:
            self.tree.heading(name, text=name)
            self.tree.column(name, width=240 if name == STATUS else max(90, min(260, len(name) * 9 + 20)), stretch=False)
        for index, record in enumerate(self.rows):
            record['iid'] = str(index)
            self.tree.insert('', 'end', iid=record['iid'], values=['Chờ'] + record['cells'])
        interrupted = journal.unfinished(paths.RUNTIME, self.path.name)
        for record in self.rows:
            if record['line'] in interrupted:
                self.tree.set(record['iid'], STATUS, 'Lỗi · Lần chạy trước bị ngắt giữa chừng ở dòng này; có thể đã tạo hồ sơ dở trên OH. RPA sẽ chạy lại để hoàn tất.')
        self.source.set(f'Ngày {day_folder().name} · {self.path.name} · {len(self.rows)} dòng, {len(self.header)} cột')
        self.status.set('Đã nạp danh sách.' + (' RPA sẽ tự chạy khi OH sẵn sàng.' if self.auto_run and not self.ready else ''))
        self.controls()
        if self.auto_run and self.ready:
            self.start_run()

    def set_status(self, row, text):
        self.tree.set(row['iid'], STATUS, text)
        self.tree.see(row['iid'])

    def controls(self):
        can_run = bool(self.rows) and self.ready and not self.running
        self.run_button.configure(state='normal' if can_run else 'disabled')
        self.reload_button.configure(state='disabled' if self.running else 'normal')
        self.stop_button.configure(state='normal' if self.running else 'disabled')
        post = bool(self.rows) and self.ready and not self.running and self.path is not None
        self.audit_button.configure(state='normal' if post else 'disabled')
        self.restore_button.configure(state='normal' if post else 'disabled')

    # ---- chạy RPA --------------------------------------------------------------------------
    def start_run(self):
        todo = [r for r in self.rows if self.tree.set(r['iid'], STATUS) in ('Chờ', '') or
                self.tree.set(r['iid'], STATUS).startswith(('Lỗi', 'Đã dừng'))]
        if self.running or not self.ready or not todo:
            return
        self.stop.clear()
        self.running = True
        self.status.set(f'RPA đang chạy nền ({len(todo)} dòng). Bạn vẫn dùng máy bình thường.')
        for r in todo:
            self.set_status(r, 'Chờ')
        todo_ids = {r['iid'] for r in todo}
        prior = [(r, self.tree.set(r['iid'], STATUS).split(' · ', 1)[-1]) for r in self.rows
                 if r['iid'] not in todo_ids and self.tree.set(r['iid'], STATUS).startswith(MANUAL)]
        self.commands.put(('run', [(r['iid'], r['line'], r['values'], r) for r in todo], prior))

        self.controls()

    def start_audit(self):
        """Chỉ đọc: mở lại từng hồ sơ RPA đã xử lý và so với Excel; kết quả ở bao_cao_doi_soat.xlsx. Không ghi gì vào OH."""
        if self.running or not self.ready:
            return
        self.stop.clear()
        self.running = True
        self.status.set('Đang đối soát (chỉ đọc)…')
        self.commands.put(('audit', list(self.rows), None))
        self.controls()

    def start_restore(self):
        entries = [e for e in audit_trail.read_entries(self.path.parent, self.path.name)]
        updated = {e['pid'] for e in entries if e['action'] == 'cập nhật'}
        created = [e for e in entries if e['action'] == 'tạo']
        if not updated and not created:
            messagebox.showinfo('Khôi phục', 'Chưa có nhật ký thay đổi nào của file này để khôi phục.')
            return
        if not messagebox.askyesno('Khôi phục lượt chạy', f'Khôi phục {len(updated)} hồ sơ đã CẬP NHẬT về giá trị trước lượt chạy?\n\n'
                                   'Hồ sơ nào đã bị ai sửa tiếp sau đó sẽ được bỏ qua.\n'
                                   f'{len(created)} hồ sơ TẠO MỚI không xóa được bằng RPA; sẽ chỉ được liệt kê trong bao_cao_khoi_phuc.xlsx.'):
            return
        self.stop.clear()
        self.running = True
        self.status.set('Đang khôi phục…')
        self.commands.put(('restore', None, None))
        self.controls()

    def cancel(self):
        self.stop.set()
        self.status.set('Đang dừng sau dòng hiện tại…')

    def worker(self):
        import pythoncom
        pythoncom.CoInitializeEx(0)
        try:
            from rpa_tool.ohdemo_engine import OhDemoRPA, NeedManual, find_window
            engine = None
            while engine is None and not self.shutdown.is_set():      # chờ người dùng mở OHDemo.exe
                try:
                    engine = OhDemoRPA()
                except ReviewRequired:
                    time.sleep(1.5)
            if engine is None:
                return
            self.events.put(('ready', None))
            while not self.shutdown.is_set():
                try:
                    action, data, prior = self.commands.get(timeout=.35)
                except queue.Empty:
                    continue
                if action in ('audit', 'restore'):
                    try:
                        if find_window() != engine.handle:
                            engine = OhDemoRPA()
                        note = lambda text: self.events.put(('info', text))
                        if action == 'audit':
                            results, bad = hau_kiem.doi_soat(engine, self.path.parent, self.path.name, data, note, self.stop)
                            self.events.put(('info', f'Đối soát xong: {len(results) - bad} dòng khớp/bỏ qua, {bad} bất thường. Chi tiết ở {hau_kiem.AUDIT_REPORT}.'))
                        else:
                            results, done = hau_kiem.khoi_phuc(engine, self.path.parent, self.path.name, note, self.stop)
                            self.events.put(('info', f'Khôi phục xong: {done} hồ sơ đã khôi phục. Chi tiết ở {hau_kiem.RESTORE_REPORT}.'))
                    except Exception as exc:
                        self.events.put(('info', 'Không thực hiện được: ' + str(exc)[:200]))
                    self.events.put(('task_end', None))
                    continue
                if action != 'run':
                    continue
                try:
                    if find_window() != engine.handle:                # OHDemo đã được mở lại
                        engine = OhDemoRPA()
                except Exception:
                    pass
                counts = run_rows(engine, data, self.stop, lambda iid, text: self.events.put(('row', (iid, text))),
                                  self.path.parent, self.header, prior, self.path.name)
                self.events.put(('done', counts))
        except Exception as exc:
            self.events.put(('fatal', 'Không điều khiển được OHDemo.exe: ' + str(exc)))
        finally:
            pythoncom.CoUninitialize()

    def save_errors(self):
        """Ghi các dòng Lỗi / Cần điền tay vào 'ds lỗi.xlsx' trong thư mục ngày để điền thủ công."""
        items = []
        for r in self.rows:
            text = self.tree.set(r['iid'], STATUS)
            if text.startswith(('Lỗi', MANUAL)):
                items.append((r, text.split(' · ', 1)[1] if ' · ' in text else text))
        try:
            path = write_errors(self.path.parent, self.header, items)
        except OSError as exc:
            return f' Không ghi được {ERROR_FILE} (đang mở trong Excel?): {exc}'
        return f' Đã ghi {len(items)} dòng vào {path.name} để điền thủ công.' if path else ''
    def poll(self):
        try:
            while True:
                event, data = self.events.get_nowait()
                if event == 'ready':
                    self.ready = True
                    self.status.set('Đã nối với OHDemo.exe.' + (' RPA tự chạy…' if self.auto_run else ' Bấm Chạy RPA.'))
                    self.controls()
                    if self.auto_run:
                        self.start_run()
                elif event == 'row':
                    iid, text = data
                    self.tree.set(iid, STATUS, text)
                    self.tree.see(iid)
                elif event == 'done':
                    self.running = False
                    note = self.save_errors()
                    self.status.set(f"Xong · tạo mới {data['created']} · cập nhật {data['updated']} · không đổi {data['same']} · cần điền tay {data['manual']} · lỗi {data['error']}."
                                    + (' (đã dừng)' if self.stop.is_set() else '') + note)
                    self.controls()
                elif event == 'info':
                    self.status.set(data)
                elif event == 'task_end':
                    self.running = False
                    self.controls()
                elif event == 'fatal':
                    self.running = False
                    self.status.set('CẦN KIỂM TRA · ' + data)
                    self.controls()
        except queue.Empty:
            pass
        if not self.shutdown.is_set():
            self.root.after(100, self.poll)

    def close(self):
        self.stop.set()
        self.shutdown.set()
        self.root.destroy()


if __name__ == '__main__':
    window = tk.Tk()
    ReceptionApp(window)
    window.mainloop()
