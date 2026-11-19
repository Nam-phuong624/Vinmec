"""Nhóm I (người dùng can thiệp trên OH khi RPA đang chạy) và nhóm J (OH hoặc RPA bị ngắt/dừng giữa chừng).

Chạy:  python kiem_thu\\nhom_i_j.py truoc     (kiểm thử bản mã đã lưu trong kiem_thu\\_ban_truoc_sua)
       python kiem_thu\\nhom_i_j.py sau       (kiểm thử bản mã hiện tại)
Kết quả: kiem_thu/ket_qua_ij_<chế độ>.json   (đặt KT_ONLY=I01,J01 để chỉ chạy vài ca)

Cách làm: mỗi ca khởi động OHDemo mới, RPA xử lý dòng Excel; giữa hai bước của RPA, một "người dùng" giả lập (hooks.py)
làm đúng một thao tác (tìm hồ sơ khác, gõ vào ô, bấm nút, thu nhỏ cửa sổ...) hoặc OH/RPA bị tắt ở đúng bước đó.
Sau đó đọc lại TOÀN BỘ hồ sơ trong OH và kiểm tra các bất biến an toàn (không phụ thuộc RPA tự báo gì):
  S1  hồ sơ có sẵn không thuộc dòng này không bị đổi (không ghi nhầm người);
  S2  nếu RPA báo thành công thì hồ sơ phải khớp dữ liệu Excel; OH đã tắt thì không được báo thành công;
  S3  không tạo hồ sơ trùng hoặc hồ sơ ngoài ý định (kể cả từ dòng lỗi dữ liệu);
  S4  hồ sơ nửa vời do lỗi/dừng phải được nêu (PID) trong thông báo của RPA;
  S5  (ca bị tắt RPA) dòng đang xử lý dở phải để lại dấu vết; dòng lỗi đã xử lý trước đó phải còn trong ds lỗi.xlsx;
  C1  chạy lại khi không còn can thiệp: hội tụ về đúng dữ liệu Excel, không trùng, không đổi hồ sơ khác.
Giới hạn: thao tác "người dùng" được chèn đồng bộ giữa hai bước của RPA (tái lập được) chứ không chạy song song ngẫu nhiên.
"""
import json
import os
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
MODE = sys.argv[1] if len(sys.argv) > 1 else 'sau'
if MODE == 'truoc':
    os.environ['KT_SRC'] = str(HERE / '_ban_truoc_sua')
sys.path.insert(0, str(HERE))
import chay_kiem_thu as K
import win32api
import win32con
import win32gui
from openpyxl import load_workbook
from hooks import Hooks

E = K.E
TMP = HERE / '_tmp'
TMP.mkdir(exist_ok=True)
LOGF = HERE / f'tien_do_ij_{MODE}.log'
DEMO_IDS = ['DEMO0001', 'DEMO0002', 'DEMO0003', 'DEMO0004', 'DEMO0005']
SUCCESS = ('CREATE', 'UPDATE', 'SAME')


def log(text):
    line = f'{datetime.now():%H:%M:%S} {text}'
    print(line, flush=True)
    with LOGF.open('a', encoding='utf-8') as f:
        f.write(line + '\n')


# ---------------------------------------------------------------- dữ liệu ------------------------------------------
U_RAW = dict(title='Ông', last='Nguyễn', middle='Văn', given='Mẫu', dob='15/02/1980', sex='Nam',
             addr='Số 10 Đường Láng, Phường Láng Hạ, Hà Nội', phone='0900000009', nat='Việt Nam', cccd='079080000001')
U_TRUTH = dict(title='Ông', first='Nguyễn', middle='Văn', last='Mẫu', sex='Nam', dob='15/02/1980', phone='0900000009', nat='Việt Nam',
               addr='Số 10 Đường Láng, Phường Láng Hạ, Hà Nội')
_seed = [9000]


def make_row(kind):
    if kind == 'U':
        return dict(kind='U', raw=dict(U_RAW), truth=dict(U_TRUTH), name='Nguyễn Văn Mẫu')
    _seed[0] += 1
    raw, truth = K.person(_seed[0], year_range=(1975, 1999))
    name = ' '.join(x for x in (raw['last'], raw['middle'], raw['given']) if x)
    if kind == 'BAD':
        raw['phone'] = '123'
        return dict(kind='BAD', raw=raw, truth=None, name=name)
    return dict(kind='N', raw=raw, truth=truth, name=name)


def write_rows(rows, tag):
    cases = [K.Case(id=f'{tag}{i}', group='I', title='', risk='', raw=r['raw'], expected='CREATE') for i, r in enumerate(rows, 1)]
    path = TMP / f'{tag}.xlsx'
    K.write_xlsx(cases, path)
    header, data = K.read_daily(path)
    for r, d in zip(rows, data):
        r['line'], r['row'] = d['line'], d
    return path, header


# ---------------------------------------------------------------- người dùng giả lập -------------------------------
class SkipC1(Exception):
    """Ca mà bản ghi đã bị chính người dùng lưu dữ liệu lạ (RPA báo lỗi nêu rõ): cần người sửa tay, không kiểm tra hồi phục tự động."""


class Ctx:
    def __init__(self):
        self.stop = threading.Event()
        self.relaunch()

    def relaunch(self):
        self.proc, self.eng = K.launch_oh()
        self.user = E.OhDemoRPA()                          # "người dùng" dùng bản điều khiển riêng, không chia sẻ bộ nhớ đệm với RPA

    def act(self, p):
        do, arg, u, h = p['do'], p.get('arg'), self.user, self.eng.handle
        if do == 'search_other':
            u.set_text('pid-search', 'DEMO0002'); u.enter('pid-search'); time.sleep(0.7)
        elif do == 'search_other_edit':
            u.set_text('pid-search', 'DEMO0002'); u.enter('pid-search'); time.sleep(0.7)
            u.wait_for(lambda: 'view-pid' in u.index, 'view'); u.click('edit-toggle'); time.sleep(0.7)
        elif do == 'set_search_text':
            u.set_text('pid-search', arg); time.sleep(0.3)
        elif do == 'click':
            u.click(arg); time.sleep(0.6)
        elif do == 'type':
            u.set_text(arg[0], arg[1]); time.sleep(0.3)
        elif do == 'minimize':
            win32gui.ShowWindow(h, win32con.SW_MINIMIZE); time.sleep(0.5)
        elif do == 'move':
            l, t, r, b = win32gui.GetWindowRect(h)
            win32gui.SetWindowPos(h, 0, l + 120, t + 60, r - l, b - t, win32con.SWP_NOZORDER); time.sleep(0.4)
        elif do == 'mouse_click':
            l, t, r, b = win32gui.GetWindowRect(h)
            win32api.SetCursorPos((l + 900, t + 60))
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0); time.sleep(0.4)
        elif do == 'kill_oh':
            subprocess.run(['taskkill', '/F', '/IM', 'OHDemo.exe'], capture_output=True); time.sleep(0.3)
        elif do == 'set_stop':
            self.stop.set()

    def tidy(self):
        """Đưa OH về trạng thái đọc được (việc của người kiểm thử, không phải của RPA)."""
        try:
            if win32gui.IsIconic(self.eng.handle):
                win32gui.ShowWindow(self.eng.handle, win32con.SW_RESTORE); time.sleep(0.6)
            for _ in range(3):
                self.eng.clear_boxes(); time.sleep(0.2)
            self.eng.invalidate()
            self.eng.leave_edit()
        except Exception:
            pass

    def close(self):
        subprocess.run(['taskkill', '/F', '/IM', 'OHDemo.exe'], capture_output=True)


def fullname(cur):
    return ' '.join(x for x in (cur['first'], cur['middle'], cur['last']) if x)


def snap(eng):
    """Đọc lại toàn bộ hồ sơ: 5 hồ sơ mẫu và mọi hồ sơ NEW… đã được tạo."""
    out = {}
    for pid in DEMO_IDS + [f'NEW{n:06d}' for n in range(1, 9)]:
        try:
            out[pid] = K.readback(eng, pid)
        except Exception:
            if pid.startswith('DEMO'):
                out[pid] = None
            else:
                break
    return out


def fields(cur):
    return {k: cur[k] for k in ('title', 'first', 'middle', 'last', 'sex', 'dob', 'phone', 'nationality', 'addresses')}


def judge(after, base, intents):
    """Trả danh sách vi phạm bất biến. intents: các dòng có ý định; mỗi dòng: kind, truth, name, reported=(loại, thông báo)|None."""
    issues = []
    u = next((i for i in intents if i['kind'] == 'U'), None)
    for pid in DEMO_IDS:
        cur = after.get(pid)
        if cur is None:
            issues.append(f'S1 {pid}: không đọc lại được'); continue
        if fields(cur) == fields(base[pid]):
            continue
        if pid == 'DEMO0001' and u and not K.reconcile(cur, u['truth']):
            continue                                       # đã được cập nhật đúng theo Excel
        rep_u = u.get('reported') if u else None
        if pid == 'DEMO0001' and rep_u and rep_u[0] == 'ERROR' and 'DEMO0001' in rep_u[1]:
            continue                                       # dữ liệu lạ do người dùng gõ, RPA đã phát hiện và báo lỗi nêu rõ hồ sơ để kiểm tra tay
        diff = [k for k in fields(cur) if cur[k] != base[pid][k]]
        issues.append(f'S1 {pid} bị đổi ngoài ý muốn (trường: {", ".join(diff)}; SĐT OH="{cur["phone"]}", gốc="{base[pid]["phone"]}")')
    news = {pid: cur for pid, cur in after.items() if pid.startswith('NEW') and cur}
    claimed = set()
    for it in intents:
        rep = it.get('reported')
        ok = bool(rep) and rep[0] in SUCCESS
        if it['kind'] == 'U':
            bad = K.reconcile(after['DEMO0001'], it['truth']) if after.get('DEMO0001') else ['không đọc được']
            if ok and bad:
                issues.append('S2 RPA báo thành công nhưng DEMO0001 lệch Excel: ' + '; '.join(bad))
            continue
        same = [pid for pid, cur in news.items() if K.fold(fullname(cur)) == K.fold(it['name'])]
        claimed.update(same)
        if it['kind'] == 'BAD':
            if same:
                issues.append(f'S3 dòng có dữ liệu lỗi vẫn tạo hồ sơ {same}')
            continue
        if len(same) > 1:
            issues.append(f'S3 tạo trùng {len(same)} hồ sơ cho "{it["name"]}": {same}')
        if ok and not same:
            issues.append(f'S2 RPA báo thành công nhưng không có hồ sơ "{it["name"]}"')
        for pid in same[:1]:
            bad = K.reconcile(news[pid], it['truth'])
            if ok and bad:
                issues.append(f'S2 RPA báo thành công nhưng {pid} lệch Excel: ' + '; '.join(bad))
            if not ok and bad and it.get('need_flag') and (rep is None or (pid not in rep[1] and 'có thể đã tạo hồ sơ' not in rep[1])):
                issues.append(f'S4 hồ sơ nửa vời {pid} không được nêu trong thông báo của RPA')
    for pid in news:
        if pid not in claimed:
            issues.append(f'S3 hồ sơ ngoài ý định: {pid} "{fullname(news[pid])}"')
    return issues


# ---------------------------------------------------------------- kịch bản -----------------------------------------
def P(when, key, do, arg=None, nth=1):
    return dict(when=when, key=key, do=do, arg=arg, nth=nth)


SC = []
GI, GJ = 'I. Người dùng can thiệp khi RPA đang chạy', 'J. OH hoặc RPA bị ngắt/dừng giữa chừng'


def sc(id_, group, title, risk, kind, rows, plan, **kw):
    SC.append(dict(id=id_, group=group, title=title, risk=risk, kind=kind, rows=rows, plan=plan, **kw))


# --- I: dòng cập nhật DEMO0001 (U)
sc('I01', GI, 'Người dùng tìm hồ sơ khác ngay sau khi RPA tìm xong', 'Trang đổi từ danh sách sang hồ sơ khác trước khi RPA mở hồ sơ.', 'inproc', ['U'], [P('after', 'search', 'search_other')])
sc('I02', GI, 'Người dùng mở hồ sơ khác khi RPA vừa mở DEMO0001', 'RPA sắp bấm Edit nhưng màn hình đã là hồ sơ khác.', 'inproc', ['U'], [P('after', 'open_pid', 'search_other')])
sc('I03', GI, 'Người dùng mở hồ sơ khác ngay khi RPA bấm Edit', 'Cuộc đua giữa bấm Edit của RPA và tìm kiếm của người dùng.', 'inproc', ['U'], [P('after', 'click:edit-toggle', 'search_other')])
sc('I04', GI, 'Người dùng chuyển sang sửa hồ sơ khác (DEMO0002) sau khi RPA đọc xong DEMO0001', 'RPA điền dữ liệu của DEMO0001 vào form đang mở của người khác: nguy cơ ghi nhầm người.', 'inproc', ['U'], [P('after', 'read_edit', 'search_other_edit')])
sc('I05', GI, 'Người dùng gõ SĐT khác vào form trước khi RPA bấm Lưu', 'Dữ liệu người dùng gõ lẫn vào dữ liệu RPA rồi vẫn được lưu.', 'inproc', ['U'], [P('before', 'click:edit-save', 'type', ('edit-phone', '0111111111'))])
sc('I06', GI, 'Người dùng đổi họ trên form trước khi RPA bấm Lưu', 'Họ bị sửa thành giá trị lạ rồi vẫn được lưu.', 'inproc', ['U'], [P('before', 'click:edit-save', 'type', ('edit-local-first', 'Sai'))], no_c1=True)
sc('I07', GI, 'Người dùng bấm thoát Edit khi form đang có thay đổi dở', 'Hộp thoại "Bỏ các thay đổi?" hiện giữa chừng.', 'inproc', ['U'], [P('after', 'set_text:edit-phone', 'click', 'edit-toggle')])
sc('I08', GI, 'Người dùng bấm New Patient khi RPA sắp mở hồ sơ', 'Màn hình đổi sang khung tạo mới.', 'inproc', ['U'], [P('before', 'click:results-open', 'click', 'new-patient')])
sc('I09', GI, 'Người dùng đổi nội dung ô tìm kiếm thành PID', 'OH mở thẳng hồ sơ DEMO0001; RPA tưởng là "không có kết quả" nên có thể tạo trùng.', 'inproc', ['U'], [P('after', 'set_text:pid-search', 'set_search_text', 'DEMO0001')])
sc('I10', GI, 'Người dùng tìm hồ sơ khác ngay sau khi RPA bấm Lưu', 'Dòng trạng thái đổi trước khi RPA đọc "Đã lưu".', 'inproc', ['U'], [P('after', 'click:edit-save', 'search_other')])
sc('I11', GI, 'Người dùng tự mở khung địa chỉ trước khi RPA bấm "+"', 'Khung địa chỉ đã mở sẵn khi RPA bấm "+".', 'inproc', ['U'], [P('before', 'click:edit-add-address', 'click', 'edit-add-address')])
sc('I12', GI, 'Người dùng thu nhỏ cửa sổ OH giữa dòng', 'RPA không điều khiển được cửa sổ thu nhỏ.', 'inproc', ['U'], [P('after', 'click:edit-toggle', 'minimize')])
sc('I13', GI, 'Người dùng kéo di chuyển cửa sổ OH giữa dòng', 'Dời cửa sổ không được làm RPA sai.', 'inproc', ['U'], [P('after', 'open_pid', 'move')])
sc('I14', GI, 'Người dùng bấm chuột thật vào vùng trống của OH giữa dòng', 'Đổi tiêu điểm không được làm RPA sai.', 'inproc', ['U'], [P('after', 'read_edit', 'mouse_click')])
# --- I: dòng tạo mới (N)
sc('I21', GI, 'Người dùng tìm hồ sơ khác ngay sau khi RPA bấm New Patient', 'Khung tạo mới bị thay bằng hồ sơ khác khi RPA đang gõ tên.', 'inproc', ['N'], [P('after', 'click:new-patient', 'search_other')])
sc('I22', GI, 'Người dùng sửa Tên trong khung New Patient sau khi RPA điền', 'Hồ sơ mới có thể bị tạo với tên lạ.', 'inproc', ['N'], [P('after', 'set_text:new-last', 'type', ('new-last', 'Sai'))])
sc('I23', GI, 'Người dùng sửa năm sinh trong khung New Patient trước khi RPA bấm Lưu', 'Hồ sơ mới có thể bị tạo với năm sinh sai.', 'inproc', ['N'], [P('before', 'click:new-save', 'type', ('new-year', '1950'))])
sc('I24', GI, 'Người dùng tìm hồ sơ khác ngay sau khi hồ sơ mới được tạo', 'Hồ sơ mới đã tạo (chỉ có tên, năm sinh, SĐT) nhưng RPA mất trang Edit.', 'inproc', ['N'], [P('after', 'click:new-save', 'search_other')])
sc('I25', GI, 'Người dùng bấm thoát Edit trước khi RPA bấm Lưu (hồ sơ mới)', 'Hộp thoại "Bỏ các thay đổi?" làm mất phần bổ sung.', 'inproc', ['N'], [P('before', 'click:edit-save', 'click', 'edit-toggle')])
sc('I26', GI, 'Người dùng mở New Patient ngay sau khi hồ sơ mới được tạo', 'Trang Edit của hồ sơ mới bị che bởi khung tạo mới.', 'inproc', ['N'], [P('after', 'click:new-save', 'click', 'new-patient')])
sc('I27', GI, 'Người dùng tự bấm Save trong khung New Patient trước RPA', 'Hồ sơ được tạo hai lần (bởi người và bởi RPA)?', 'inproc', ['N'], [P('after', 'set_text:new-phone', 'click', 'new-save')])
sc('I28', GI, 'Người dùng thu nhỏ cửa sổ OH khi RPA đang điền khung New Patient', 'Dòng bị ngắt trước khi tạo hồ sơ.', 'inproc', ['N'], [P('after', 'set_text:new-first', 'minimize')])
# --- J: OH bị tắt
KO = [('U', 'after', 'search'), ('U', 'after', 'click:edit-toggle'), ('U', 'before', 'click:edit-save'), ('U', 'after', 'click:edit-save'),
      ('N', 'after', 'set_text:new-first'), ('N', 'after', 'click:new-save'), ('N', 'before', 'click:edit-save'), ('N', 'after', 'click:edit-save')]
for i, (k, when, key) in enumerate(KO, 1):
    sc(f'J{i:02d}', GJ, f'OH bị tắt: {"cập nhật" if k == "U" else "tạo mới"}, {when} {key}',
       'OH bị đóng ở đúng bước này; RPA không được báo thành công, không treo; mở lại OH rồi chạy lại phải đúng.', 'kill_oh', [k], [P(when, key, 'kill_oh')])
# --- J: RPA bị tắt (giết tiến trình) khi đang chạy danh sách 4 dòng: [dòng lỗi dữ liệu, người mới, dòng mục tiêu, người mới]
KR = [('U', 'after', 'search'), ('U', 'after', 'click:edit-toggle'), ('U', 'after', 'read_edit'), ('U', 'after', 'set_text:edit-phone'), ('U', 'before', 'click:edit-save'),
      ('U', 'after', 'click:edit-save'), ('N', 'after', 'click:new-patient'), ('N', 'after', 'set_text:new-last'), ('N', 'after', 'click:new-save'),
      ('N', 'after', 'read_edit'), ('N', 'after', 'set_text:edit-dob'), ('N', 'before', 'click:edit-save'), ('N', 'after', 'click:edit-save')]
for i, (k, when, key) in enumerate(KR, 11):
    sc(f'J{i}', GJ, f'RPA bị tắt đột ngột: {"cập nhật" if k == "U" else "tạo mới"}, {when} {key}',
       'Tiến trình RPA bị kết thúc ở đúng bước này khi đang chạy danh sách 4 dòng. Dòng đang dở, dòng lỗi trước đó và dòng sau phải được xử lý đúng.',
       'kill_rpa', ['BAD', 'N', k, 'N'], [P(when, key, 'kill_rpa')], target=2)
# --- J: người dùng bấm Dừng
for i, (k, when, key) in enumerate([('N', 'after', 'click:new-save'), ('N', 'after', 'set_text:edit-dob'), ('U', 'after', 'click:edit-toggle'), ('U', 'before', 'click:edit-save')], 24):
    sc(f'J{i}', GJ, f'Người dùng bấm Dừng: {"cập nhật" if k == "U" else "tạo mới"}, {when} {key}',
       'Cờ Dừng bật giữa dòng; dòng dở phải được nêu rõ và chạy lại phải hoàn tất.', 'inproc', [k], [P(when, key, 'set_stop')], use_stop=True)


# ---------------------------------------------------------------- chạy một ca -------------------------------------
def run_sub(cfg):
    cfgp = TMP / f'cfg_{cfg["tag"]}.json'
    cfgp.write_text(json.dumps(cfg, ensure_ascii=False), encoding='utf-8')
    outp = TMP / f'out_{cfg["tag"]}.txt'
    env = dict(os.environ, RPA_RUNTIME=str(TMP / ('rt_' + cfg['tag'].rstrip('ab'))), PYTHONIOENCODING='utf-8')
    if MODE == 'truoc':
        env['KT_SRC'] = str(HERE / '_ban_truoc_sua')
    with outp.open('w', encoding='utf-8') as f:
        p = subprocess.Popen([sys.executable, '-X', 'utf8', str(HERE / '_tien_trinh.py'), str(cfgp)], stdout=f, stderr=subprocess.STDOUT, env=env)
        try:
            code = p.wait(timeout=150)
        except subprocess.TimeoutExpired:
            p.kill(); code = 'treo >150s'
    res = {}
    for line in outp.read_text(encoding='utf-8', errors='replace').splitlines():
        if line.startswith('{'):
            d = json.loads(line)
            if d['tag'] == 'row':
                res[d['line']] = d['text']
    return code, res


def rep_of(text):
    if not text or text == 'Đang xử lý…':
        return None
    typ = ('CREATE' if text.startswith('Đã tạo') else 'UPDATE' if text.startswith('Đã cập nhật') else 'SAME' if text.startswith('Không đổi') else
           'MANUAL' if text.startswith('Cần điền tay') else 'ERROR')
    return typ, text


def run_case(s, holder):
    t0 = time.time()
    rows = [make_row(k) for k in s['rows']]
    tgt = rows[s.get('target', len(rows) - 1)]
    tag = s['id']
    xlsx, header = write_rows(rows, tag)
    plan = [dict(p, line=tgt['line']) for p in s['plan']]
    ctx = Ctx()
    if 'base' not in holder:
        holder['base'] = snap(ctx.eng)
        ctx.eng.leave_edit()
        log('Trạng thái gốc: ' + ', '.join(f'{k}={v["phone"] if v else None}' for k, v in holder['base'].items()))
    base = holder['base']
    notes, issues, summary = [], [], ''
    folder = TMP / f'f_{tag}'
    folder.mkdir(exist_ok=True)
    for old in folder.iterdir():
        old.unlink()
    try:
        if s['kind'] == 'inproc':
            hooks = Hooks(ctx.eng, plan, ctx.act)
            fn = (lambda r: ctx.eng.process(r, ctx.stop)) if s.get('use_stop') else ctx.eng.process
            typ, text = K.classify(fn, tgt['row'])
            tgt['reported'], tgt['need_flag'] = (typ, text), True
            summary = f'RPA báo {typ}: {text[:140]}'
            notes.append('Vết: ' + ' › '.join(x for x in hooks.trace if x.startswith('>>')))
            if hooks.errors:
                notes.append('Lỗi giả lập thao tác: ' + '; '.join(hooks.errors))
            if not all(q['done'] for q in hooks.plan):
                issues.append('LỖI HARNESS: bước chèn thao tác không xảy ra trong dòng này (ca không có hiệu lực)')
            ctx.tidy()
            issues += judge(snap(ctx.eng), base, [dict(tgt)])
        elif s['kind'] == 'kill_oh':
            Hooks(ctx.eng, plan, ctx.act)
            t1 = time.time()
            typ, text = K.classify(ctx.eng.process, tgt['row'])
            took = time.time() - t1
            summary = f'RPA báo {typ}: {text[:140]} ({took:.1f}s)'
            if typ in SUCCESS:
                issues.append('S2 OH đã bị tắt nhưng RPA vẫn báo thành công')
            if took > 45:
                issues.append(f'S2 RPA chờ quá lâu ({took:.0f}s) sau khi OH bị tắt')
            if 'OH' not in text:
                issues.append('S4 thông báo không nói rõ OH đã đóng')
            ctx.relaunch()
        else:  # kill_rpa
            code, res = run_sub(dict(tag=tag + 'a', xlsx=str(xlsx), lines=[r['line'] for r in rows], mode=MODE, plan=plan, folder=str(folder)))
            summary = f'Tiến trình RPA kết thúc (mã {code}); báo cáo trước khi bị tắt: ' + '; '.join(f'dòng {l}: {t[:45]}' for l, t in res.items())
            if code != 137:
                issues.append(f'LỖI HARNESS: tiến trình RPA không bị kết thúc ở bước đã định (mã {code})')
            ctx.tidy()
            for r in rows:
                r['reported'] = None if r is tgt else rep_of(res.get(r['line']))
                r['need_flag'] = False
            issues += judge(snap(ctx.eng), base, [dict(r) for r in rows])
            try:
                from rpa_tool import journal
                unfinished = journal.unfinished(TMP / ('rt_' + tag), xlsx.name)
                if tgt['line'] not in unfinished:
                    issues.append(f'S5 nhật ký không ghi nhận dòng {tgt["line"]} đang dở (nhật ký ghi: {sorted(unfinished)})')
            except ImportError:
                issues.append(f'S5 không có nhật ký tiến độ: dòng {tgt["line"]} đang dở không để lại dấu vết nào')
            errfile = folder / 'ds lỗi.xlsx'
            have = [c.value for c in load_workbook(errfile).active['A'][1:]] if errfile.exists() else []
            if rows[0]['line'] not in have:
                issues.append(f'S5 dòng lỗi dữ liệu {rows[0]["line"]} (đã xử lý xong trước khi tắt RPA) chưa có trong ds lỗi.xlsx (hiện: {have or "chưa có file"})')
        if s.get('no_c1'):
            raise SkipC1()
        # ---- C1: chạy lại khi không còn can thiệp
        if s['kind'] == 'kill_rpa':
            code2, res2 = run_sub(dict(tag=tag + 'b', xlsx=str(xlsx), lines=[r['line'] for r in rows], mode=MODE, plan=[], folder=str(folder)))
            for r in rows:
                r['reported'] = rep_of(res2.get(r['line']))
            summary += ' | chạy lại: ' + '; '.join(f'dòng {l}: {t[:35]}' for l, t in res2.items())
            ctx.eng.invalidate()
        else:
            ctx.eng = E.OhDemoRPA()
            typ2, text2 = K.classify(ctx.eng.process, tgt['row'])
            tgt['reported'] = (typ2, text2)
            summary += f' | chạy lại: {typ2} {text2[:60]}'
            if typ2 not in SUCCESS:
                issues.append(f'C1 chạy lại không thành công: {typ2} {text2[:100]}')
        after2 = snap(ctx.eng)
        for r in rows:
            r['need_flag'] = False
        for iss in judge(after2, base, [dict(r) for r in rows]):
            issues.append('C1 sau khi chạy lại: ' + iss)
        for r in rows:
            if r['kind'] == 'N':
                m = [p for p, c in after2.items() if p.startswith('NEW') and c and K.fold(fullname(c)) == K.fold(r['name'])]
                if len(m) != 1 or K.reconcile(after2[m[0]], r['truth']):
                    issues.append(f'C1 hồ sơ "{r["name"]}" chưa có đúng một bản khớp Excel sau khi chạy lại ({m})')
        if any(r['kind'] == 'U' for r in rows) and K.reconcile(after2['DEMO0001'], U_TRUTH):
            issues.append('C1 DEMO0001 chưa khớp Excel sau khi chạy lại')
    except SkipC1:
        notes.append('Không kiểm tra hồi phục tự động: hồ sơ đã bị lưu dữ liệu lạ do chính người dùng gõ, RPA đã báo lỗi nêu rõ PID để người sửa tay.')
    except Exception as exc:
        issues.append(f'LỖI HARNESS {type(exc).__name__}: {exc}')
    finally:
        ctx.close()
    uniq = list(dict.fromkeys(issues))
    return dict(id=s['id'], group=s['group'], title=s['title'], risk=s['risk'], expected='SAFE', kw='',
                pre='; '.join(f'{p["when"]} {p["key"]} → {p["do"]}' + (f' {p["arg"]}' if p.get('arg') else '') for p in s['plan']),
                sev='Cao', note=' '.join(notes), raw={}, truth=None, line=tgt['line'], pid='', actual=summary,
                actual_type='SAFE' if not uniq else 'UNSAFE', before=None, after=None, recon=uniq,
                verdict='ĐẠT' if not uniq else 'KHÔNG ĐẠT', why='; '.join(uniq), dur=round(time.time() - t0, 1), rerun_of='', side=False)


def main():
    if not os.environ.get('KT_ONLY'):
        LOGF.write_text('', encoding='utf-8')
    started = datetime.now()
    log(f'Bắt đầu nhóm I+J, chế độ {MODE}, {len(SC)} ca')
    holder, out = {}, []
    only = os.environ.get('KT_ONLY')
    for s in SC:
        if only and s['id'] not in only.split(','):
            continue
        r = run_case(s, holder)
        out.append(r)
        log(f'{r["id"]} {r["verdict"]} | {r["actual"][:110]} | {r["why"][:260]}')
    outfile = HERE / f'ket_qua_ij_{MODE}.json'
    if only and outfile.exists():                           # chạy lại vài ca: gộp vào kết quả cũ
        old = {c['id']: c for c in json.loads(outfile.read_text(encoding='utf-8'))['cases']}
        old.update({c['id']: c for c in out})
        out = [old[k] for k in sorted(old, key=lambda x: (x[0], int(x[1:])))]
    data = dict(meta=dict(mode=MODE, started=started.isoformat(timespec='seconds'), finished=datetime.now().isoformat(timespec='seconds')), cases=out)
    (HERE / f'ket_qua_ij_{MODE}.json').write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding='utf-8')
    log(f'Xong: {len(out)} ca, ĐẠT {sum(c["verdict"] == "ĐẠT" for c in out)}, KHÔNG ĐẠT {sum(c["verdict"] == "KHÔNG ĐẠT" for c in out)}')


if __name__ == '__main__':
    main()
