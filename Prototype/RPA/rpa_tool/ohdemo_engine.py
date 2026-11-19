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

WINDOW_TITLE = 'OH · Patient Profile — DEMO'
PLACEHOLDER_ADDR = 'Add one or more addresses.'
UIA_AUTOMATION_ID = 30011
CB_SETCURSEL = 0x014E


class NeedManual(ReviewRequired):
    """Đã xử lý được phần lớn nhưng còn trường phải điền tay."""


def fold(text: str) -> str:
    t = unicodedata.normalize('NFD', str(text or '').lower().replace('đ', 'd'))
    return ' '.join(''.join(c for c in t if unicodedata.category(c) != 'Mn').split())


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
                raise ReviewRequired('Hết thời gian chờ: ' + what)
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
        province, ward, street = parts
        self.click('edit-add-address')
        found = []

        def visit(h, _):
            if (win32gui.IsWindowVisible(h) and win32gui.GetWindowText(h).startswith('Add Address')
                    and win32process.GetWindowThreadProcessId(h)[1] == self.pid):
                found.append(h)
        wait_until(self.timeout, .1, lambda: (found.clear(), win32gui.EnumWindows(visit, None), bool(found))[2])
        dialog = self.app.window(handle=found[0])
        self.set_text('address-province', province, dialog)
        self.set_text('address-ward', ward, dialog)
        self.set_text('address-street', street, dialog)
        self.click('apply-address', dialog)
        wait_until(self.timeout, .1, lambda: not win32gui.IsWindow(found[0]))
        self.invalidate()

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

    def save_edit(self):
        self.click('edit-save')
        end = time.time() + self.timeout
        while time.time() < end:
            text = self.status()
            if text.startswith('Đã lưu hồ sơ'):
                return
            if text.startswith('Chưa lưu'):
                raise ReviewRequired(text)
            time.sleep(0.1)
        raise ReviewRequired('OH không báo lưu thành công trong ' + str(self.timeout) + ' giây.')

    # ---- một dòng Excel ------------------------------------------------------------------------------
    def process(self, row, stop=None) -> str:
        """Trả về chuỗi trạng thái. Ném ReviewRequired (lỗi) hoặc NeedManual (xong nhưng còn việc điền tay)."""
        def check():
            if stop is not None and stop.is_set():
                raise ReviewRequired('Đã dừng; dòng này chưa xử lý xong.')
        rec = ohdemo_record(row)
        started = time.time()
        try:
            check()
            self.leave_edit()
            state = self.search(rec['full_name'])
            matches = [r for r in (self.result_rows() if state == 'list' else [])
                       if fold(r['name']) == fold(rec['full_name'])]
            same_year = [r for r in matches if r['dob'][-4:] == rec['year']]
            if len(same_year) > 1:
                raise ReviewRequired('Có ' + str(len(same_year)) + ' hồ sơ cùng tên và năm sinh (' + ', '.join(r['pid'] for r in same_year) + '); chọn tay.')
            if not same_year and any(r['phone'] == rec['phone'] for r in matches):
                raise ReviewRequired('Trùng tên và số điện thoại nhưng khác năm sinh; kiểm tra tay.')
            check()
            if same_year:
                pid = same_year[0]['pid']
                self.open_pid(pid)
                self.click('edit-toggle')
                self.wait_for(lambda: 'edit-pid' in self.index, 'mở trang Edit')
                verb = 'cập nhật'
            else:
                self.click('new-patient')
                self.wait_for(lambda: 'new-first' in self.index, 'mở khung New Patient')
                for aid, value in (('new-first', rec['first']), ('new-middle', rec['middle']), ('new-last', rec['last']),
                                   ('new-year', rec['year']), ('new-phone', rec['phone'])):
                    self.set_text(aid, value)
                check()
                self.click('new-save')
                self.wait_for(lambda: 'edit-pid' in self.index, 'cấp PID mới')
                pid = self.label('edit-pid')
                verb = 'tạo'
            check()
            current = self.read_edit()
            changed, manual = self.apply(rec, current)
            check()
            if changed or verb == 'tạo':
                self.save_edit()
                result = f'Đã {verb} · PID {pid}' + (' · ' + ', '.join(changed) if changed else '')
            else:
                self.leave_edit()
                result = f'Không đổi · PID {pid}'
            audit('row_done', pid=pid, action=verb if changed or verb == 'tạo' else 'giữ', elapsed_ms=round((time.time() - started) * 1000))
            if manual:
                raise NeedManual(f'PID {pid} · cần điền tay: ' + '; '.join(manual))
            return result
        except Exception:
            try:
                self.leave_edit()
            except Exception:
                pass
            raise
