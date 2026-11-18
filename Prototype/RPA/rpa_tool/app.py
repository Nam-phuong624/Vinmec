"""Two desktop windows: Tkinter UI on main thread; Windows UIA on worker."""
import json
import queue
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from shared.excel import MAPPING, sheets, read_roster, read_preparation, export_prepared
from shared.identity import parse_scan
from shared.paths import DEMO, RUNTIME
import hashlib


class ReceptionApp:
    def __init__(self, root, process_id=None):
        self.root = root
        self.process_id = process_id
        self.commands, self.events = queue.Queue(), queue.Queue()
        self.stop = threading.Event()
        self.shutdown = threading.Event()
        self.rows, self.proposal, self.pending = [], None, None
        self.mapping = dict(MAPPING)
        self._phase_states = {}
        self._active_phase = None
        self._restoring_phase = False
        self.busy = False
        self.root.title('RPA · Tiếp đón khám sức khỏe — DEMO')
        height = min(940, self.root.winfo_screenheight()-100)
        self.root.geometry(f'600x{height}')
        self.root.minsize(560, min(700,height))
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TFrame', background='#f4f7f8')
        style.configure('TLabel', background='#f4f7f8', foreground='#243947', font=('Segoe UI', 10))
        style.configure('Title.TLabel', font=('Segoe UI', 19, 'bold'), foreground='#176b78')
        style.configure('TButton', font=('Segoe UI', 10), padding=7)
        canvas = tk.Canvas(root, background='#f4f7f8', highlightthickness=0)
        scrollbar = ttk.Scrollbar(root, orient='vertical', command=canvas.yview)
        scrollbar.pack(side='right', fill='y')
        canvas.pack(side='left', fill='both', expand=True)
        canvas.configure(yscrollcommand=scrollbar.set)
        body = ttk.Frame(canvas, padding=20)
        content = canvas.create_window((0,0), window=body, anchor='nw')
        body.bind('<Configure>', lambda _: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.bind('<Configure>', lambda event: canvas.itemconfigure(content, width=event.width))
        root.bind('<MouseWheel>', lambda event: canvas.yview_scroll(-int(event.delta/120), 'units'))
        self.canvas = canvas
        self.workflow_title=tk.StringVar(value='RPA · Chuẩn bị trước khám')
        ttk.Label(body, textvariable=self.workflow_title, style='Title.TLabel').pack(anchor='w')
        ttk.Label(body, text='MÔ PHỎNG · DỮ LIỆU GIẢ', foreground='#956615').pack(anchor='w', pady=(4, 16))
        self.phase = tk.StringVar(value='1. Chuẩn bị — tạo PID / bung gói')
        self.phase_box=ttk.Combobox(body,textvariable=self.phase,state='readonly',
            values=['1. Chuẩn bị — tạo PID / bung gói','2. Khách đến — tiếp đón'])
        self.phase_box.pack(fill='x',pady=(0,12))
        self.file = tk.StringVar(value=str(DEMO / 'new_customers_A.xlsx'))
        self.sheet = tk.StringVar(value='DS_bung_DEMO')
        self.company = tk.StringVar(value='Công ty Demo A')
        self.batch = tk.StringVar(value='DEMO-2026')
        self.header = tk.StringVar(value='2')
        self.mode = tk.StringVar(value='demo')
        self.confirmed = tk.BooleanVar(value=False)
        self.status = tk.StringVar(value='Đang kết nối OH Desktop…')
        self.info = tk.StringVar(value='Chưa đối chiếu hồ sơ.')
        self.inputs = []

        main_body=body
        self.data_frame=ttk.Frame(main_body)
        self.data_frame.pack(fill='x')
        body=self.data_frame
        self.entry(body, 'Danh sách Excel (CCCD bắt buộc)', self.file)
        actions = ttk.Frame(body); actions.pack(fill='x', pady=5)
        self.choose = ttk.Button(actions, text='Chọn file', command=self.choose_file); self.choose.pack(side='left')
        ttk.Label(actions, text='  Sheet').pack(side='left')
        self.sheet_box = ttk.Combobox(actions, textvariable=self.sheet, width=24, state='readonly'); self.sheet_box.pack(side='left', padx=6)
        self.entry(body, 'Công ty', self.company)
        pair = ttk.Frame(body); pair.pack(fill='x', pady=3)
        ttk.Label(pair, text='Đợt khám').pack(side='left')
        self.batch_entry = ttk.Entry(pair, textvariable=self.batch, width=22); self.batch_entry.pack(side='left', padx=8)
        ttk.Label(pair, text='Hàng tiêu đề').pack(side='left')
        self.header_entry = ttk.Entry(pair, textvariable=self.header, width=4); self.header_entry.pack(side='left', padx=8)
        load_row = ttk.Frame(body); load_row.pack(fill='x', pady=8)
        self.load_button = ttk.Button(load_row, text='Nạp danh sách', command=self.load); self.load_button.pack(side='left', fill='x', expand=True)
        self.mapping_button = ttk.Button(load_row, text='Ánh xạ cột', command=self.choose_mapping); self.mapping_button.pack(side='left', padx=(6,0))
        self.reception_context=ttk.Frame(main_body)
        self.roster_summary=tk.StringVar(value='Chưa nạp danh sách tiếp đón.')
        ttk.Label(self.reception_context,text='Đoàn đang tiếp đón',font=('Segoe UI',11,'bold')).pack(anchor='w')
        ttk.Label(self.reception_context,textvariable=self.roster_summary,wraplength=520).pack(fill='x',pady=6)
        self.change_roster=ttk.Button(self.reception_context,text='Đổi đoàn / chọn danh sách',command=self.toggle_roster_editor)
        self.change_roster.pack(anchor='w',pady=(0,8))
        self.prep_frame=ttk.Frame(main_body);self.prep_frame.pack(fill='x')
        ttk.Separator(self.prep_frame).pack(fill='x',pady=8)
        ttk.Label(self.prep_frame,text='Lần 1 · Khách mới chưa có PID').pack(anchor='w')
        self.customer_box=ttk.Combobox(self.prep_frame,state='readonly');self.customer_box.pack(fill='x',pady=8)
        self.customer_box.bind('<<ComboboxSelected>>',lambda _:self.controls())
        self.create_button=ttk.Button(self.prep_frame,text='Điền hồ sơ & gói khám vào OH',command=self.create_patient,state='disabled')
        self.create_button.pack(fill='x',pady=6)
        self.created_info=tk.StringVar(value='OH sẽ cấp PID sau khi nhân viên kiểm tra và lưu. Không tự sinh PID trong RPA.')
        ttk.Label(self.prep_frame,textvariable=self.created_info,wraplength=520).pack(fill='x',pady=10)
        self.handoff_button=ttk.Button(self.prep_frame,text='Dùng danh sách đã có PID cho lần 2',command=self.use_handoff)
        self.handoff_button.pack(fill='x',pady=6)
        ttk.Label(self.prep_frame,text='Sau khi điền, kiểm tra hộp Tạo hồ sơ trên OH rồi bấm “Lưu và cấp PID”.\nDanh sách kết quả được xuất riêng, giữ nguyên Excel đầu vào.',wraplength=520).pack(fill='x',pady=8)
        self.reception_frame=ttk.Frame(main_body);self.reception_frame.pack(fill='x')
        body=self.reception_frame
        ttk.Separator(body).pack(fill='x', pady=8)
        ttk.Label(body, text='Lần 2 · Quét CCCD (Enter để đối chiếu)').pack(anchor='w')
        self.scan = tk.StringVar()
        self.scan_entry = ttk.Entry(body, textvariable=self.scan); self.scan_entry.pack(fill='x', pady=5)
        self.scan_entry.bind('<Return>', lambda _: self.prepare())
        row = ttk.Frame(body); row.pack(fill='x')
        self.mode_box = ttk.Combobox(row, textvariable=self.mode, values=['demo', 'qr-pipe'], state='readonly', width=12)
        self.mode_box.pack(side='left')
        self.sample_button = ttk.Button(row, text='CCCD demo theo PID', command=self.demo_scan); self.sample_button.pack(side='left', padx=6)
        self.prepare_button = ttk.Button(row, text='Đối chiếu', command=self.prepare); self.prepare_button.pack(side='right')
        ttk.Label(body, textvariable=self.info, wraplength=540, justify='left').pack(fill='x', pady=12)
        ttk.Separator(body).pack(fill='x', pady=8)
        ttk.Label(body, text='Địa chỉ hiện tại đã hỏi khách').pack(anchor='w')
        self.address = {k: tk.StringVar() for k in ('province','ward','street')}
        for key, label in [('province','Tỉnh / Thành phố'),('ward','Phường / Xã'),('street','Số nhà / Đường / Thôn')]:
            self.entry(body, label, self.address[key])
            self.address[key].trace_add('write', lambda *_: self.confirmed.set(False))
        self.checkbox = ttk.Checkbutton(body, text='Đã xác nhận địa chỉ với khách', variable=self.confirmed, command=self.controls)
        self.checkbox.pack(anchor='w', pady=9)
        row = ttk.Frame(body); row.pack(fill='x')
        self.fill_button = ttk.Button(row, text='Điền vào OH', command=self.fill, state='disabled'); self.fill_button.pack(side='left', expand=True, fill='x')
        self.stop_button = ttk.Button(row, text='Dừng', command=self.cancel); self.stop_button.pack(side='left', padx=7)
        self.clear_button = ttk.Button(row, text='Lượt mới', command=self.clear); self.clear_button.pack(side='left')
        ttk.Label(body, text='Sau khi điền: kiểm tra và bấm “Lưu hồ sơ” trên cửa sổ OH.', wraplength=540).pack(anchor='w')
        self.status_label=ttk.Label(main_body,textvariable=self.status,wraplength=520,foreground='#176b78',justify='left')
        self.status_label.pack(fill='x',pady=15)
        self.prep_stop=ttk.Button(main_body,text='Dừng / hủy theo dõi lượt hiện tại',command=self.cancel)
        self.prep_stop.pack(fill='x',pady=5)
        for var in (self.file,self.sheet,self.company,self.batch,self.header):
            var.trace_add('write', self.invalidate_roster)
        self.mode.trace_add('write', self.invalidate_proposal)
        self.scan.trace_add('write', self.invalidate_proposal)
        self.confirmed.trace_add('write', lambda *_: self.controls())
        self.phase.trace_add('write',self.phase_changed)
        self.phase_changed()
        self.root.protocol('WM_DELETE_WINDOW', self.close)
        self.worker_thread = threading.Thread(target=self.worker, daemon=True)
        self.worker_thread.start()
        self.root.after(100, self.poll)

    def entry(self, body, label, variable):
        ttk.Label(body, text=label).pack(anchor='w', pady=(5, 2))
        widget = ttk.Entry(body, textvariable=variable)
        widget.pack(fill='x', pady=(0,3)); self.inputs.append(widget)
        return widget

    def invalidate_proposal(self, *_):
        self.proposal = None
        self.confirmed.set(False)
        self.controls()

    def invalidate_roster(self, *_):
        if self._restoring_phase:return
        self.rows = []
        self.invalidate_proposal()
        self.update_roster_summary()

    def update_roster_summary(self):
        state=f'Đã nạp {len(self.rows)} khách' if self.rows else 'Chưa nạp danh sách'
        self.roster_summary.set(f'{self.company.get()} · {self.batch.get()}\n{state}')

    def controls(self):
        valid = self.proposal is not None and self.confirmed.get() and not self.busy and not self.pending
        self.fill_button.configure(state='normal' if valid else 'disabled')
        blocked=bool(self.busy or self.pending)
        index=self.customer_box.current()
        eligible=0<=index<len(self.rows) and not self.rows[index].get('pid') and not self.rows[index].get('blocked')
        self.create_button.configure(state='normal' if eligible and not blocked and self.phase.get().startswith('1.') else 'disabled')
        self.phase_box.configure(state='disabled' if blocked else 'readonly')
        self.customer_box.configure(state='disabled' if blocked else 'readonly')
        self.handoff_button.configure(state='disabled' if blocked else 'normal')
        self.change_roster.configure(state='disabled' if blocked else 'normal')
        for widget in self.inputs+[self.choose,self.load_button,self.mapping_button,self.scan_entry,self.sample_button,
                self.prepare_button,self.checkbox,self.batch_entry,self.header_entry]:
            widget.configure(state='disabled' if blocked else 'normal')
        for widget in (self.sheet_box,self.mode_box):widget.configure(state='disabled' if blocked else 'readonly')

    def phase_changed(self,*_):
        preparing=self.phase.get().startswith('1.')
        self.workflow_title.set('RPA · Chuẩn bị trước khám' if preparing else 'RPA · Tiếp đón khách đến')
        key='1' if preparing else '2'
        if self._active_phase and key!=self._active_phase:
            self._phase_states[self._active_phase]=dict(file=self.file.get(),sheet=self.sheet.get(),header=self.header.get(),
                context=(self.company.get(),self.batch.get()),mapping=dict(self.mapping),rows=list(self.rows),
                selected=self.customer_box.current())
        context=(self.company.get(),self.batch.get())
        target=self._phase_states.get(key)
        if target and target['context']!=context:target=None
        generated=self.handoff_path()
        use_generated=not preparing and not target and generated.exists()
        self._restoring_phase=True
        try:
            self.mapping=dict(target['mapping']) if target else dict(MAPPING)
            self.file.set(target['file'] if target else str(generated if use_generated else DEMO/('new_customers_A.xlsx' if preparing else 'company_A.xlsx')))
            self.sheet.set(target['sheet'] if target else 'DS_bung_DEMO')
            self.header.set(target['header'] if target else '2')
            self.rows=list(target['rows']) if target else []
        finally:self._restoring_phase=False
        self._active_phase=key
        self.invalidate_proposal();self.scan.set('');self.info.set('Chưa đối chiếu hồ sơ.')
        for frame in (self.data_frame,self.prep_frame,self.reception_context,self.reception_frame):frame.pack_forget()
        self.prep_stop.pack_forget()
        if preparing:
            self.data_frame.pack(fill='x',before=self.status_label)
            self.prep_frame.pack(fill='x',before=self.status_label)
            self.prep_stop.pack(fill='x',pady=5,after=self.status_label)
        else:
            self.reception_context.pack(fill='x',before=self.status_label)
            self.reception_frame.pack(fill='x',before=self.status_label)
        self.refresh_customers(target.get('selected',0) if target else 0)
        self.update_roster_summary();self.controls()
        self.canvas.yview_moveto(0)
        if use_generated:self.load()
        elif not preparing:
            self.status.set('Sẵn sàng quét CCCD. Không cần nạp Excel lại cho từng khách.' if self.rows else
                            'Chưa có danh sách tiếp đón. Hoàn thành lần 1 hoặc chọn Đổi đoàn / chọn danh sách để nạp một lần đầu buổi.')
        else:self.status.set('Lần 1: nạp Excel khách mới chưa PID.' if not self.rows else 'Lần 1: chọn khách để tạo hồ sơ và gói khám.')

    def refresh_customers(self,selected=0):
        self.customer_box.configure(values=[f"Dòng {r['line']} · {r['name']} · {r.get('pid') or 'Chưa PID'} · {r.get('package_code','')}" for r in self.rows])
        if self.rows:self.customer_box.current(selected if 0<=selected<len(self.rows) else 0)
        else:self.customer_box.set('')

    def toggle_roster_editor(self):
        if self.busy or self.pending:return
        if self.data_frame.winfo_manager():self.data_frame.pack_forget()
        else:self.data_frame.pack(fill='x',before=self.reception_frame)

    def handoff_path(self):
        context=self.company.get().strip()+'|'+self.batch.get().strip()
        return RUNTIME/'prepared'/(hashlib.sha256(context.encode()).hexdigest()[:16]+'.xlsx')

    def use_handoff(self):
        path=self.handoff_path()
        if not path.exists():return self.status.set('Chưa có danh sách PID đã xác minh cho công ty/đợt này. Hoàn thành lần 1 trước.')
        self.phase.set('2. Khách đến — tiếp đón')
        self.mapping=dict(MAPPING)
        if self.file.get()!=str(path) or not self.rows:
            self.file.set(str(path));self.sheet.set('DS_bung_DEMO');self.header.set('2');self.load()

    def create_patient(self):
        if self.busy or self.pending or not self.rows:return
        index=self.customer_box.current()
        if index<0:return self.status.set('Chọn một khách trong danh sách Excel.')
        self.stop.clear();self.commands.put(('create',dict(self.rows[index])))
        self.set_busy(True);self.status.set('Lần 1: đang điền hồ sơ và gói khám vào OH…')

    def set_busy(self, value):
        self.busy = value
        for widget in self.inputs + [self.choose, self.load_button, self.mapping_button, self.scan_entry, self.sample_button,
                self.prepare_button, self.checkbox, self.clear_button, self.batch_entry, self.header_entry]:
            widget.configure(state='disabled' if value else 'normal')
        for widget in (self.sheet_box,self.mode_box):
            widget.configure(state='disabled' if value else 'readonly')
        self.controls()

    def choose_file(self):
        path = filedialog.askopenfilename(filetypes=[('Excel', '*.xlsx *.xlsm')])
        if not path: return
        try:
            self.file.set(path)
            names = sheets(path); self.sheet_box.configure(values=names)
            self.sheet.set('')  # Explicit sheet selection, no implicit first sheet.
            self.status.set('Chọn sheet chính xác rồi nạp danh sách.')
        except Exception as exc:
            self.status.set(f'Không đọc được file: {exc}')

    def load(self):
        self.invalidate_roster()
        try:
            reader=read_preparation if self.phase.get().startswith('1.') else read_roster
            self.rows, errors = reader(self.file.get(), self.sheet.get(), self.company.get(), self.batch.get(), int(self.header.get()), self.mapping)
            self.refresh_customers()
            preparing=self.phase.get().startswith('1.')
            self.status.set(f'Đã nạp {len(self.rows)} dòng. {len(errors)} cảnh báo. '+('Chọn khách mới và điền hồ sơ/gói khám.' if preparing else 'Sẵn sàng quét CCCD; danh sách dùng cho cả buổi.'))
            if not preparing:self.data_frame.pack_forget()
            self.update_roster_summary()
            self.controls()
            if errors: messagebox.showwarning('Kiểm tra Excel', '\n'.join(errors[:20]))
        except Exception as exc:
            self.status.set(str(exc))

    def choose_mapping(self):
        path = filedialog.askopenfilename(filetypes=[('Ánh xạ JSON', '*.json')])
        if not path: return
        try:
            mapping = json.loads(Path(path).read_text(encoding='utf-8'))
            if not isinstance(mapping, dict) or set(mapping) != set(MAPPING) or any(
                    not isinstance(v,str) or not v.strip() for v in mapping.values()):
                raise ValueError('JSON phải có đủ khóa như config/column-mapping.json.')
            self.mapping = mapping
            self.invalidate_roster()
            self.status.set('Đã đổi ánh xạ cột. Nạp lại danh sách để áp dụng.')
        except Exception as exc:
            self.status.set('Không đọc được ánh xạ: '+str(exc))

    def demo_scan(self):
        self.commands.put(('demo', None)); self.set_busy(True)

    def prepare(self):
        if self.busy or self.pending: return
        self.stop.clear()
        self.invalidate_proposal()
        if not self.rows: return self.status.set('Nạp danh sách Excel hợp lệ trước; CCCD bắt buộc ở mọi dòng.')
        try:
            identity = parse_scan(self.scan.get(), self.mode.get())
            self.commands.put(('prepare', (identity, list(self.rows), self.company.get(), self.batch.get())))
            self.set_busy(True); self.status.set('Đang đối chiếu CCCD, Excel và PID trên OH…')
        except Exception as exc:
            self.status.set(str(exc))

    def fill(self):
        if not self.proposal or self.busy: return
        self.stop.clear()
        self.commands.put(('fill', (self.proposal, {k:v.get() for k,v in self.address.items()}, self.confirmed.get())))
        self.set_busy(True); self.status.set('Đang điền vào OH. Có thể nhấn Dừng.')

    def cancel(self):
        self.stop.set()
        self.proposal = None
        self.pending = None
        self.commands.put(('cancel_pending', None))
        self.confirmed.set(False); self.controls()
        self.status.set('Đã yêu cầu dừng. Kiểm tra OH; dữ liệu điền một phần chưa tự lưu.')

    def clear(self):
        self.cancel(); self.scan.set(''); self.info.set('Chưa đối chiếu hồ sơ.')
        self.status.set('Lượt mới: mở đúng PID trên OH rồi quét CCCD.')

    def worker(self):
        pending = None
        import pythoncom
        pythoncom.CoInitializeEx(0)
        try:
            from rpa_tool.desktop_engine import DesktopRPA
            if self.process_id is None:
                raise ValueError('Khởi động bằng scripts/start.py để mở OH Desktop và RPA cùng nhau.')
            engine = DesktopRPA(self.process_id)
            self.events.put(('ready', None))
            while not self.shutdown.is_set():
                try:
                    action, data = self.commands.get(timeout=.35)
                except queue.Empty:
                    if pending:
                        try:
                            if pending.get('kind')=='creation':
                                result=engine.verify_creation(pending)
                                if result:self.events.put(('created',result));pending=None
                            elif engine.verify_saved(pending):
                                self.events.put(('saved', pending)); pending = None
                        except Exception as exc:
                            self.events.put(('error', str(exc))); pending = None
                    continue
                try:
                    if action == 'prepare':
                        self.events.put(('prepared', engine.prepare(*data)))
                    elif action == 'fill':
                        pending = engine.fill(*data, cancelled=self.stop)
                        pending['kind']='reception'
                        self.events.put(('filled', pending))
                    elif action == 'create':
                        pending=engine.fill_creation(data,cancelled=self.stop)
                        self.events.put(('creation_filled',pending))
                    elif action == 'demo':
                        record=engine.snapshot()['record'];pid=record['pid']
                        scans = json.loads((DEMO/'scans.json').read_text(encoding='utf-8'))
                        scans+=json.loads((DEMO/'new_scans.json').read_text(encoding='utf-8'))
                        self.events.put(('demo', next(s['scan'] for s in scans if s['pid'] == pid or json.loads(s['scan'])['national_id']==record['national_id'])))
                    elif action == 'cancel_pending': pending = None
                except Exception as exc:
                    pending = None
                    self.events.put(('error', str(exc)))
        except Exception as exc:
            self.events.put(('error', 'Không mở/điều khiển được OH: '+str(exc)))
        finally:
            pythoncom.CoUninitialize()

    def poll(self):
        try:
            while True:
                event, data = self.events.get_nowait()
                self.set_busy(False)
                if self.stop.is_set() and event in ('prepared', 'filled', 'saved','creation_filled','created'):
                    self.pending = None
                    self.proposal = None
                    self.status.set('Đã dừng lượt. Kiểm tra dữ liệu chưa lưu trên OH; chọn Lượt mới để tiếp tục.')
                    self.controls()
                    continue
                if event == 'ready':
                    self.status.set('OH đã mở. Chọn lần 1 để tạo PID/bung gói hoặc lần 2 để tiếp đón.')
                elif event=='creation_filled':
                    self.pending=data;self.proposal=None
                    self.status.set('CHỜ LƯU LẦN 1 · Kiểm tra hồ sơ/gói khám trên OH rồi bấm “Lưu và cấp PID”.')
                elif event=='created':
                    self.pending=None;self.proposal=None
                    for row in self.rows:
                        if row['national_id']==data['national_id']:row['pid']=data['pid']
                    selected=self.customer_box.current()
                    self.customer_box.configure(values=[f"Dòng {r['line']} · {r['name']} · {r.get('pid') or 'Chưa PID'} · {r.get('package_code','')}" for r in self.rows])
                    if selected>=0:self.customer_box.current(selected)
                    path=self.handoff_path()
                    self.created_info.set(f"Đã tạo và tải lại xác minh PID {data['pid']} · {data['name']} · Gói {data['package_code']}")
                    try:
                        prior=read_roster(path,'DS_bung_DEMO',data['company'],data['batch'])[0] if path.exists() else []
                        rows=[r for r in prior if r['national_id']!=data['national_id']]+[data]
                        export_prepared(path,rows)
                        self.status.set(f"HOÀN TẤT LẦN 1 · PID {data['pid']}. Đã xuất {len(rows)} hồ sơ: {path}")
                    except Exception as exc:
                        self.status.set(f"OH đã lưu PID {data['pid']} nhưng xuất file thất bại: {exc}. Ghi lại PID, không tạo lại hồ sơ.")
                elif event == 'demo':
                    self.mode.set('demo'); self.scan.set(data)
                    self.status.set('Đã lấy CCCD giả theo PID. Chọn “Đối chiếu”.')
                elif event == 'prepared':
                    self.proposal = data
                    record = data.snapshot['record']
                    nid = data.identity.national_id
                    self.info.set(f"KHỚP · {record['pid']} · {record['name']}\nCCCD: {'*'*8}{nid[-4:]} · {record['dob']}\nNguồn địa chỉ Excel: {data.row['address']}\nOH hiện tại: {', '.join(record['address'].values())}\nDự kiến: bổ sung CCCD nếu trống và cập nhật địa chỉ bên dưới.")
                    for key in self.address: self.address[key].set(record['address'][key])
                    self.status.set('Đối chiếu khớp. Hỏi khách, sửa địa chỉ và đánh dấu xác nhận.')
                elif event == 'filled':
                    self.pending = data; self.proposal = None
                    self.status.set(f"Đã điền và đọc lại ({data['elapsed_ms']/1000:.2f}s). CHỜ LƯU: kiểm tra rồi bấm Lưu hồ sơ trên OH.")
                elif event == 'saved':
                    self.pending = None; self.proposal = None; self.confirmed.set(False)
                    self.status.set('HOÀN TẤT · Đã lưu và mở lại xác minh đúng hồ sơ. Chọn Lượt mới để tiếp tục.')
                elif event == 'error':
                    self.pending = None; self.proposal = None; self.confirmed.set(False)
                    self.status.set('CẦN KIỂM TRA · '+data)
                self.controls()
        except queue.Empty:
            pass
        if not self.shutdown.is_set(): self.root.after(100, self.poll)

    def close(self):
        self.stop.set(); self.shutdown.set()
        self.root.destroy()


if __name__ == '__main__':
    window = tk.Tk()
    ReceptionApp(window)
    window.mainloop()
