"""Kiểm thử RPA_OHDemo: sinh dữ liệu (hợp lệ, sai, thiếu), chạy thật trên OHDemo.exe, đối soát từng hồ sơ, ghi toàn bộ kết quả.

Chạy:  python kiem_thu\\chay_kiem_thu.py            (mất khoảng 40 phút; cửa sổ OH sẽ nhảy lên trước khi RPA điền)
Kết quả: kiem_thu/ket_qua.json, kiem_thu/du_lieu_kiem_thu.xlsx; báo cáo .md sinh bằng kiem_thu/viet_bao_cao.py.
Mỗi ca có mong đợi viết TRƯỚC khi chạy; kết quả "ĐẠT" chỉ khi thực tế khớp mong đợi và đối soát lại trong OH khớp dữ liệu gốc.
"""
import hashlib
import json
import os
import platform
import random
import subprocess
import sys
import tempfile
import time
import unicodedata
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SRC = Path(os.environ.get('KT_SRC') or ROOT)      # thư mục chứa rpa_tool/ và shared/ cần kiểm thử (mặc định: bản hiện tại)
sys.path.insert(0, str(SRC))
sys.stdout.reconfigure(encoding='utf-8')
import pythoncom
from openpyxl import Workbook
from shared.excel import ERROR_FILE, find_daily_file, read_daily, write_errors
from shared.identity import ReviewRequired
from rpa_tool import ohdemo_engine as E

OH_EXE = ROOT.parent / 'OH_Demo' / 'OHDemo.exe'
HEADER = ['Patient ID', 'Title', 'Patient Given Name', 'Patient Middle Name', 'Patient Last Name', 'Date Of Birth', 'Sex',
          'Patient Address', 'Business Phone Number', 'Nationality', 'Policy Code', 'Policy Name', 'Package Code', 'Package Name',
          'Visit Date Time', 'Patient Work Queue', 'Attending Doctor Number', 'National ID', 'Passport Number',
          'Requesting Cost Centre', 'Pricing Class', 'Mã ca kiểm thử']
LOG = HERE / 'tien_do.log'


def log(text):
    line = f'{datetime.now():%H:%M:%S} {text}'
    print(line, flush=True)
    with LOG.open('a', encoding='utf-8') as f:
        f.write(line + '\n')


@dataclass
class Case:
    id: str
    group: str
    title: str
    risk: str
    raw: dict                       # giá trị thô trong Excel (str, datetime, int...) theo khóa: title,last,middle,given,dob,sex,addr,phone,nat,cccd
    expected: str                   # CREATE | UPDATE | SAME | ERROR | MANUAL
    kw: str = ''                    # từ khóa phải có trong thông báo (ERROR / MANUAL)
    truth: dict | None = None       # giá trị đúng phải thấy trong OH sau khi chạy (title, first, middle, last, sex, dob, phone, nat, addr)
    side: bool = False              # kiểm tra không tạo thêm hồ sơ (dùng cho ca mong đợi ERROR)
    pre: str = ''                   # tiền điều kiện
    sev: str = 'Trung bình'         # mức nghiêm trọng nếu ca này không đạt
    note: str = ''
    rerun_of: str = ''              # ca chạy lại: dùng lại dữ liệu của ca khác
    # --- kết quả ---
    line: int = 0
    pid: str = ''
    actual: str = ''
    actual_type: str = ''
    before: int | None = None
    after: int | None = None
    recon: list = field(default_factory=list)
    recon_done: bool = False
    verdict: str = ''
    why: str = ''
    dur: float = 0.0


# ======================================================================================================
# SINH DỮ LIỆU
# ======================================================================================================
HO = ['Nguyễn', 'Trần', 'Lê', 'Phạm', 'Hoàng', 'Huỳnh', 'Phan', 'Vũ', 'Võ', 'Đặng', 'Bùi', 'Đỗ', 'Hồ', 'Ngô', 'Dương',
      'Lý', 'Chử', 'Đinh', 'Trịnh', 'Đoàn', 'Lương', 'Tạ', 'Cao', 'Từ', 'Quản']
DEM_NAM = ['Văn', 'Hữu', 'Minh', 'Quang', 'Đức', 'Thanh', 'Xuân', 'Tiến', 'Gia', 'Công', 'Quốc', 'Ngọc']
DEM_NU = ['Thị', 'Ngọc', 'Thu', 'Thanh', 'Hồng', 'Kim', 'Bích', 'Diệu', 'Phương', 'Thùy']
TEN_NAM = ['An', 'Bình', 'Cường', 'Dũng', 'Hải', 'Hiếu', 'Khánh', 'Long', 'Nam', 'Phúc', 'Quân', 'Sơn', 'Tuấn', 'Việt', 'Đạt',
           'Huy', 'Khoa', 'Thành', 'Trung', 'Tùng', 'Kiên', 'Lâm', 'Nghĩa', 'Phát']
TEN_NU = ['Anh', 'Châu', 'Dung', 'Hà', 'Hạnh', 'Lan', 'Linh', 'Mai', 'Ngân', 'Nhi', 'Oanh', 'Phương', 'Thảo', 'Trang', 'Vy',
          'Yến', 'Hương', 'Thúy', 'Quỳnh', 'Ánh', 'Diễm', 'Giang', 'Hồng', 'Tâm']
TINH = ['Hà Nội', 'Hưng Yên', 'Hải Phòng', 'Nam Định', 'Thái Bình', 'Bắc Ninh', 'Ninh Bình', 'Đà Nẵng', 'Thành phố Hồ Chí Minh', 'Đồng Nai']
PHUONG = ['Phường Tân Hiệp', 'Phường Láng Hạ', 'Phường Đông Hải', 'Phường Lê Lợi', 'Xã Tây Phương', 'Xã Kiều Phú', 'Phường Mới']
DUONG = ['Láng Hạ', 'Nguyễn Trãi', 'Lê Lợi', 'Trần Phú', 'Hoàng Diệu', 'Số 3', 'Điện Biên Phủ', 'Phạm Văn Đồng']

rng = random.Random(20261119)
USED_NAMES, USED_PHONES = set(), set()


def unique_phone():
    while True:
        p = '09' + ''.join(str(rng.randint(0, 9)) for _ in range(8))
        if p not in USED_PHONES:
            USED_PHONES.add(p)
            return p


def person(i, *, year_range=(1950, 2016), force_sex=None):
    """Một người hợp lệ, duy nhất theo (họ tên, năm sinh) và SĐT. Trả (raw, truth)."""
    while True:
        sex = force_sex or rng.choice(['Nam', 'Nữ'])
        last = rng.choice(HO)
        mid = ' '.join(rng.choice(DEM_NAM if sex == 'Nam' else DEM_NU) for _ in range(rng.choice([0, 1, 1, 1, 2])))
        given = rng.choice(TEN_NAM if sex == 'Nam' else TEN_NU)
        d = datetime(rng.randint(*year_range), rng.randint(1, 12), rng.randint(1, 28))
        key = (' '.join(x for x in (last, mid, given) if x).lower(), d.year)
        if key not in USED_NAMES:
            USED_NAMES.add(key)
            break
    old = (datetime.now().year - d.year) < 14
    title = 'Bé' if old else rng.choice(['Ông', 'Anh'] if sex == 'Nam' else ['Bà', 'Chị'])
    form = rng.random()
    dob_raw = d if form < .10 else d.strftime('%Y-%m-%d') if form < .15 else d.strftime('%d%m%Y') if form < .20 else d.strftime('%d/%m/%Y')
    r = rng.random()
    if r < .65:
        addr = f'Số {rng.randint(1, 200)} Đường {rng.choice(DUONG)}, {rng.choice(PHUONG)}, {rng.choice(TINH)}'
    elif r < .90:
        addr = f'Thôn {rng.choice("ABCDEFG")}, Xã {rng.choice("HIKLMN")}, Tỉnh {rng.choice(TINH)}'
    else:
        addr = f'{rng.randint(1, 99)} {rng.choice(DUONG)}, {rng.choice(TINH)}'
    nat = 'Việt Nam' if rng.random() < .85 else ''
    phone = unique_phone()
    raw = dict(title=title, last=last, middle=mid, given=given, dob=dob_raw, sex=sex, addr=addr, phone=phone, nat=nat,
               cccd=f'0{rng.randint(10, 99)}{rng.randint(10**8, 10**9 - 1)}')
    truth = dict(title=title, first=last, middle=mid, last=given, sex=sex, dob=d.strftime('%d/%m/%Y'), phone=phone, nat=nat,
                 addr=', '.join(p.strip() for p in addr.split(',')))
    return raw, truth


def clone(raw, truth, **over):
    r, t = dict(raw), dict(truth)
    r.update({k: v for k, v in over.items() if k in r})
    mapping = dict(title='title', last='first', middle='middle', given='last', sex='sex', phone='phone', nat='nat')
    for k, v in over.items():
        if k in mapping and isinstance(v, str):
            t[mapping[k]] = v.strip()
    if 'addr' in over:
        t['addr'] = ', '.join(p.strip() for p in over['addr'].split(',') if p.strip())
    return r, t


def build_cases():
    cases = []

    def add(**kw):
        c = Case(**kw)
        cases.append(c)
        return c

    # ---- A. Người mới hợp lệ (đa dạng) -----------------------------------------------------------
    for i in range(1, int(os.environ.get('KT_A', 80)) + 1):
        raw, truth = person(i)
        add(id=f'A{i:03d}', group='A. Người mới hợp lệ (sinh tự động)', title='Tạo mới người chưa có hồ sơ',
            risk='Luồng chính: tìm không thấy → tạo → điền đủ trường → lưu. Đa dạng tên có dấu, định dạng ngày, địa chỉ 2-3 phần, quốc tịch có/không.',
            raw=raw, expected='CREATE', truth=truth, sev='Cao')

    # ---- H. Khối lượng: thêm 100 người nữa ---------------------------------------------------------
    for i in range(1, int(os.environ.get('KT_H', 100)) + 1):
        raw, truth = person(1000 + i)
        add(id=f'H{i:03d}', group='H. Khối lượng (sinh tự động)', title='Tạo mới (khối lượng lớn)',
            risk='Ổn định khi chạy dài liên tục: không rơi dòng, không lỗi ngẫu nhiên, không chậm dần.',
            raw=raw, expected='CREATE', truth=truth, sev='Cao')

    # ---- C. Cập nhật người đã có -------------------------------------------------------------------
    def base(n, **over):
        raw, truth = person(2000 + n, year_range=(1985, 1990))
        raw.update(addr=f'Số {n} Đường A, Phường B, Hà Nội', nat=over.pop('nat', 'Việt Nam'))
        truth.update(addr=f'Số {n} Đường A, Phường B, Hà Nội', nat=raw['nat'])
        raw.update(over)
        truth.update({k: v for k, v in over.items() if k in truth})
        return raw, truth

    def upd(n, title, risk, mutate, expected, **kw):
        raw, truth = base(n)
        add(id=f'C{n:02d}S', group='C. Cập nhật (bước chuẩn bị: tạo người gốc)', title=f'Chuẩn bị cho C{n:02d}', risk='Tạo người gốc để cập nhật.',
            raw=raw, expected='CREATE', truth=truth, sev='Cao')
        raw2, truth2 = mutate(dict(raw), dict(truth))
        add(id=f'C{n:02d}', group='C. Cập nhật người đã có', title=title, risk=risk, raw=raw2, expected=expected, truth=truth2, **kw)

    new_phone_c1 = unique_phone()
    upd(1, 'Đổi số điện thoại', 'Trường điện thoại thay đổi phải được cập nhật.',
        lambda r, t: (dict(r, phone=new_phone_c1), dict(t, phone=new_phone_c1)), 'UPDATE')

    raw, truth = base(2)
    year = truth['dob'][-4:]
    add(id='C02S', group='C. Cập nhật (bước chuẩn bị: tạo người gốc)', title='Chuẩn bị cho C02', risk='Tạo người gốc để cập nhật.', raw=dict(raw, dob=f'10/05/{year}'),
        expected='CREATE', truth=dict(truth, dob=f'10/05/{year}'), sev='Cao')
    add(id='C02', group='C. Cập nhật người đã có', title='Cùng tên và năm sinh nhưng khác ngày/tháng (10/05 → 20/05)', risk='Có thể là người khác hoặc nhập sai ngày: không được tự ghi đè ngày sinh của hồ sơ cũ, cũng không tạo người mới; chuyển người duyệt.',
        raw=dict(raw, dob=f'20/05/{year}'), expected='ERROR', kw='khác ngày/tháng sinh', side=True, sev='Cao',
        note='Đổi theo yêu cầu: trước đây ca này mong đợi UPDATE (ghi đè ngày sinh); nay RPA dừng để người duyệt quyết định.')

    upd(3, 'Thêm địa chỉ mới', 'Địa chỉ mới được thêm vào danh sách (OH giữ cả địa chỉ cũ).',
        lambda r, t: (dict(r, addr='Số 99 Đường Mới, Phường Mới, Đà Nẵng'), dict(t, addr='Số 99 Đường Mới, Phường Mới, Đà Nẵng')), 'UPDATE')
    upd(4, 'Địa chỉ giống hệt cũ', 'Không được thêm địa chỉ trùng; kết quả phải là Không đổi.', lambda r, t: (dict(r), dict(t)), 'SAME')
    upd(5, 'Đổi Title Ông → Anh', 'Danh mục Title.', lambda r, t: (dict(r, title='Anh'), dict(t, title='Anh')), 'UPDATE')
    upd(6, 'Họ tên viết HOA toàn bộ', 'Khớp người cũ theo tên không phân biệt hoa/thường; Excel mới nhất ghi đè cách viết.',
        lambda r, t: (dict(r, last=r['last'].upper(), middle=r['middle'].upper(), given=r['given'].upper()),
                      dict(t, first=r['last'].upper(), middle=r['middle'].upper(), last=r['given'].upper())), 'UPDATE')
    upd(7, 'Họ tên viết thường toàn bộ', 'Như C06 với chữ thường.',
        lambda r, t: (dict(r, last=r['last'].lower(), middle=r['middle'].lower(), given=r['given'].lower()),
                      dict(t, first=r['last'].lower(), middle=r['middle'].lower(), last=r['given'].lower())), 'UPDATE')
    upd(8, 'Họ tên dạng Unicode tổ hợp (NFD)', 'Cùng một người nhưng mã hóa chữ có dấu khác (hay gặp khi dán từ nguồn khác). Mong đợi: nhận ra là cùng người và KHÔNG coi là thay đổi.',
        lambda r, t: (dict(r, last=unicodedata.normalize('NFD', r['last']), middle=unicodedata.normalize('NFD', r['middle']), given=unicodedata.normalize('NFD', r['given'])), dict(t)), 'SAME',
        sev='Thấp', note='Nếu thực tế là UPDATE: RPA ghi đè lại đúng chữ đó dưới dạng mã hóa khác (không sai nội dung nhưng là thay đổi thừa).')
    upd(9, 'Khoảng trắng thừa đầu/cuối ở họ tên', 'Khoảng trắng thừa trong Excel phải được loại bỏ, không tạo người mới.',
        lambda r, t: (dict(r, last=' ' + r['last'] + ' ', given='  ' + r['given']), dict(t)), 'SAME', sev='Thấp')
    upd(10, 'Thêm quốc tịch cho người chưa có', 'Điền thêm trường còn trống.', lambda r, t: (dict(r, nat='Việt Nam'), dict(t, nat='Việt Nam')), 'UPDATE')
    cases[-2].raw['nat'] = ''
    cases[-2].truth['nat'] = ''
    upd(11, 'Đổi nhiều trường cùng lúc (SĐT + địa chỉ + Title)', 'Nhiều thay đổi trong một lần lưu.',
        lambda r, t: (dict(r, phone='0977000011', addr='Số 5 Đường E, Phường F, Hải Phòng', title='Anh'), dict(t, phone='0977000011', addr='Số 5 Đường E, Phường F, Hải Phòng', title='Anh')), 'UPDATE')
    upd(12, 'Đổi giới tính Nam → Nữ', 'Trường giới tính và hộp chọn.', lambda r, t: (dict(r, sex='Nữ', title='Bà'), dict(t, sex='Nữ', title='Bà')), 'UPDATE')
    upd(13, 'Xóa trống số điện thoại', 'Thiếu SĐT phải bị chặn, hồ sơ cũ giữ nguyên.', lambda r, t: (dict(r, phone=''), dict(t)), 'ERROR', kw='Số điện thoại', sev='Cao')
    cases[-1].truth = None
    upd(14, 'Địa chỉ để trống khi cập nhật', 'Ô Excel trống không được xóa địa chỉ đã có.', lambda r, t: (dict(r, addr=''), dict(t)), 'SAME')
    upd(15, 'Sửa tên đệm (thêm 1 từ)', 'Quy tắc khớp theo họ tên đầy đủ: tên đệm khác nghĩa là người khác → tạo hồ sơ mới. Rủi ro: tạo trùng người nếu Excel chỉ sửa chính tả.',
        lambda r, t: (dict(r, middle=(r['middle'] + ' Hữu').strip(), phone=unique_phone()), dict(t, middle=(t['middle'] + ' Hữu').strip())), 'CREATE', sev='Cao',
        note='Quan sát: hành vi theo thiết kế, ghi nhận để người dùng quyết định có chấp nhận không.')
    cases[-1].truth['phone'] = cases[-1].raw['phone']

    # ---- D. Trùng lặp / nhập nhằng ------------------------------------------------------------------
    add(id='D01', group='D. Trùng lặp và nhập nhằng', title='Hai hồ sơ có sẵn cùng họ tên và năm sinh', risk='Không đoán: phải dừng và báo người chọn tay, không sửa nhầm hồ sơ nào.',
        pre='Tạo trước 2 hồ sơ "Hồ Thanh Tùng" sinh 1990, SĐT khác nhau.', raw=dict(title='Ông', last='Hồ', middle='Thanh', given='Tùng', dob='05/06/1990', sex='Nam', addr='Số 1 Đường A, Phường B, Hà Nội', phone='0911000003', nat='Việt Nam', cccd='079090000003'),
        expected='ERROR', kw='cùng tên và năm sinh', side=True, sev='Cao')
    add(id='D02', group='D. Trùng lặp và nhập nhằng', title='Cùng họ tên với người có sẵn nhưng khác năm sinh', risk='Hai người khác nhau trùng tên phải được tạo riêng, không ghi đè người cũ.',
        pre='Có sẵn DEMO0001/0004/0005 "Nguyễn Văn Mẫu" sinh 1980/1992/1975.', raw=dict(title='Ông', last='Nguyễn', middle='Văn', given='Mẫu', dob='09/09/1999', sex='Nam', addr='Số 7 Đường G, Phường H, Hà Nội', phone='0922000002', nat='Việt Nam', cccd='079099000002'),
        expected='CREATE', truth=dict(title='Ông', first='Nguyễn', middle='Văn', last='Mẫu', sex='Nam', dob='09/09/1999', phone='0922000002', nat='Việt Nam', addr='Số 7 Đường G, Phường H, Hà Nội'), sev='Cao')
    add(id='D03', group='D. Trùng lặp và nhập nhằng', title='Cùng họ tên và SĐT với người có sẵn nhưng khác năm sinh', risk='Nghi trùng người (nhập sai năm sinh): không tạo mới, báo kiểm tra tay.',
        pre='DEMO0001 "Nguyễn Văn Mẫu" SĐT 0900000001.', raw=dict(title='Ông', last='Nguyễn', middle='Văn', given='Mẫu', dob='01/01/1970', sex='Nam', addr='Số 8 Đường K, Phường L, Hà Nội', phone='0900000001', nat='Việt Nam', cccd='079070000003'),
        expected='ERROR', kw='Trùng tên và số điện thoại', side=True, sev='Cao')
    add(id='D04', group='D. Trùng lặp và nhập nhằng', title='Tên là phần đầu của tên người khác ("Nguyễn Văn An" so với "Nguyễn Văn Anh")', risk='Ô tìm của OH tìm theo "chứa"; RPA phải lọc đúng tên, không cập nhật nhầm người tên dài hơn.',
        pre='Tạo trước hồ sơ "Nguyễn Văn Anh" sinh 1990.', raw=dict(title='Ông', last='Nguyễn', middle='Văn', given='An', dob='11/11/1990', sex='Nam', addr='Số 9 Đường M, Phường N, Hà Nội', phone='0933000004', nat='Việt Nam', cccd='079090000004'),
        expected='CREATE', truth=dict(title='Ông', first='Nguyễn', middle='Văn', last='An', sex='Nam', dob='11/11/1990', phone='0933000004', nat='Việt Nam', addr='Số 9 Đường M, Phường N, Hà Nội'), sev='Cao')
    raw, truth = person(3000, year_range=(1970, 1980))
    add(id='D05A', group='D. Trùng lặp và nhập nhằng', title='Cùng một người xuất hiện 2 lần trong Excel (lần 1)', risk='Lần 1 tạo hồ sơ.', raw=raw, expected='CREATE', truth=truth, sev='Cao')
    add(id='D05B', group='D. Trùng lặp và nhập nhằng', title='Cùng một người xuất hiện 2 lần trong Excel (lần 2, giống hệt)', risk='Lần 2 không được tạo trùng.', raw=dict(raw), expected='SAME', truth=truth, sev='Cao')
    raw, truth = person(3001, year_range=(1970, 1980))
    add(id='D06A', group='D. Trùng lặp và nhập nhằng', title='Người xuất hiện 2 lần, lần 2 khác SĐT (lần 1)', risk='Lần 1 tạo hồ sơ.', raw=raw, expected='CREATE', truth=truth, sev='Cao')
    new_phone = unique_phone()
    add(id='D06B', group='D. Trùng lặp và nhập nhằng', title='Người xuất hiện 2 lần, lần 2 khác SĐT (lần 2)', risk='Lần 2 phải cập nhật SĐT, không tạo người mới.', raw=dict(raw, phone=new_phone), expected='UPDATE', truth=dict(truth, phone=new_phone), sev='Cao')
    add(id='D07', group='D. Trùng lặp và nhập nhằng', title='Người có sẵn trong OH, đổi SĐT', risk='Cập nhật hồ sơ có sẵn từ trước khi chạy RPA.', pre='DEMO0004 "Nguyễn Văn Mẫu" 03/09/1992.',
        raw=dict(title='Ông', last='Nguyễn', middle='Văn', given='Mẫu', dob='03/09/1992', sex='Nam', addr='Thôn A, Xã B, Tỉnh Demo', phone='0944000007', nat='Việt Nam', cccd='079092000007'),
        expected='UPDATE', truth=dict(title='Ông', first='Nguyễn', middle='Văn', last='Mẫu', sex='Nam', dob='03/09/1992', phone='0944000007', nat='Việt Nam', addr='Thôn A, Xã B, Tỉnh Demo'), sev='Cao')
    add(id='D08', group='D. Trùng lặp và nhập nhằng', title='Cùng người, Excel viết không dấu ("Nguyen Van Mau")', risk='Khớp theo tên không dấu nhận ra DEMO0005; nhưng Excel mới nhất ghi đè → tên trong OH bị đổi thành không dấu.',
        pre='DEMO0005 "Nguyễn Văn Mẫu" 12/12/1975.', raw=dict(title='Ông', last='Nguyen', middle='Van', given='Mau', dob='12/12/1975', sex='Nam', addr='5 Đường C, Phường D, Thành phố Demo', phone='0900000005', nat='Việt Nam', cccd='079075000008'),
        expected='UPDATE', truth=dict(title='Ông', first='Nguyen', middle='Van', last='Mau', sex='Nam', dob='12/12/1975', phone='0900000005', nat='Việt Nam', addr='5 Đường C, Phường D, Thành phố Demo'), sev='Cao',
        note='Quan sát: tên trong OH có dấu bị ghi đè thành tên không dấu. Nên cân nhắc không ghi đè tên khi chỉ khác dấu.')
    add(id='D09', group='D. Trùng lặp và nhập nhằng', title='Hồ sơ có sẵn cùng họ tên và năm sinh, khác ngày/tháng sinh', risk='Không ghi đè ngày sinh của DEMO0004 và không tạo hồ sơ thứ hai: chuyển người duyệt.',
        pre='DEMO0004 "Nguyễn Văn Mẫu" 03/09/1992.', raw=dict(title='Ông', last='Nguyễn', middle='Văn', given='Mẫu', dob='15/09/1992', sex='Nam', addr='Thôn A, Xã B, Tỉnh Demo', phone='0944000009', nat='Việt Nam', cccd='079092000009'),
        expected='ERROR', kw='khác ngày/tháng sinh', side=True, sev='Cao')

    # ---- E. Dữ liệu sai / lỗi / thiếu ----------------------------------------------------------------
    def e(id_, title, risk, over, expected, kw='', sev='Trung bình', note='', truth_over=None, side=None, ok_truth=False):
        raw, truth = person(4000 + len(cases), year_range=(1975, 1995))
        raw.update(over)
        t = None
        if expected in ('CREATE', 'UPDATE', 'SAME', 'MANUAL'):
            t = dict(truth)
            if 'last' in over: t['first'] = str(over['last']).strip()
            if 'middle' in over: t['middle'] = str(over['middle']).strip()
            if 'given' in over: t['last'] = str(over['given']).strip()
            if 'phone' in over and isinstance(over['phone'], str): t['phone'] = ''.join(ch for ch in over['phone'] if ch.isdigit())
            if 'sex' in over: t['sex'] = over['sex']
            if 'title' in over: t['title'] = over['title']
            if 'nat' in over: t['nat'] = over['nat']
            if 'addr' in over: t['addr'] = ', '.join(p.strip() for p in str(over['addr']).split(',') if p.strip())
            if truth_over: t.update(truth_over)
        add(id=id_, group='E. Dữ liệu sai, lỗi, thiếu', title=title, risk=risk, raw=raw, expected=expected, kw=kw, truth=t,
            side=(expected == 'ERROR') if side is None else side, sev=sev, note=note)

    # -- tên --
    e('E01', 'Thiếu họ', 'Không được tạo hồ sơ thiếu họ.', dict(last=''), 'ERROR', 'họ hoặc tên', 'Cao')
    e('E02', 'Thiếu tên (Given)', 'Không được tạo hồ sơ thiếu tên.', dict(given=''), 'ERROR', 'họ hoặc tên', 'Cao')
    e('E03', 'Thiếu cả họ và tên', 'Chỉ còn tên đệm.', dict(last='', given=''), 'ERROR', 'họ hoặc tên', 'Cao')
    e('E04', 'Họ chỉ gồm khoảng trắng', 'Khoảng trắng phải coi là trống.', dict(last='   '), 'ERROR', 'họ hoặc tên', 'Cao')
    e('E05', 'Thiếu tên đệm', 'Tên đệm không bắt buộc.', dict(middle=''), 'CREATE', sev='Cao')
    e('E06', 'Tên có chữ số ("An2")', 'Tên chứa số là dữ liệu sai, không nên nhập thầm lặng vào OH.', dict(given='An2'), 'ERROR', 'tên', 'Trung bình')
    e('E07', 'Tên chứa emoji', 'Ký tự ngoài chữ cái.', dict(given='Nam😀'), 'ERROR', 'tên', 'Trung bình')
    e('E08', 'Tên chứa mã giống HTML/script', 'Chuỗi như <script> không được đưa vào hồ sơ.', dict(given='<script>x</script>'), 'ERROR', 'tên', 'Trung bình')
    e('E09', 'Tên chứa dấu nháy và dấu gạch ("O\'Brien-Lê")', 'Ký tự đặc biệt thường gặp ở tên nước ngoài.', dict(given="O'Brien-Lê"), 'CREATE', sev='Thấp', note='Quan sát: tên có dấu nháy/gạch nối là hợp lệ.')
    e('E10', 'Họ rất dài (80 ký tự)', 'Giới hạn độ dài của ô.', dict(last='Nguyễn' * 13), 'CREATE', sev='Thấp', note='Quan sát độ dài chấp nhận được.')
    # -- giới tính --
    e('E11', 'Giới tính trống', 'Thiếu giới tính phải bị chặn.', dict(sex=''), 'ERROR', 'Giới tính', 'Cao')
    e('E12', 'Giới tính viết tiếng Anh ("Male")', 'Giá trị ngoài danh mục.', dict(sex='Male'), 'ERROR', 'Giới tính', 'Trung bình')
    e('E13', 'Giới tính viết thường ("nam")', 'Lỗi gõ phổ biến; nên chấp nhận.', dict(sex='nam', title='Ông'), 'CREATE', sev='Thấp', truth_over=dict(sex='Nam'), note='Mong đợi tiêu chí thực tế: chuẩn hóa chữ hoa/thường.')
    e('E14', 'Giới tính viết HOA ("NAM")', 'Như E13.', dict(sex='NAM', title='Ông'), 'CREATE', sev='Thấp', truth_over=dict(sex='Nam'))
    e('E15', 'Giới tính "Nữ" dạng Unicode tổ hợp', 'Cùng chữ nhưng khác mã hóa.', dict(sex=unicodedata.normalize('NFD', 'Nữ'), title='Bà'), 'CREATE', sev='Thấp', truth_over=dict(sex='Nữ'))
    e('E16', 'Giới tính có khoảng trắng ("Nam ")', 'Khoảng trắng thừa phải được cắt.', dict(sex='Nam ', title='Ông'), 'CREATE', sev='Thấp', truth_over=dict(sex='Nam'))
    e('E17', 'Giới tính "Khác"', 'Giá trị hợp lệ thứ ba.', dict(sex='Khác', title=''), 'CREATE', sev='Thấp')
    # -- ngày sinh --
    e('E18', 'Ngày sinh trống', 'Thiếu ngày sinh phải bị chặn.', dict(dob=''), 'ERROR', 'Ngày sinh', 'Cao')
    e('E19', 'Ngày sinh không tồn tại (31/02/2000)', 'Ngày sai lịch.', dict(dob='31/02/2000'), 'ERROR', 'Ngày sinh', 'Cao')
    e('E20', 'Ngày sinh là chữ ("abc")', 'Dữ liệu rác.', dict(dob='abc'), 'ERROR', 'Ngày sinh', 'Cao')
    e('E21', 'Ngày sinh dạng gạch ngang (15-03-1985)', 'Định dạng khác thường gặp.', dict(dob='15-03-1985'), 'CREATE', sev='Thấp', truth_over=dict(dob='15/03/1985'),
      note='Mong đợi tiêu chí thực tế: chấp nhận định dạng dd-mm-yyyy.')
    e('E22', 'Chỉ có năm sinh ("1985")', 'Thiếu ngày/tháng; OH cần ngày đủ ở trang Edit.', dict(dob='1985'), 'ERROR', 'Ngày sinh', 'Trung bình')
    e('E23', 'Ngày sinh ở tương lai (01/01/2099)', 'Ngày vô lý phải bị chặn thay vì nhập thầm lặng.', dict(dob='01/01/2099'), 'ERROR', 'Ngày sinh', 'Cao')
    e('E24', 'Ngày sinh quá xa (01/01/1850)', 'Tuổi trên 120.', dict(dob='01/01/1850'), 'ERROR', 'Ngày sinh', 'Trung bình')
    e('E25', 'Ngày sinh không có số 0 đầu (5/3/1985)', 'Định dạng d/m/yyyy.', dict(dob='5/3/1985'), 'CREATE', sev='Thấp', truth_over=dict(dob='05/03/1985'))
    e('E26', 'Ngày sinh là ngày hôm nay (trẻ sơ sinh)', 'Biên: tuổi 0.', dict(dob=datetime.now().replace(hour=0, minute=0, second=0, microsecond=0), title='Bé'), 'CREATE', sev='Thấp',
      truth_over=dict(dob=datetime.now().strftime('%d/%m/%Y')))
    # -- số điện thoại --
    e('E27', 'SĐT trống', 'Thiếu SĐT phải bị chặn.', dict(phone=''), 'ERROR', 'Số điện thoại', 'Cao')
    e('E28', 'SĐT quá ngắn ("123")', 'Dưới 8 chữ số.', dict(phone='123'), 'ERROR', 'Số điện thoại', 'Cao')
    e('E29', 'SĐT lẫn chữ ("0912abc456")', 'Dữ liệu rác.', dict(phone='0912abc456'), 'ERROR', 'Số điện thoại', 'Cao')
    e('E30', 'SĐT có dấu cách ("091 234 5678")', 'Định dạng hay gặp; nên chuẩn hóa thành số liền.', dict(phone='091 234 5678'), 'CREATE', sev='Thấp', truth_over=dict(phone='0912345678'))
    e('E31', 'SĐT có dấu gạch ("091-234-5678")', 'Như E30.', dict(phone='091-234-5678'), 'CREATE', sev='Trung bình', truth_over=dict(phone='0912345678'),
      note='Mong đợi tiêu chí thực tế: chuẩn hóa bỏ dấu gạch.')
    e('E32', 'SĐT dạng quốc tế (+84912345678)', 'Định dạng hợp lệ và rất phổ biến.', dict(phone='+84912345678'), 'CREATE', sev='Trung bình', truth_over=dict(phone='0912345678'),
      note='Chuẩn hóa +84 thành số 0 đầu.')
    e('E33', 'SĐT quá dài (20 chữ số)', 'Số vô lý không nên nhập thầm lặng.', dict(phone='09123456789012345678'), 'ERROR', 'Số điện thoại', 'Trung bình')
    e('E34', 'SĐT trong Excel là số (mất số 0 đầu: 912345678)', 'Excel hay đổi 0912... thành số 912...; nhập thầm lặng số thiếu 0 là lỗi dữ liệu nguy hiểm.', dict(phone=912345678), 'ERROR', 'Số điện thoại', 'Cao',
      note='Hiện RPA nhận chuỗi "912345678" như hợp lệ (đủ 9 chữ số).')
    # -- Title / quốc tịch --
    e('E35', 'Title ngoài danh mục ("Dr")', 'Phải báo cần điền tay, không bỏ qua im lặng.', dict(title='Dr'), 'MANUAL', 'Title', 'Trung bình', truth_over=dict(title=''), note='Title ngoài danh mục: để trống, RPA báo điền tay.')
    e('E36', 'Title trống', 'Title không bắt buộc.', dict(title=''), 'CREATE', sev='Thấp')
    e('E37', 'Quốc tịch ngoài danh mục ("Lào")', 'Báo cần điền tay.', dict(nat='Lào'), 'MANUAL', 'Nationality', 'Trung bình', truth_over=dict(nat=''))
    e('E38', 'Quốc tịch viết không dấu ("Viet Nam")', 'Gần đúng nhưng khác danh mục.', dict(nat='Viet Nam'), 'MANUAL', 'Nationality', 'Thấp', truth_over=dict(nat=''))
    # -- địa chỉ --
    e('E39', 'Địa chỉ trống', 'Địa chỉ không bắt buộc.', dict(addr=''), 'CREATE', sev='Trung bình')
    e('E40', 'Địa chỉ chỉ 1 phần ("Hà Nội")', 'Không tách được tỉnh/phường/số nhà → báo điền tay.', dict(addr='Hà Nội'), 'MANUAL', 'Địa chỉ', 'Trung bình', truth_over=dict(addr=None))
    e('E41', 'Địa chỉ chỉ có dấu phẩy (",,,")', 'Dữ liệu rác.', dict(addr=',,,'), 'MANUAL', 'Địa chỉ', 'Thấp')
    e('E42', 'Địa chỉ 4 phần', 'Phần đầu gộp thành số nhà/đường.', dict(addr='Số 1, Ngõ 2, Phường B, Hà Nội'), 'CREATE', sev='Thấp')
    e('E43', 'Địa chỉ dài trên 250 ký tự', 'Ô địa chỉ giới hạn 250 ký tự: không được cắt cụt thầm lặng.', dict(addr='Số 1 ' + 'Đường rất dài ' * 20 + ', Phường B, Hà Nội'), 'ERROR', 'địa chỉ', 'Trung bình')
    e('E44', 'Địa chỉ có xuống dòng trong ô Excel', 'Ô nhiều dòng; OH chỉ có ô một dòng.', dict(addr='Số 3\nĐường D, Phường E, Hà Nội'), 'CREATE', sev='Thấp', note='Quan sát cách lưu của OH.',
      truth_over=dict(addr=None))
    # -- khác --
    e('E45', 'Thiếu số CCCD trong Excel', 'RPA không dùng CCCD (OHDemo không có ô CCCD): thiếu CCCD không được làm hỏng luồng.', dict(cccd=''), 'CREATE', sev='Thấp')
    e('E46', 'Ngày sinh nhập dưới dạng số (15031985)', 'Excel có thể lưu ngày thành số nguyên.', dict(dob=15031985), 'CREATE', sev='Thấp', truth_over=dict(dob='15/03/1985'))
    return cases


# ======================================================================================================
# GHI EXCEL
# ======================================================================================================
def write_xlsx(cases, path: Path):
    wb = Workbook()
    ws = wb.active
    ws.append(['Dữ liệu kiểm thử RPA (sinh tự động, dữ liệu giả)'])
    ws.append(HEADER)
    for c in cases:
        r = c.raw if not c.rerun_of else c.raw
        ws.append(['KT-' + c.id, r.get('title') or None, r.get('given') or None, r.get('middle') or None, r.get('last') or None, r.get('dob') if r.get('dob') != '' else None,
                   r.get('sex') or None, r.get('addr') or None, r.get('phone') if r.get('phone') != '' else None, r.get('nat') or None,
                   'POL-KT', 'Công ty Kiểm thử', 'PKG-01', 'Gói khám sức khỏe tổng quát cơ bản', None, None, None, r.get('cccd') or None, None, None, None, c.id])
        for cell in ws[ws.max_row]:
            if isinstance(cell.value, str):
                cell.data_type = 's'
    wb.save(path)


# ======================================================================================================
# CÔNG CỤ ĐIỀU KHIỂN OH
# ======================================================================================================
def fold(t):
    t = unicodedata.normalize('NFD', str(t or '').lower().replace('đ', 'd'))
    return ' '.join(''.join(c for c in t if unicodedata.category(c) != 'Mn').split())


def launch_oh():
    subprocess.run(['taskkill', '/F', '/IM', 'OHDemo.exe'], capture_output=True)
    time.sleep(0.5)
    proc = subprocess.Popen([str(OH_EXE)])
    time.sleep(4)
    return proc, E.OhDemoRPA()


def classify(fn, row):
    """Chạy process() và trả (loại, thông báo)."""
    try:
        text = fn(row)
    except E.NeedManual as exc:
        return 'MANUAL', str(exc)
    except Exception as exc:
        return 'ERROR', f'{type(exc).__name__}: {exc}'
    if text.startswith('Đã tạo'):
        return 'CREATE', text
    if text.startswith('Đã cập nhật'):
        return 'UPDATE', text
    if text.startswith('Không đổi'):
        return 'SAME', text
    return 'OTHER', text


def count_name(eng, full):
    try:
        if eng.search(full) != 'list':
            return 0
        return sum(fold(r['name']) == fold(full) for r in eng.result_rows())
    except Exception:
        return -1


def readback(eng, pid):
    eng.leave_edit()
    state = eng.search(pid)
    if state != 'view':
        raise ReviewRequired(f'Không mở được hồ sơ {pid} để đối soát (trang: {state}).')
    eng.click('edit-toggle')
    eng.wait_for(lambda: 'edit-pid' in eng.index, 'mở Edit để đối soát')
    cur = eng.read_edit()
    eng.leave_edit()
    return cur


def reconcile(cur, truth):
    """So hồ sơ đọc lại từ OH với dữ liệu gốc. Trả danh sách sai lệch (rỗng = khớp)."""
    bad = []
    pairs = [('first', 'Họ'), ('middle', 'Đệm'), ('last', 'Tên'), ('sex', 'Giới tính'), ('dob', 'Ngày sinh'), ('phone', 'Điện thoại')]
    for key, label in pairs:
        if truth.get(key) is not None and cur.get(key) != truth[key]:
            bad.append(f'{label}: OH="{cur.get(key)}" ≠ gốc="{truth[key]}"')
    if truth.get('title') and cur.get('title') != truth['title']:
        bad.append(f'Title: OH="{cur.get("title")}" ≠ gốc="{truth["title"]}"')
    if truth.get('nat') and cur.get('nationality') != truth['nat']:
        bad.append(f'Quốc tịch: OH="{cur.get("nationality")}" ≠ gốc="{truth["nat"]}"')
    if truth.get('addr') and truth['addr'] not in cur.get('addresses', []):
        bad.append(f'Địa chỉ: không thấy "{truth["addr"]}" trong {cur.get("addresses")}')
    return bad


def setup_manual(eng, last, mid, given, year, phone):
    """Tạo sẵn hồ sơ bằng thao tác giao diện (tiền điều kiện của các ca D)."""
    eng.leave_edit()
    eng.click('new-patient')
    eng.wait_for(lambda: 'new-first' in eng.index, 'mở khung New Patient (chuẩn bị)')
    for aid, v in (('new-first', last), ('new-middle', mid), ('new-last', given), ('new-year', year), ('new-phone', phone)):
        eng.set_text(aid, v)
    eng.click('new-save')
    eng.wait_for(lambda: 'edit-pid' in eng.index, 'cấp PID (chuẩn bị)')
    pid = eng.label('edit-pid')
    eng.leave_edit()
    return pid


# ======================================================================================================
# CHẠY
# ======================================================================================================
def evaluate(c: Case):
    """Phán định ĐẠT / KHÔNG ĐẠT dựa trên mong đợi viết trước."""
    if not c.actual_type:                                   # ca chưa được chạy (ví dụ chế độ thử nhanh)
        c.verdict, c.why = 'CHƯA CHẠY', 'Ca chưa được chạy'
        return
    why = []
    if c.actual_type != c.expected:
        why.append(f'Mong đợi {c.expected} nhưng thực tế {c.actual_type}')
    elif c.expected in ('ERROR', 'MANUAL') and c.kw and fold(c.kw) not in fold(c.actual):
        why.append(f'Thông báo không nêu "{c.kw}"')
    if c.expected == 'ERROR' and c.before is not None and c.after is not None and c.before >= 0 and c.after != c.before:
        why.append(f'Có tác động phụ: số hồ sơ cùng tên đổi {c.before} → {c.after}')
    if c.recon:
        why.append('Đối soát lệch: ' + '; '.join(c.recon))
    c.why = '; '.join(why)
    c.verdict = 'ĐẠT' if not why else 'KHÔNG ĐẠT'


def run_main(cases):
    pythoncom.CoInitializeEx(0)
    xlsx = HERE / 'du_lieu_kiem_thu.xlsx'
    write_xlsx(cases, xlsx)
    _, rows = read_daily(xlsx)
    by_line = {}
    for case, row in zip(cases, rows):
        case.line = row['line']
        by_line[case.id] = row
    log(f'Đã sinh {len(cases)} ca; file {xlsx.name}')
    proc, eng = launch_oh()
    pids = {}

    def run(case_list, *, side_check=True):
        for c in case_list:
            row = by_line[c.id]
            if side_check and c.side:
                full = ' '.join(x for x in (str(c.raw['last']).strip(), str(c.raw['middle']).strip(), str(c.raw['given']).strip()) if x)
                c.before = count_name(eng, full) if full else None
            t = time.time()
            c.actual_type, c.actual = classify(eng.process, row)
            c.dur = round(time.time() - t, 2)
            import re
            m = re.search(r'PID (\S+)', c.actual)
            if m:
                c.pid = m.group(1).split(' ')[0]
                pids[c.id] = c.pid
            if side_check and c.side and c.before is not None:
                full = ' '.join(x for x in (str(c.raw['last']).strip(), str(c.raw['middle']).strip(), str(c.raw['given']).strip()) if x)
                c.after = count_name(eng, full)
            log(f'{c.id:<6} {c.expected:<7} → {c.actual_type:<7} {c.actual[:90]}')

    def do_recon(case_list):
        for c in case_list:
            if (c.id.endswith('S') and c.id.startswith('C')) or c.id == 'D06A':
                continue                                  # hồ sơ bị ca sau cố ý sửa
            if c.truth is None or not c.pid or c.actual_type not in ('CREATE', 'UPDATE', 'SAME', 'MANUAL'):
                continue
            try:
                cur = readback(eng, c.pid)
                c.recon = reconcile(cur, c.truth)
            except Exception as exc:
                c.recon = [f'Không đọc lại được: {exc}']
            c.recon_done = True

    pre_cases = lambda ids: [c for c in cases if c.id in ids]
    # Chuẩn bị tiền điều kiện cho nhóm D
    log('Chuẩn bị tiền điều kiện nhóm D')
    setup_manual(eng, 'Hồ', 'Thanh', 'Tùng', '1990', '0911000001')
    setup_manual(eng, 'Hồ', 'Thanh', 'Tùng', '1990', '0911000002')
    setup_manual(eng, 'Nguyễn', 'Văn', 'Anh', '1990', '0933000099')

    order = [c for c in cases if c.group.startswith('A.')]
    log('=== Pha 1: nhóm A (80 người mới) ===')
    run(order)
    log('=== Pha 2: nhóm H (100 người, khối lượng) ===')
    h_cases = [c for c in cases if c.group.startswith('H.')]
    run(h_cases)
    log('=== Pha 3: nhóm C, D, E ===')
    mid_cases = [c for c in cases if c.group[0] in 'CDE']
    if os.environ.get('KT_FAST'):                         # chế độ thử nhanh: chỉ vài ca mỗi nhóm
        keep = ('C01S', 'C01', 'C04S', 'C04', 'D01', 'D02', 'D03', 'D05A', 'D05B', 'E01', 'E06', 'E13', 'E32', 'E34', 'E35', 'E40')
        mid_cases = [c for c in mid_cases if c.id in keep]
    run(mid_cases)
    log('=== Pha 4: đối soát lại toàn bộ hồ sơ trong OH ===')
    do_recon(order + h_cases + mid_cases)
    # Pha 5: chạy lại toàn bộ A và H (phải ra "Không đổi", không tạo trùng)
    log('=== Pha 5: chạy lại nhóm A và H lần 2 ===')
    reruns = []
    for c in order + h_cases:
        r = Case(id=c.id + '-L2', group='B. Chạy lại lần 2 (không được tạo trùng)', title=f'Chạy lại {c.id}', risk='Chạy lại cùng dữ liệu phải ra "Không đổi", không tạo thêm hồ sơ.',
                 raw=c.raw, expected='SAME', truth=c.truth, sev='Cao', rerun_of=c.id)
        reruns.append(r)
        by_line[r.id] = by_line[c.id]
    run(reruns, side_check=False)
    for r in reruns:
        r.line = by_line[r.id]['line']
        if r.pid and r.pid != pids.get(r.rerun_of):
            r.recon.append(f'PID đổi {pids.get(r.rerun_of)} → {r.pid}')
    cases.extend(reruns)
    # đếm tổng số hồ sơ để phát hiện tạo trùng
    for c in cases:
        evaluate(c)
    proc.terminate()
    return cases


def run_env(env_results):
    """Nhóm G: tình huống môi trường (mỗi ca dùng một cửa sổ OHDemo riêng)."""
    pythoncom.CoInitializeEx(0)
    import win32con
    import win32gui
    raw, truth = person(9000)
    xlsx = HERE / 'du_lieu_kiem_thu_G.xlsx'
    probe = [Case(id=f'G{i:02d}', group='G. Tình huống môi trường', title='', risk='', raw=person(9000 + i)[0], expected='CREATE') for i in range(1, 10)]
    for p_, (r_, t_) in zip(probe, [person(9000 + i) for i in range(1, 10)]):
        p_.raw, p_.truth = r_, t_
    write_xlsx(probe, xlsx)
    _, rows = read_daily(xlsx)
    rowof = {p_.id: r for p_, r in zip(probe, rows)}
    out = []

    def case(id_, title, risk, expected, kw=''):
        c = next(p for p in probe if p.id == id_)
        c.title, c.risk, c.expected, c.kw, c.sev = title, risk, expected, kw, 'Cao'
        return c

    def finish(c, t0):
        c.dur = round(time.time() - t0, 2)
        evaluate(c)
        out.append(c)
        log(f'{c.id} {c.expected} → {c.actual_type} {c.actual[:100]} | {c.verdict}')

    # G01: hộp thoại "Vẫn tạo mới?" đang kẹt
    c = case('G01', 'Hộp thoại xác nhận "Vẫn tạo mới?" đang kẹt trước khi chạy', 'Hộp thoại do thao tác tay/lần chạy trước để lại; RPA phải tự dọn và xử lý bình thường.', 'CREATE')
    c.pre = 'Tạo hồ sơ trùng tên + SĐT với DEMO0001 rồi Save → hộp thoại hiện.'
    proc, eng = launch_oh()
    eng.click('new-patient'); eng.wait_for(lambda: 'new-first' in eng.index, 'new')
    for aid, v in (('new-first', 'Nguyễn'), ('new-middle', 'Văn'), ('new-last', 'Mẫu'), ('new-year', '1999'), ('new-phone', '0900000001')):
        eng.set_text(aid, v)
    eng.click('new-save'); time.sleep(1.2)
    c.note = f'Hộp thoại lúc đầu: {eng.box_texts()}'
    t0 = time.time(); c.actual_type, c.actual = classify(eng.process, rowof['G01'])
    c.recon = [] if not eng.message_boxes() else ['Hộp thoại vẫn còn sau khi chạy']
    finish(c, t0); proc.terminate()

    # G02: OH đang ở trang Edit có thay đổi chưa lưu
    c = case('G02', 'OH đang ở trang Edit, có thay đổi chưa lưu', 'Nhân viên đang sửa dở hồ sơ rồi bấm chạy RPA.', 'CREATE')
    c.pre = 'Mở DEMO0001 → Edit → sửa SĐT, chưa Save.'
    proc, eng = launch_oh()
    eng.set_text('pid-search', 'DEMO0001'); eng.enter('pid-search'); eng.wait_for(lambda: 'view-pid' in eng.index, 'view')
    eng.click('edit-toggle'); eng.wait_for(lambda: 'edit-pid' in eng.index, 'edit'); eng.set_text('edit-phone', '0999999999')
    t0 = time.time(); c.actual_type, c.actual = classify(eng.process, rowof['G02'])
    cur = readback(eng, 'DEMO0001'); c.recon = [] if cur['phone'] == '0900000001' else [f'DEMO0001 bị đổi SĐT thành {cur["phone"]} (thay đổi dở dang bị lưu nhầm)']
    c.note = 'RPA bỏ thay đổi chưa lưu của người dùng (chọn Yes ở hộp xác nhận). Đã kiểm tra DEMO0001 không bị lưu nhầm.'
    finish(c, t0); proc.terminate()

    # G03: OH đang ở trang kết quả tìm kiếm
    c = case('G03', 'OH đang ở trang Search Results', 'Trang bất kỳ đang mở khi bắt đầu.', 'CREATE'); c.pre = 'Tìm "Nguyễn Văn Mẫu" → hiện danh sách.'
    proc, eng = launch_oh(); eng.search('Nguyễn Văn Mẫu')
    t0 = time.time(); c.actual_type, c.actual = classify(eng.process, rowof['G03']); finish(c, t0); proc.terminate()

    # G04: OH đang ở khung New Patient đang nhập dở
    c = case('G04', 'OH đang ở khung New Patient, đã nhập dở', 'Khung tạo mới đang mở với dữ liệu dở dang.', 'CREATE'); c.pre = 'Mở New Patient, nhập tên "Dở Dang".'
    proc, eng = launch_oh(); eng.click('new-patient'); eng.wait_for(lambda: 'new-first' in eng.index, 'new'); eng.set_text('new-first', 'Dở'); eng.set_text('new-last', 'Dang')
    t0 = time.time(); c.actual_type, c.actual = classify(eng.process, rowof['G04']); finish(c, t0); proc.terminate()

    # G05: OH bị thu nhỏ
    c = case('G05', 'Cửa sổ OH bị thu nhỏ khi chạy', 'Người dùng thu nhỏ OH; UI Automation không thấy ô. Phải báo rõ nguyên nhân, không treo, không ghi sai.', 'ERROR', 'THU NHỎ')
    c.pre = 'Thu nhỏ cửa sổ OHDemo.'
    proc, eng = launch_oh(); win32gui.ShowWindow(eng.handle, win32con.SW_MINIMIZE); time.sleep(0.6)
    t0 = time.time(); c.actual_type, c.actual = classify(eng.process, rowof['G05'])
    win32gui.ShowWindow(eng.handle, win32con.SW_RESTORE); time.sleep(0.8)
    t1 = time.time(); a2, m2 = classify(eng.process, rowof['G05'])
    c.note = f'Sau khi khôi phục cửa sổ, chạy lại cùng dòng: {a2} ({m2[:60]})'
    if a2 != 'CREATE':
        c.recon.append('Chạy lại sau khi khôi phục cửa sổ không thành công')
    finish(c, t0); proc.terminate()

    # G06: OH bị đóng giữa chừng
    c = case('G06', 'OH bị đóng giữa lúc chạy', 'OH tắt đột ngột; RPA phải báo lỗi rõ ràng, không treo.', 'ERROR', 'OH')
    c.pre = 'Đóng OHDemo ngay trước khi xử lý dòng.'
    proc, eng = launch_oh(); proc.terminate(); time.sleep(1.5)
    t0 = time.time(); c.actual_type, c.actual = classify(eng.process, rowof['G06']); finish(c, t0)

    # G07: nút Dừng
    c = case('G07', 'Người dùng bấm Dừng', 'Tín hiệu dừng phải chặn dòng đang chờ, không ghi dở dang.', 'ERROR', 'dừng')
    c.pre = 'Bật cờ dừng trước khi xử lý.'
    proc, eng = launch_oh(); import threading
    stop = threading.Event(); stop.set()
    t0 = time.time(); c.actual_type, c.actual = classify(lambda r: eng.process(r, stop), rowof['G07'])
    c.after = count_name(eng, ' '.join(x for x in (rowof['G07']['values']['Patient Last Name'], rowof['G07']['values']['Patient Middle Name'], rowof['G07']['values']['Patient Given Name']) if x))
    if c.after: c.recon.append(f'Đã lỡ tạo {c.after} hồ sơ dù đã dừng')
    finish(c, t0); proc.terminate()

    # G08: ghi ds lỗi.xlsx
    c = case('G08', 'Ghi file ds lỗi.xlsx cho các dòng lỗi', 'Dòng lỗi phải được ghi đủ, đúng số dòng và lý do, để điền tay.', 'SAME')
    tmpdir = Path(tempfile.mkdtemp())
    items = [(rowof['G01'], 'Lý do thử 1'), (rowof['G02'], 'Lý do thử 2')]
    t0 = time.time()
    try:
        path = write_errors(tmpdir, HEADER[:-1], items)
        from openpyxl import load_workbook
        ws = load_workbook(path).active
        data = [[cc.value for cc in r] for r in ws.iter_rows(min_row=2)]
        ok = len(data) == 2 and data[0][1] == 'Lý do thử 1' and data[1][0] == rowof['G02']['line']
        c.actual_type, c.actual = ('SAME', f'Đã ghi {len(data)} dòng, lý do và số dòng đúng') if ok else ('ERROR', f'Nội dung sai: {data}')
        write_errors(tmpdir, HEADER[:-1], [])
        if (tmpdir / ERROR_FILE).exists():
            c.recon.append('Không còn dòng lỗi nhưng file ds lỗi cũ không bị xóa')
    except Exception as exc:
        c.actual_type, c.actual = 'ERROR', f'{type(exc).__name__}: {exc}'
    c.title = 'Ghi và xóa file ds lỗi.xlsx'
    finish(c, t0)
    return out


def run_files():
    """Nhóm F: lỗi ở mức file Excel / thư mục ngày (đọc bằng đúng hàm của RPA, đối chiếu với cách app.load() bắt lỗi)."""
    from datetime import date
    from openpyxl import Workbook
    caught = (ReviewRequired, OSError, KeyError)        # đúng như app.load() đang bắt
    out = []
    base = Path(tempfile.mkdtemp())
    day = date.today().strftime('%d-%m-%Y')

    def mk(rows, header=HEADER[:21], header_row=2, extra_sheet=False, name='ds.xlsx'):
        folder = base / f'case{len(out)}' / day
        folder.mkdir(parents=True)
        wb = Workbook(); ws = wb.active
        for _ in range(header_row - 1):
            ws.append(['Main (Mandatory)'])
        if header is not None:
            ws.append(header)
        for r in rows:
            ws.append(r)
        if extra_sheet:
            wb.create_sheet('Sheet2')
        wb.save(folder / name)
        return folder.parent

    good = ['VM1', 'Ông', 'An', 'Văn', 'Nguyễn', '15/03/1985', 'Nam', 'Thôn A, xã B, Hà Nội', '0912345001', 'Việt Nam', 'P', 'C', 'K', 'G', None, None, None, '001085000001', None, None, None]

    def scenario(id_, title, risk, setup, expected_handled, kw='', note=''):
        c = Case(id=id_, group='F. Lỗi ở file Excel / thư mục', title=title, risk=risk, raw={}, expected='ERROR' if expected_handled else 'SAME', kw=kw, sev='Cao', note=note)
        t0 = time.time()
        try:
            root = setup()
            path = find_daily_file(date.today(), base=root)
            header, rows = read_daily(path)
            c.actual_type, c.actual = 'SAME', f'Đọc được {len(rows)} dòng, {len(header)} cột'
        except Exception as exc:
            c.actual_type = 'ERROR'
            c.actual = f'{type(exc).__name__}: {exc}'
            if not isinstance(exc, caught):
                c.recon = [f'Lỗi {type(exc).__name__} KHÔNG được app.load() bắt → chương trình RPA sẽ báo lỗi hệ thống/treo thay vì thông báo rõ']
        c.dur = round(time.time() - t0, 2)
        evaluate(c)
        out.append(c)
        log(f'{id_} → {c.actual_type} {c.actual[:90]} | {c.verdict}')

    def folder_missing():
        (base / 'none').mkdir(exist_ok=True)
        return base / 'none'

    def folder_empty():
        d = base / 'empty' / day; d.mkdir(parents=True); return d.parent

    def only_error_file():
        d = base / 'onlyerr' / day; d.mkdir(parents=True)
        wb = Workbook(); wb.active.append(['x']); wb.save(d / ERROR_FILE); return d.parent

    def only_temp():
        d = base / 'onlytmp' / day; d.mkdir(parents=True)
        wb = Workbook(); wb.active.append(['x']); wb.save(d / '~$ds.xlsx'); return d.parent

    def fake_xlsx():
        d = base / 'fake' / day; d.mkdir(parents=True); (d / 'ds.xlsx').write_text('đây không phải file Excel', encoding='utf-8'); return d.parent

    def empty_book():
        d = base / 'emptybook' / day; d.mkdir(parents=True); Workbook().save(d / 'ds.xlsx'); return d.parent

    def header_late():
        return mk([good], header_row=14)

    def two_files():
        root = mk([good], name='cu.xlsx'); time.sleep(1.1)
        wb = Workbook(); ws = wb.active; ws.append(['g']); ws.append(HEADER[:21])
        for i in range(3): ws.append(good)
        wb.save(root / day / 'moi.xlsx'); return root

    def blank_rows():
        return mk([good, [None] * 21, [None] * 21, good])

    def second_sheet():
        folder = base / f'case{len(out)}' / day; folder.mkdir(parents=True)
        wb = Workbook(); wb.active.append(['trống']); ws2 = wb.create_sheet('DuLieu'); ws2.append(['g']); ws2.append(HEADER[:21]); ws2.append(good); wb.save(folder / 'ds.xlsx'); return folder.parent

    def wrong_day_folder():
        d = base / 'wrongday' / date.today().strftime('%Y-%m-%d'); d.mkdir(parents=True); mk([good]); return base / 'wrongday'

    scenario('F01', 'Chưa có thư mục của ngày hôm nay', 'Ngày chưa tạo thư mục: phải báo rõ, không đoán file của ngày khác.', folder_missing, True, 'thư mục')
    scenario('F02', 'Thư mục ngày rỗng', 'Chưa đặt file Excel.', folder_empty, True, '.xlsx')
    scenario('F03', 'Thư mục chỉ có ds lỗi.xlsx', 'File kết quả không được đọc nhầm làm danh sách.', only_error_file, True, '.xlsx')
    scenario('F04', 'Thư mục chỉ có file tạm ~$ (Excel đang mở)', 'File khóa tạm của Excel phải bị bỏ qua.', only_temp, True, '.xlsx')
    scenario('F05', 'File .xlsx hỏng (thực chất là văn bản)', 'Phải báo "không đọc được file", không để chương trình lỗi hệ thống.', fake_xlsx, True, 'file', note='Nếu lỗi không được bắt, RPA khi khởi động sẽ ném ngoại lệ chưa xử lý.')
    scenario('F06', 'Workbook trống (không có dữ liệu)', 'Không có dòng nào.', empty_book, True, 'tiêu đề')
    scenario('F07', 'Có tiêu đề nhưng 0 dòng dữ liệu', 'Danh sách rỗng.', lambda: mk([]), True, 'không có dòng')
    scenario('F08', 'Thiếu cột National ID trong tiêu đề', 'Không nhận ra hàng tiêu đề.', lambda: mk([good], header=[h for h in HEADER[:21] if h != 'National ID']), True, 'tiêu đề')
    scenario('F09', 'Hàng tiêu đề ở hàng 14 (quá xa)', 'RPA chỉ tìm tiêu đề trong 10 hàng đầu.', header_late, True, 'tiêu đề')
    scenario('F10', 'Hàng tiêu đề ở hàng 1 (không có hàng nhóm)', 'Cấu trúc hơi khác nhưng hợp lệ.', lambda: mk([good], header_row=1), False)
    scenario('F11', 'Có hàng trống xen giữa dữ liệu', 'Hàng trống phải bị bỏ qua, các dòng còn lại vẫn đọc.', blank_rows, False)
    scenario('F12', 'Hai file .xlsx trong thư mục: chọn file mới nhất', 'Phải chọn đúng file mới nhất, không lẫn.', two_files, False, note='Kỳ vọng đọc 3 dòng của file mới.')
    scenario('F13', 'Dữ liệu nằm ở sheet thứ 2 (sheet đầu trống)', 'RPA chỉ đọc sheet đầu tiên.', second_sheet, True, 'tiêu đề', note='Giới hạn đã biết: nhiều sheet không được hỗ trợ.')
    scenario('F14', 'Thư mục ngày sai định dạng (YYYY-MM-DD thay vì DD-MM-YYYY)', 'Quy ước thư mục đặt sai.', wrong_day_folder, True, 'thư mục')
    return out


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:12]


def main():
    LOG.write_text('', encoding='utf-8')
    started = datetime.now()
    cases = build_cases()
    log(f'Bắt đầu kiểm thử {started:%d/%m/%Y %H:%M}')
    cases = run_main(cases)
    log('=== Nhóm F (file) ===')
    files = run_files()
    log('=== Nhóm G (môi trường) ===')
    env = run_env([])
    result = dict(
        meta=dict(started=started.isoformat(timespec='seconds'), finished=datetime.now().isoformat(timespec='seconds'),
                  python=platform.python_version(), os=platform.platform(), engine_sha=sha(SRC / 'rpa_tool' / 'ohdemo_engine.py'),
                  ohdemo_sha=sha(OH_EXE), excel_sha=sha(SRC / 'shared' / 'excel.py'), seed=20261119),
        cases=[asdict(c) for c in cases + files + env])
    (HERE / 'ket_qua.json').write_text(json.dumps(result, ensure_ascii=False, indent=1, default=str), encoding='utf-8')
    done = result['cases']
    log(f'Xong: {len(done)} ca, ĐẠT {sum(c["verdict"] == "ĐẠT" for c in done)}, KHÔNG ĐẠT {sum(c["verdict"] == "KHÔNG ĐẠT" for c in done)}')


if __name__ == '__main__':
    main()
