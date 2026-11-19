"""Quét CCCD → đối chiếu ds bung của ngày → điền form .docx (trang 1 và 4) → (tùy chọn) in."""
import sys
import threading
import tkinter as tk
from datetime import date, datetime
from tkinter import ttk

import fill
from shared.identity import ReviewRequired
from shared.excel import day_folder

PACKAGES = {'Tự động theo ds bung': None, 'Gói cơ bản': 'coban', 'Gói tiêu chuẩn': 'tieuchuan'}


class App:
    def __init__(self, root):
        self.root = root
        self.rows, self.path, self.last = [], None, None
        self.link = None
        self.outcome = (False, '')
        root.title('In phiếu khám sức khỏe — quét CCCD')
        root.geometry('900x640')
        root.minsize(760, 520)
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TFrame', background='#f4f7f8')
        style.configure('TLabel', background='#f4f7f8', foreground='#243947', font=('Segoe UI', 10))
        style.configure('Title.TLabel', font=('Segoe UI', 18, 'bold'), foreground='#176b78')
        style.configure('TButton', font=('Segoe UI', 10), padding=6)
        style.configure('TCheckbutton', background='#f4f7f8', font=('Segoe UI', 10))
        body = ttk.Frame(root, padding=16)
        body.pack(fill='both', expand=True)
        ttk.Label(body, text='In phiếu khám sức khỏe theo CCCD', style='Title.TLabel').pack(anchor='w')
        self.source = tk.StringVar()
        ttk.Label(body, textvariable=self.source, wraplength=840).pack(anchor='w', pady=(2, 10))

        ttk.Label(body, text='Quét CCCD tại đây (đầu đọc nhập chuỗi rồi Enter; hoặc gõ 12 số CCCD):').pack(anchor='w')
        self.scan = tk.StringVar()
        self.entry = ttk.Entry(body, textvariable=self.scan, font=('Consolas', 13))
        self.entry.pack(fill='x', pady=(2, 8))
        self.entry.bind('<Return>', lambda _: self.process())
        row = ttk.Frame(body)
        row.pack(fill='x')
        ttk.Label(row, text='Gói khám:').pack(side='left')
        self.package = tk.StringVar(value='Tự động theo ds bung')
        ttk.Combobox(row, textvariable=self.package, values=list(PACKAGES), state='readonly', width=24).pack(side='left', padx=8)
        self.auto_open = tk.BooleanVar(value=True)
        ttk.Checkbutton(row, text='Tự mở file Word để kiểm tra', variable=self.auto_open).pack(side='left', padx=(12, 0))
        self.auto_print = tk.BooleanVar(value=False)
        ttk.Checkbutton(row, text='Tự in ngay (bỏ qua bước kiểm tra)', variable=self.auto_print).pack(side='left', padx=12)
        ttk.Button(row, text='Nạp lại danh sách', command=self.load).pack(side='right')
        row2 = ttk.Frame(body)
        row2.pack(fill='x', pady=(8, 0))
        ttk.Button(row2, text='📱 Ghép điện thoại quét CCCD…', command=self.pair_phone).pack(side='left')
        ttk.Button(row2, text='Mô phỏng quét QR (khách mẫu)…', command=self.simulate).pack(side='left', padx=8)
        ttk.Button(row2, text='Quét từ ảnh CCCD…', command=self.scan_image).pack(side='left')
        self.phone_state = tk.StringVar(value='Điện thoại: chưa ghép đôi')
        ttk.Label(row2, textvariable=self.phone_state).pack(side='right')

        self.result = tk.StringVar(value='Chưa quét.')
        ttk.Label(body, textvariable=self.result, wraplength=840, justify='left', font=('Segoe UI', 11)).pack(anchor='w', pady=10, fill='x')
        actions = ttk.Frame(body)
        actions.pack(fill='x')
        self.open_btn = ttk.Button(actions, text='Mở file xem trước', command=self.open_last, state='disabled')
        self.open_btn.pack(side='left')
        self.print_btn = ttk.Button(actions, text='In phiếu này', command=self.print_last, state='disabled')
        self.print_btn.pack(side='left', padx=8)

        cols = ('Giờ', 'Khách hàng', 'Form', 'Kết quả')
        self.tree = ttk.Treeview(body, columns=cols, show='headings', height=10)
        for c, w in zip(cols, (70, 260, 150, 380)):
            self.tree.heading(c, text=c)
            self.tree.column(c, width=w, anchor='w')
        self.tree.pack(fill='both', expand=True, pady=(12, 0))
        self.load()
        self.entry.focus_set()

    def load(self):
        try:
            self.path, _, self.rows = fill.load_customers()
            self.source.set(f'Ngày {day_folder().name} · {self.path.name} · {len(self.rows)} khách. Form lưu vào thư mục "phieu_in" cùng ngày.')
        except ReviewRequired as exc:
            self.path, self.rows = None, []
            self.source.set(f'Không nạp được ds bung hôm nay: {exc}')

    def log(self, name, form, outcome):
        self.tree.insert('', 0, values=(datetime.now().strftime('%H:%M:%S'), name, form, outcome))

    def process(self):
        text = self.scan.get()
        self.scan.set('')
        self.entry.focus_set()
        self.last = None
        self.open_btn.configure(state='disabled')
        self.print_btn.configure(state='disabled')
        if not text.strip():
            return
        try:
            if not self.rows:
                self.load()
            if not self.rows:
                raise ReviewRequired('Chưa có danh sách bung hôm nay.')
            scan = fill.parse_scan(text)
            row = fill.find_customer(self.rows, scan['cccd'])
            problems = fill.check_scan(row, scan)
            out, form, filled = fill.make_form(row, scan, PACKAGES[self.package.get()], out_dir=day_folder() / 'phieu_in')
        except Exception as exc:
            self.result.set('KHÔNG ĐIỀN ĐƯỢC · ' + str(exc))
            self.log('', '', 'Lỗi · ' + str(exc))
            self.outcome = (False, 'Không điền được: ' + str(exc))
            return
        p = fill.person(row, scan)
        name = p['name']
        self.last = out
        self.open_btn.configure(state='normal')
        self.print_btn.configure(state='normal')
        from_card = [label for key, label in (('name', 'họ tên'), ('dob', 'ngày sinh'), ('sex', 'giới tính'), ('address', 'địa chỉ'), ('issued', 'ngày cấp')) if scan.get(key)]
        source = ('Từ thẻ CCCD: ' + ', '.join(from_card) + '. Bổ sung từ ds bung: số điện thoại, PID, công ty.') if from_card else 'Từ ds bung (chưa đọc được dữ liệu trên thẻ).'
        info = f'{name} · {"Nam" if p["sex"] == "nam" else "Nữ"} · {p["dob"]} · {form}\nĐã điền: {len(filled)} trường · {out.name}\n{source}'
        if problems:
            self.result.set('CẦN KIỂM TRA · ' + '; '.join(problems) + '\n' + info + '\nKhông tự in vì thông tin thẻ không khớp.')
            self.log(name, form, 'Đã tạo file · thông tin thẻ không khớp (không in)')
            self.outcome = (False, 'Cần kiểm tra: ' + '; '.join(problems))
            return
        if self.auto_print.get():
            self.result.set('Đang in… ' + info)
            self.print_btn.configure(state='disabled')
            self.outcome = (True, f'{name} — đã tạo {form}, đang in')
            threading.Thread(target=self.do_print, args=(out, name, form), daemon=True).start()
        else:
            opened = self.auto_open.get()
            self.result.set('Đã điền form' + (' và mở Word: kiểm tra thông tin rồi in (Ctrl+P). ' if opened else '. ') + info)
            self.log(name, form, 'Đã mở Word để kiểm tra' if opened else 'Đã tạo file (chưa in)')
            self.outcome = (True, f'{name} — đã điền {form}' + (', đã mở Word trên máy tính' if opened else ''))
            if opened:
                self.open_last()

    def do_print(self, path, name, form):
        try:
            fill.print_docx(path)
            outcome = 'Đã gửi lệnh in'
        except Exception as exc:
            outcome = 'Lỗi in · ' + str(exc)
        self.root.after(0, lambda: (self.log(name, form, outcome), self.result.set(f'{outcome} · {name}'), self.print_btn.configure(state='normal')))

    def feed(self, text):
        """Đưa chuỗi QR vào ô quét như thể đầu đọc vừa nhập."""
        self.scan.set(text)
        self.process()
        return self.outcome

    def scan_image(self):
        from tkinter import filedialog
        path = filedialog.askopenfilename(title='Chọn ảnh CCCD có mã QR', filetypes=[('Ảnh', '*.jpg *.jpeg *.png *.bmp *.webp'), ('Tất cả', '*.*')])
        if not path:
            return
        try:
            self.feed(fill.decode_qr(path))
        except Exception as exc:
            self.result.set('KHÔNG ĐỌC ĐƯỢC QR · ' + str(exc))
            self.log('', '', 'Lỗi quét ảnh · ' + str(exc))

    def pair_phone(self):
        """Ghép đôi điện thoại Android làm đầu quét: hiện QR ghép đôi; điện thoại mở trang, bật camera, quét QR CCCD."""
        import phone_scan
        if self.link is None:
            try:
                link = phone_scan.PhoneLink(fill.HERE / 'runtime' / 'certs', decoder=fill.decode_qr)
                link.start()
            except OSError as exc:
                self.result.set(f'KHÔNG MỞ ĐƯỢC CỔNG CHO ĐIỆN THOẠI ({phone_scan.HTTP_PORT}/{phone_scan.HTTPS_PORT}): {exc}. Đóng chương trình đang dùng cổng này hoặc đặt biến IN_PHIEU_HTTPS_PORT.')
                return
            self.link = link
            self.root.after(300, self.poll_phone)
        link = self.link
        win = tk.Toplevel(self.root)
        win.title('Ghép đôi điện thoại quét CCCD')
        win.configure(bg='#f4f7f8')
        win.transient(self.root)
        png = fill.make_qr_png(link.url)
        image = tk.PhotoImage(data=png)
        ttk.Label(win, text='Mở camera điện thoại Android (cùng Wi-Fi với máy tính) quét mã QR này:', wraplength=520).pack(padx=16, pady=(16, 4))
        tk.Label(win, image=image, bg='white', bd=1, relief='solid').pack(pady=4)
        win.image = image
        field = ttk.Entry(win, width=62)
        field.insert(0, link.url)
        field.configure(state='readonly')
        field.pack(padx=16, pady=4)
        status = tk.StringVar()
        ttk.Label(win, textvariable=status, font=('Segoe UI', 11, 'bold')).pack(pady=4)
        steps = ('Trên điện thoại: mở đường dẫn → Chrome báo "không an toàn" (chứng chỉ tự ký) → Nâng cao → Tiếp tục → '
                 'Bật camera → đưa mã QR ở mặt sau CCCD vào khung. Thông tin tự hiện trên máy tính và mở file Word.\n\n'
                 'Lần đầu Windows có thể hỏi quyền mạng: chọn "Cho phép" (mạng riêng).\n'
                 f'Không có Wi-Fi: cắm cáp USB (bật Gỡ lỗi USB), chạy "adb reverse tcp:{phone_scan.HTTP_PORT} tcp:{phone_scan.HTTP_PORT}" '
                 f'rồi mở trên Chrome điện thoại:\n{link.usb_url}')
        ttk.Label(win, text=steps, wraplength=520, justify='left').pack(padx=16, pady=8)

        def refresh():
            if not win.winfo_exists():
                return
            status.set('● Điện thoại đã kết nối' if link.connected() else '○ Đang chờ điện thoại…')
            win.after(1000, refresh)
        refresh()
        ttk.Button(win, text='Đóng (vẫn nhận mã nền)', command=win.destroy).pack(pady=(0, 16))

    def poll_phone(self):
        """Nhận chuỗi QR từ điện thoại → xử lý như đầu đọc → trả kết quả để điện thoại hiển thị."""
        link = self.link
        if link is None:
            return
        try:
            while True:
                text = link.codes.get_nowait()
                ok, message = self.feed(text)
                link.publish(message or ('Đã xử lý.' if ok else 'Không điền được.'), ok)
        except Exception as exc:
            if exc.__class__.__name__ != 'Empty':
                link.publish('Lỗi xử lý trên máy tính: ' + str(exc), False)
        self.phone_state.set('📱 Điện thoại: đã kết nối' if link.connected() else '📱 Điện thoại: đang chờ')
        self.root.after(300, self.poll_phone)

    def simulate(self):
        """Mô phỏng: chọn một khách trong ds bung → sinh thẻ có mã QR giả → 'quét' (giải mã ảnh QR) → điền form."""
        if not self.rows:
            self.result.set('Chưa có danh sách bung hôm nay để mô phỏng.')
            return
        win = tk.Toplevel(self.root)
        win.title('Mô phỏng quét QR CCCD')
        win.configure(bg='#f4f7f8')
        win.transient(self.root)
        names = [f"Dòng {r['line']} · " + ' '.join(str(r['values'].get(k) or '') for k in ('Patient Last Name', 'Patient Middle Name', 'Patient Given Name'))
                 for r in self.rows]
        pick = tk.StringVar(value=names[0])
        box = ttk.Combobox(win, textvariable=pick, values=names, state='readonly', width=42)
        box.pack(padx=16, pady=(16, 8))
        card = tk.Label(win, bg='white', bd=1, relief='solid')
        card.pack(padx=16, pady=4)
        hint = ttk.Label(win, text='Mã QR giả lập (không phải thẻ thật). Bấm “Quét QR này” như khi đưa thẻ vào đầu đọc.')
        hint.pack(padx=16)
        state = {}

        def show(*_):
            row = self.rows[names.index(pick.get())]
            text = fill.sample_scan(row)
            png = fill.make_qr_png(text)
            state['png'] = png
            state['image'] = tk.PhotoImage(data=png)    # giữ tham chiếu để ảnh không bị thu hồi
            card.configure(image=state['image'])
        box.bind('<<ComboboxSelected>>', show)
        show()

        def do_scan():
            try:
                text = fill.decode_qr(state['png'])
            except Exception as exc:
                self.result.set('KHÔNG ĐỌC ĐƯỢC QR · ' + str(exc))
                return
            win.destroy()
            self.feed(text)
        ttk.Button(win, text='Quét QR này', command=do_scan).pack(pady=12)

    def open_last(self):
        if self.last:
            import os
            os.startfile(str(self.last))

    def print_last(self):
        if self.last:
            self.print_btn.configure(state='disabled')
            threading.Thread(target=self.do_print, args=(self.last, self.last.stem, 'in lại'), daemon=True).start()


def run_once(argv) -> int:
    """Chế độ dòng lệnh: In_Phieu.exe --cccd "<chuỗi quét hoặc 12 số>" [--package coban|tieuchuan] [--print]. Tạo form rồi thoát."""
    import sys
    def opt(name):
        return argv[argv.index(name) + 1] if name in argv and argv.index(name) + 1 < len(argv) else None
    try:
        _, _, rows = fill.load_customers()
        scan = fill.parse_scan(opt('--cccd'))
        row = fill.find_customer(rows, scan['cccd'])
        problems = fill.check_scan(row, scan)
        out, form, filled = fill.make_form(row, scan, opt('--package'), out_dir=day_folder() / 'phieu_in')
        print(f'{out} | {form} | {len(filled)} trường' + (' | KHÔNG KHỚP: ' + '; '.join(problems) if problems else ''), file=sys.stderr)
        if '--print' in argv and not problems:
            fill.print_docx(out)
        return 1 if problems else 0
    except Exception as exc:
        print('LỖI: ' + str(exc), file=sys.stderr)
        return 2


def main():
    if '--cccd' in sys.argv:
        raise SystemExit(run_once(sys.argv))
    import ctypes
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except (AttributeError, OSError):
        ctypes.windll.user32.SetProcessDPIAware()
    root = tk.Tk()
    app = App(root)

    def close():
        if app.link:
            app.link.stop()
        root.destroy()
    root.protocol('WM_DELETE_WINDOW', close)
    if '--ghep-doi' in sys.argv:          # mở sẵn hộp ghép đôi điện thoại khi khởi động
        root.after(500, app.pair_phone)
    root.mainloop()


if __name__ == '__main__':
    main()
