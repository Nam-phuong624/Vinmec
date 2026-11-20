"""Điều khiển OHDemo.exe (OH mô phỏng) bằng Windows UI Automation, chạy nền.

Không gõ phím thật, không click chuột, không SetFocus: chỉ SetValue / BM_CLICK / WM_KEYDOWN / CB_SETCURSEL gửi
thẳng vào control, nên người dùng vẫn thao tác bình thường trên máy. Với mỗi dòng Excel:
  1. tìm theo họ tên;  2. trùng tên + trùng năm sinh → cập nhật theo Excel;
  3. không có → tạo mới (tên, năm sinh, SĐT) rồi bổ sung các trường còn lại ở trang Edit.
"""
import time
import unicodedata
import win32api
import win32con
import win32gui
import win32process
from pywinauto import Application
from pywinauto.controls.uiawrapper import UIAWrapper
from pywinauto.timings import wait_until
from pywinauto.uia_defines import IUIA
from pywinauto.uia_element_info import UIAElementInfo
from shared.excel import ohdemo_record
from shared.identity import ReviewRequired
from rpa_tool.contracts import audit
from rpa_tool.audit_trail import fields as record_fields, expected as record_expected

WINDOW_TITLE = 'OH · Patient Profile — DEMO'
PLACEHOLDER_ADDR = 'Add one or more addresses.'
UIA_AUTOMATION_ID = 30011
CB_SETCURSEL = 0x014E


class NeedManual(ReviewRequired):
    """Đã xử lý được phần lớn nhưng còn trường phải điền tay."""


def fold(text: str) -> str:
    t = unicodedata.normalize('NFD', str(text or '').lower().replace('đ', 'd'))
    return ' '.join(''.join(c for c in t if unicodedata.category(c) != 'Mn').split())


def day_month_conflict(oh_dob: str, excel_dob: str) -> bool:
    """Hai ngày sinh đầy đủ (d/m/yyyy) cùng năm nhưng khác ngày hoặc tháng: có thể là hai người khác nhau.
    Nếu OH chỉ có năm/tháng (không đủ ngày) thì không đủ căn cứ để coi là mâu thuẫn."""
    def parts(text):
        p = str(text or '').strip().split('/')
        return tuple(int(x) for x in p) if len(p) == 3 and all(x.strip().isdigit() for x in p) else None
    a, b = parts(oh_dob), parts(excel_dob)
    return a is not None and b is not None and a[2] == b[2] and a[:2] != b[:2]


def find_window() -> int | None:
    found = []

    def visit(h, _):
        if win32gui.IsWindowVisible(h) and win32gui.GetWindowText(h) == WINDOW_TITLE:
            found.append(h)
    win32gui.EnumWindows(visit, None)
    return found[0] if found else None


class OhDemoRPA:
    def __init__(self, timeout=5):
        handle = find_window()
        if not handle:
            raise ReviewRequired('Chưa thấy cửa sổ OHDemo.exe. Hãy mở OHDemo.exe trước.')
        self.handle = handle
        self.pid = win32process.GetWindowThreadProcessId(handle)[1]
        self.timeout = timeout
        self.app = Application(backend='uia').connect(handle=handle)
        self.w = self.app.window(handle=handle)
        self.iuia = IUIA().iuia
        self.root = self.w.element_info.element
        self.index = None
        self.last_change = None   # vết 'trước/sau' của dòng vừa xử lý xong (runner ghi ra nhật ký thay đổi)

    # ---- chỉ mục control của trang hiện tại -----------------------------------------------------
    def refresh(self):
        """Quét một lần toàn bộ cây UIA (có cache AutomationId) → nhanh hơn nhiều so với tìm từng control."""
        request = self.iuia.CreateCacheRequest()
        request.AddProperty(UIA_AUTOMATION_ID)
        found = self.root.FindAllBuildCache(4, self.iuia.CreateTrueCondition(), request)
        index = {}
        for i in range(found.Length):
            element = found.GetElement(i)
            aid = element.CachedAutomationId
            if aid:
                index.setdefault(aid, element)
        self.index = index
        return index

    def invalidate(self):
        self.index = None

    def diagnose(self) -> str:
        """Mô tả ngắn tình trạng OH lúc lỗi: trang đang mở, dòng trạng thái, hộp thoại, cửa sổ ẩn/thu nhỏ/khóa."""
        try:
            h = self.handle
            parts = []
            if not win32gui.IsWindow(h):
                return ' [cửa sổ OH đã đóng]'
            if win32gui.IsIconic(h):
                parts.append('cửa sổ OH đang THU NHỎ (RPA không điều khiển được cửa sổ thu nhỏ)')
            if not win32gui.IsWindowEnabled(h):
                parts.append('cửa sổ OH đang bị khóa bởi một hộp thoại')
            boxes = self.box_texts()
            if boxes:
                parts.append('OH đang hiện hộp thoại: ' + ' | '.join(boxes))
            try:
                parts.append('trang đang mở: ' + self.state())
                if self.index and 'status' in self.index:      # đọc trực tiếp, không chờ (tránh gọi đệ quy khi lỗi)
                    parts.append('dòng trạng thái OH: "' + UIAWrapper(UIAElementInfo(self.index['status'])).window_text()[:80] + '"')
            except Exception:
                pass
            return ' [' + '; '.join(parts) + ']' if parts else ''
        except Exception:
            return ''

    def message_boxes(self):
        found = []

        def visit(w, _):
            if (win32gui.IsWindowVisible(w) and win32gui.GetClassName(w) == '#32770'
                    and win32process.GetWindowThreadProcessId(w)[1] == self.pid):
                found.append(w)
        win32gui.EnumWindows(visit, None)
        return found

    def box_texts(self):
        out = []
        for w in self.message_boxes():
            texts = []
            win32gui.EnumChildWindows(w, lambda c, _: texts.append(win32gui.GetWindowText(c)) or True, None)
            out.append(' '.join(x for x in texts if x and x not in ('&Yes', '&No', 'OK')))
        return out

    def clear_boxes(self):
        """Đóng mọi hộp thoại xác nhận còn kẹt trong OH: "Bỏ các thay đổi chưa lưu?" → Yes; "Vẫn tạo mới?" (nghi trùng) → No."""
        cleared = []
        for w, text in zip(self.message_boxes(), self.box_texts()):
            win32gui.PostMessage(w, win32con.WM_COMMAND, 7 if 'Vẫn tạo mới' in text else 6, 0)   # IDNO / IDYES
            cleared.append(text)
        if cleared:
            time.sleep(0.3)
        return cleared

    def has(self, aid, fresh=False):
        if fresh or self.index is None:
            self.refresh()
        return aid in self.index

    def wait_for(self, condition, what, wait=None):
        end = time.time() + (wait or self.timeout)
        while True:
            self.refresh()
            if condition():
                return
            if time.time() > end:
                raise ReviewRequired('Hết thời gian chờ: ' + what + self.diagnose())
            time.sleep(0.08)

    def get(self, aid, dialog=None):
        if dialog is not None:     # hộp thoại nhỏ: tìm trực tiếp
            spec = dialog.child_window(auto_id=aid)
            spec.wait('exists', timeout=self.timeout)
            return spec.wrapper_object()
        if self.index is None or aid not in self.index:
            self.wait_for(lambda: aid in self.index, 'control ' + aid)
        return UIAWrapper(UIAElementInfo(self.index[aid]))

    def label(self, aid):
        return self.get(aid).window_text()

    def set_text(self, aid, value, dialog=None):
        self.get(aid, dialog).set_edit_text(value)

    def read_text(self, aid):
        return self.get(aid).get_value()

    def combo_items(self, aid):
        return list(self.get(aid).texts())

    def combo_value(self, aid):
        try:
            return self.get(aid).selected_text() or ''
        except Exception:
            return ''

    def select(self, aid, value):
        """Chọn mục của ComboBox bằng CB_SETCURSEL (không mở danh sách thả xuống, không cần focus)."""
        box = self.get(aid)
        items = list(box.texts())
        if value not in items:
            raise ReviewRequired('Không có mục "' + value + '" trong ' + aid)
        win32gui.SendMessage(box.handle, CB_SETCURSEL, items.index(value), 0)

    def click(self, aid, dialog=None):
        button = self.get(aid, dialog)
        if not button.is_enabled():
            raise ReviewRequired('Nút đang bị khóa: ' + aid)
        win32gui.PostMessage(button.handle, win32con.BM_CLICK, 0, 0)
        self.invalidate()

    def enter(self, aid):
        handle = self.get(aid).handle
        win32api.PostMessage(handle, win32con.WM_KEYDOWN, win32con.VK_RETURN, 0)
        win32api.PostMessage(handle, win32con.WM_KEYUP, win32con.VK_RETURN, 0)
        self.invalidate()

    def status(self):
        return self.label('status')

    # ---- trạng thái trang ------------------------------------------------------------------------
    def state(self, fresh=True):
        if fresh or self.index is None:
            self.refresh()
        for name, aid in (('list', 'search-results'), ('view', 'view-pid'), ('edit', 'edit-pid'), ('new', 'new-first')):
            if aid in self.index:
                return name
        return 'blank'

    def signature(self):
        state = self.state()
        key = {'list': 'search-results', 'view': 'view-pid', 'edit': 'edit-pid', 'new': 'new-first'}.get(state)
        if not key:
            return state, None
        try:
            return state, UIAWrapper(UIAElementInfo(self.index[key])).handle or self.label(key)
        except Exception:
            return state, None

    def dismiss_msgbox(self):
        """Đóng hộp thoại xác nhận (nếu có) bằng Yes; dùng khi phục hồi sau lỗi."""
        def visit(h, _):
            if (win32gui.IsWindowVisible(h) and win32gui.GetClassName(h) == '#32770'
                    and win32process.GetWindowThreadProcessId(h)[1] == self.pid):
                win32gui.PostMessage(h, win32con.WM_COMMAND, 6, 0)  # IDYES
        win32gui.EnumWindows(visit, None)

    def leave_edit(self):
        if self.state() == 'edit':
            self.click('edit-toggle')
            time.sleep(0.3)
            self.dismiss_msgbox()
            self.wait_for(lambda: 'edit-pid' not in self.index, 'thoát chế độ Edit')

    # ---- tìm kiếm ----------------------------------------------------------------------------------
    def search(self, query):
        previous = self.signature()
        self.set_text('pid-search', query)
        self.enter('pid-search')
        end = time.time() + 0.8        # không đổi gì: kết quả là trang trống (không có hồ sơ)
        while time.time() < end:
            if self.signature() != previous:
                break
        return self.state()

    def result_rows(self):
        rows = []
        for item in self.get('search-results').texts():
            if len(item) >= 7 and item[0] != 'Header Control':
                rows.append(dict(pid=item[0], name=item[1], sex=item[2], dob=item[3], phone=item[5], address=item[6]))
        return rows

    def open_pid(self, pid):
        for item in self.get('search-results').children():
            if item.element_info.control_type == 'ListItem' and item.window_text() == pid:
                item.select()
                break
        else:
            raise ReviewRequired('Không chọn được dòng ' + pid + ' trong danh sách kết quả.')
        self.click('results-open')
        self.wait_for(lambda: 'view-pid' in self.index and self.label('view-pid') == pid, 'mở hồ sơ ' + pid)

    # ---- đọc / ghi trang Edit ----------------------------------------------------------------------
    def read_edit(self):
        info = self.label('edit-address-info')
        return dict(
            pid=self.label('edit-pid'), title=self.combo_value('edit-local-title'),
            first=self.read_text('edit-local-first'), middle=self.read_text('edit-local-middle'), last=self.read_text('edit-local-last'),
            sex=self.combo_value('edit-sex'), dob=self.read_text('edit-dob'), phone=self.read_text('edit-phone'),
            nationality=self.combo_value('edit-nationality'),
            addresses=[] if info == PLACEHOLDER_ADDR else [a.strip() for a in info.split(';') if a.strip()])

    def add_address(self, parts):
        """Bấm "+" ở Addresses: các ô địa chỉ mở rộng ngay bên dưới trong cùng trang; điền rồi bấm Add."""
        province, ward, street = parts
        self.click('edit-add-address')
        self.wait_for(lambda: 'edit-address-province' in self.index, 'mở các ô địa chỉ')
        self.set_text('edit-address-province', province)
        self.set_text('edit-address-ward', ward)
        self.set_text('edit-address-street', street)
        self.click('edit-address-add')
        self.wait_for(lambda: 'edit-address-province' not in self.index, 'thêm địa chỉ (khung địa chỉ phải thu lại)')

    def apply(self, rec, cur):
        """Chỉ ghi các trường khác Excel; trả (các trường đã đổi, các việc phải điền tay)."""
        changed, manual = [], []
        if rec['title'] and rec['title'] != cur['title']:
            if rec['title'] in self.combo_items('edit-local-title'):
                self.select('edit-local-title', rec['title']); changed.append('Title')
            else:
                manual.append('Title "' + rec['title'] + '" không có trong danh mục')
        for key, aid, label in (('first', 'edit-local-first', 'Họ'), ('middle', 'edit-local-middle', 'Đệm'), ('last', 'edit-local-last', 'Tên')):
            if rec[key] != cur[key] and (rec[key] or key == 'middle'):
                self.set_text(aid, rec[key]); changed.append(label)
        if rec['sex'] != cur['sex']:
            self.select('edit-sex', rec['sex']); changed.append('Sex')
        if rec['dob'] != cur['dob']:
            self.select('edit-dob-precision', 'Year, Month and Day')
            self.set_text('edit-dob', rec['dob']); changed.append('Ngày sinh')
        if rec['phone'] != cur['phone']:
            self.set_text('edit-phone', rec['phone']); changed.append('Điện thoại')
        if rec['nationality'] and rec['nationality'] != cur['nationality']:
            if rec['nationality'] in self.combo_items('edit-nationality'):
                self.select('edit-nationality', rec['nationality']); changed.append('Nationality')
            else:
                manual.append('Nationality "' + rec['nationality'] + '" không có trong danh mục')
        if rec['address']:
            if rec['address_parts'] is None:
                manual.append('Địa chỉ không tách được: "' + rec['address'] + '"')
            else:
                province, ward, street = rec['address_parts']
                formatted = ', '.join(p for p in (street, ward, province) if p)
                if formatted not in cur['addresses']:
                    self.add_address(rec['address_parts']); changed.append('Địa chỉ')
        return changed, manual

    def save_edit(self, pid):
        """Bấm Lưu và chờ OH báo ĐÚNG hồ sơ này đã lưu (không nhận nhầm dòng trạng thái của lần lưu trước)."""
        self.click('edit-save')
        wanted = 'Đã lưu hồ sơ ' + pid
        end = time.time() + self.timeout
        while time.time() < end:
            text = self.status()
            if text.startswith(wanted):
                return
            if text.startswith('Chưa lưu'):
                raise ReviewRequired(text)
            time.sleep(0.1)
        raise ReviewRequired('OH không báo đã lưu hồ sơ ' + pid + ' trong ' + str(self.timeout) + ' giây.' + self.diagnose())

    # ---- đối chiếu dữ liệu đã nhập ---------------------------------------------------------------------
    @staticmethod
    def mismatch(cur, rec, manual=()):
        """So nội dung form/hồ sơ với dữ liệu Excel; trả danh sách chỗ lệch (rỗng = khớp). Trường đã báo "cần điền tay" thì bỏ qua."""
        skip = ' '.join(manual)
        bad = []
        for key, label in (('first', 'Họ'), ('middle', 'Đệm'), ('last', 'Tên'), ('sex', 'Giới tính'), ('dob', 'Ngày sinh'), ('phone', 'SĐT')):
            if cur[key] != rec[key] and (rec[key] or key == 'middle'):
                bad.append(f'{label}: OH="{cur[key]}" ≠ Excel="{rec[key]}"')
        if rec['title'] and cur['title'] != rec['title'] and 'Title' not in skip:
            bad.append(f'Title: OH="{cur["title"]}" ≠ Excel="{rec["title"]}"')
        if rec['nationality'] and cur['nationality'] != rec['nationality'] and 'Nationality' not in skip:
            bad.append(f'Quốc tịch: OH="{cur["nationality"]}" ≠ Excel="{rec["nationality"]}"')
        if rec['address'] and rec['address_parts'] is not None:
            province, ward, street = rec['address_parts']
            if ', '.join(x for x in (street, ward, province) if x) not in cur['addresses']:
                bad.append('Địa chỉ chưa có trong hồ sơ')
        return bad

    def read_back(self, pid):
        """Đọc lại hồ sơ đã lưu từ OH (mở hồ sơ → Edit → đọc → thoát Edit)."""
        self.leave_edit()
        if self.search(pid) != 'view' or self.label('view-pid') != pid:
            raise ReviewRequired('Không mở lại được hồ sơ ' + pid + ' để đối chiếu sau khi lưu.')
        self.click('edit-toggle')
        self.wait_for(lambda: 'edit-pid' in self.index, 'mở Edit để đối chiếu')
        cur = self.read_edit()
        self.leave_edit()
        return cur

    # ---- khôi phục hồ sơ cũ về giá trị trước ---------------------------------------------------------
    def restore_fields(self, pid, before):
        """Điền lại giá trị cũ vào hồ sơ đang ở trang Edit rồi Lưu. Trả danh sách việc phải làm tay (ví dụ xóa địa chỉ đã thêm)."""
        manual = []
        cur = self.read_edit()
        if cur['pid'] != pid:
            raise ReviewRequired(f'Trang Edit đang mở là {cur["pid"]}, không phải {pid}; dừng, không khôi phục.')
        for key, aid in (('title', 'edit-local-title'), ('sex', 'edit-sex'), ('nationality', 'edit-nationality')):
            if cur[key] != before[key]:
                if before[key] in self.combo_items(aid):
                    self.select(aid, before[key])
                else:
                    manual.append(f'{key}: không chọn lại được giá trị cũ "{before[key]}"')
        for key, aid in (('first', 'edit-local-first'), ('middle', 'edit-local-middle'), ('last', 'edit-local-last'), ('phone', 'edit-phone')):
            if cur[key] != before[key]:
                self.set_text(aid, before[key])
        if cur['dob'] != before['dob']:
            self.select('edit-dob-precision', 'Year, Month and Day')
            self.set_text('edit-dob', before['dob'])
        extra = [a for a in cur['addresses'] if a not in before['addresses']]
        if extra:
            manual.append('Địa chỉ RPA đã thêm, cần xóa tay trong OH: ' + ' | '.join(extra))
        check = self.read_edit()
        if check['pid'] != pid:
            raise ReviewRequired('Trang Edit đổi sang hồ sơ khác khi khôi phục; không lưu.')
        self.save_edit(pid)
        return manual

    # ---- một dòng Excel ------------------------------------------------------------------------------
    def process(self, row, stop=None) -> str:
        """Trả về chuỗi trạng thái. Ném ReviewRequired (lỗi) hoặc NeedManual (xong nhưng còn việc điền tay)."""
        def check():
            if stop is not None and stop.is_set():
                raise ReviewRequired('Đã dừng; dòng này chưa xử lý xong.')
        rec = ohdemo_record(row)
        started = time.time()
        self.last_change = None
        before_fields = None
        created = None            # PID hồ sơ mới đã tạo trong dòng này
        creating = False          # đã (hoặc sắp) bấm Save ở khung New Patient: có thể đã có hồ sơ mới dù chưa đọc được PID
        finished = False
        try:
            check()
            self.clear_boxes()
            self.leave_edit()
            state = self.search(rec['full_name'])
            if state not in ('list', 'blank') or self.read_text('pid-search').strip() != rec['full_name']:
                raise ReviewRequired('Kết quả tìm kiếm không phải của dòng này (trang đang mở: ' + state + '; có thao tác khác trên OH trong lúc RPA chạy?); dừng để không tạo trùng hoặc ghi nhầm.')
            matches = [r for r in (self.result_rows() if state == 'list' else [])
                       if fold(r['name']) == fold(rec['full_name'])]
            same_year = [r for r in matches if r['dob'][-4:] == rec['year']]
            if len(same_year) > 1:
                raise ReviewRequired('Có ' + str(len(same_year)) + ' hồ sơ cùng tên và năm sinh (' + ', '.join(r['pid'] for r in same_year) + '); chọn tay.')
            if not same_year and any(r['phone'] == rec['phone'] for r in matches):
                raise ReviewRequired('Trùng tên và số điện thoại nhưng khác năm sinh; kiểm tra tay.')
            if same_year and day_month_conflict(same_year[0]['dob'], rec['dob']):
                raise ReviewRequired(f'Hồ sơ {same_year[0]["pid"]} cùng họ tên và năm sinh nhưng khác ngày/tháng sinh '
                                     f'(OH: {same_year[0]["dob"]}; Excel: {rec["dob"]}); có thể là người khác hoặc nhập sai ngày; '
                                     'kiểm tra tay, RPA không tự ghi đè.')
            check()
            if same_year:
                pid = same_year[0]['pid']
                self.open_pid(pid)
                self.click('edit-toggle')
                self.wait_for(lambda: 'edit-pid' in self.index, 'mở trang Edit')
                verb = 'cập nhật'
            else:
                self.click('new-patient')
                try:
                    self.wait_for(lambda: 'new-first' in self.index, 'mở khung New Patient', wait=2.5)
                except ReviewRequired:
                    self.clear_boxes()
                    self.leave_edit()
                    self.click('new-patient')
                    self.wait_for(lambda: 'new-first' in self.index, 'mở khung New Patient')
                for aid, value in (('new-first', rec['first']), ('new-middle', rec['middle']), ('new-last', rec['last']),
                                   ('new-year', rec['year']), ('new-phone', rec['phone'])):
                    self.set_text(aid, value)
                check()
                creating = True
                self.click('new-save')
                self.wait_for(lambda: 'edit-pid' in self.index, 'cấp PID mới')
                pid = created = self.label('edit-pid')
                verb = 'tạo'
            check()
            current = self.read_edit()
            if current['pid'] != pid:
                raise ReviewRequired(f'Trang Edit đang mở là hồ sơ {current["pid"]}, không phải {pid} (có thao tác khác trên OH?); dừng để không ghi nhầm người.')
            if verb == 'cập nhật' and (fold(' '.join(x for x in (current['first'], current['middle'], current['last']) if x)) != fold(rec['full_name'])
                                       or current['dob'][-4:] != rec['year']):
                raise ReviewRequired(f'Hồ sơ {pid} đang mở không đúng tên/năm sinh dự định (có thao tác khác trên OH?); dừng để không ghi nhầm người.')
            before_fields = record_fields(current)
            changed, manual = self.apply(rec, current)
            check()
            if changed or verb == 'tạo':
                before_save = self.read_edit()         # form phải đúng là hồ sơ này và đúng dữ liệu Excel trước khi lưu
                gap = self.mismatch(before_save, rec, manual)
                if before_save['pid'] != pid or gap:
                    raise ReviewRequired(f'Form hồ sơ {before_save["pid"]} không khớp dữ liệu Excel trước khi lưu ({"; ".join(gap) or "sai hồ sơ"}); không lưu để tránh ghi sai.')
                self.save_edit(pid)
                saved = self.read_back(pid)             # đọc lại hồ sơ đã lưu để chắc chắn đúng
                gap = self.mismatch(saved, rec, manual)
                if gap:
                    raise ReviewRequired(f'Sau khi lưu, hồ sơ {pid} không khớp dữ liệu Excel ({"; ".join(gap)}); cần kiểm tra tay.')
                after_fields = record_fields(saved)
                result = f'Đã {verb} · PID {pid}' + (' · ' + ', '.join(changed) if changed else '')
            else:
                self.leave_edit()
                after_fields = before_fields
                result = f'Không đổi · PID {pid}'
            finished = True
            self.last_change = dict(pid=pid, action=verb if changed or verb == 'tạo' else 'giữ', changed=changed, manual=manual,
                                    before=None if verb == 'tạo' else before_fields, after=after_fields, expected=record_expected(rec))
            audit('row_done', pid=pid, action=verb if changed or verb == 'tạo' else 'giữ', elapsed_ms=round((time.time() - started) * 1000))
            if manual:
                raise NeedManual(f'PID {pid} · cần điền tay: ' + '; '.join(manual))
            return result
        except Exception as exc:
            gone = not win32gui.IsWindow(self.handle)
            if not gone:
                try:
                    self.clear_boxes()
                    self.leave_edit()
                except Exception:
                    pass
            if finished or isinstance(exc, NeedManual):
                raise
            if gone:
                message = 'Mất kết nối: cửa sổ OH đã bị đóng. Mở lại OHDemo.exe rồi chạy lại; dòng này chưa xử lý xong.'
            elif isinstance(exc, ReviewRequired):
                message = str(exc)
            else:
                message = f'Lỗi khi điều khiển OH ({type(exc).__name__}: {str(exc)[:120]}).' + self.diagnose()
            if created:
                message += f' · LƯU Ý: hồ sơ {created} đã được tạo nhưng chưa bổ sung đủ thông tin; chạy lại RPA để hoàn tất hoặc kiểm tra tay.'
            elif creating:
                message += ' · LƯU Ý: có thể đã tạo hồ sơ mới cho dòng này (chưa rõ PID); tìm theo họ tên trên OH để kiểm tra, chạy lại RPA sẽ tự hoàn tất.'
            raise ReviewRequired(message) from exc
