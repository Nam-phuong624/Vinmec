"""Đối chiếu CCCD với ds bung và điền các trường của form .docx (trang 1: PID; trang 4: thông tin hành chính)."""
import os
import re
import sys
import unicodedata
from datetime import date, datetime
from pathlib import Path

HERE = Path(sys.executable).resolve().parent if getattr(sys, 'frozen', False) else Path(__file__).resolve().parent
if not getattr(sys, 'frozen', False):
    sys.path.insert(0, str(HERE.parent / 'RPA'))      # dùng chung shared/excel.py và shared/paths.py của dự án RPA

from docx import Document
from docx.oxml.ns import qn
from shared.excel import day_folder, find_daily_file, parse_address, read_daily
from shared.identity import ReviewRequired, dob as normalize_dob

FORMS = {('nam', 'coban'): 'Nam_CoBan.docx', ('nam', 'tieuchuan'): 'Nam_TieuChuan.docx',
         ('nu', 'coban'): 'Nu_CoBan.docx', ('nu', 'tieuchuan'): 'Nu_TieuChuan.docx'}
BOX_ON, BOX_OFF = '☒', '☐'
# Giá trị mặc định cho trang 4. "Nơi cấp" là giá trị thường gặp trên CCCD gắn chip, ds bung/QR không có; sửa trong cau_hinh.json nếu cần.
DEFAULTS = {'DOI_TUONG': 'Người lao động', 'LY_DO': 'Khám định kỳ', 'NOI_CAP': 'Cục Cảnh sát QLHC về TTXH'}


def load_config() -> dict:
    """Tùy chọn: file cau_hinh.json cạnh chương trình ghi đè DOI_TUONG / LY_DO / NOI_CAP (để trống = không điền)."""
    import json
    path = HERE / 'cau_hinh.json'
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
        return {k: str(data[k]) for k in DEFAULTS if k in data}
    except (OSError, ValueError):
        return {}


def fold(text) -> str:
    t = unicodedata.normalize('NFD', str(text or '').lower().replace('đ', 'd'))
    return ' '.join(''.join(c for c in t if unicodedata.category(c) != 'Mn').split())


def templates_dir() -> Path:
    candidates = [HERE / 'Mau']
    if getattr(sys, 'frozen', False):
        candidates.append(Path(getattr(sys, '_MEIPASS', HERE)) / 'Mau')
    for c in candidates:
        if c.is_dir():
            return c
    raise ReviewRequired('Không thấy thư mục Mau (4 form .docx). Đặt thư mục Mau cạnh chương trình.')


def load_customers(day: date | None = None):
    """Đọc danh sách của ngày; trả (đường dẫn, tiêu đề, các dòng)."""
    path = find_daily_file(day)
    header, rows = read_daily(path)
    return path, header, rows


def parse_scan(text: str) -> dict:
    """Chuỗi quét: 7 phần ngăn cách bằng '|' (CCCD|CMND cũ|Họ tên|DDMMYYYY|Giới tính|Địa chỉ|Ngày cấp) hoặc chỉ 12 chữ số CCCD."""
    raw = fix_text((text or '').strip())
    if '|' in raw:
        parts = [p.strip() for p in raw.split('|')]
        if len(parts) != 7:
            raise ReviewRequired('Chuỗi quét phải có đúng 7 phần ngăn cách bằng "|".')
        keys = ('cccd', 'old_id', 'name', 'dob', 'sex', 'address', 'issued')
        data = dict(zip(keys, parts))
    else:
        data = dict(cccd=raw, old_id='', name='', dob='', sex='', address='', issued='')
    if not re.fullmatch(r'\d{12}', data['cccd']):
        raise ReviewRequired('CCCD phải gồm đúng 12 chữ số.')
    return data


def ddmmyyyy(value: str) -> str:
    """'15031985' hoặc '15/03/1985' → '15/03/1985'; sai định dạng thì trả chuỗi rỗng."""
    v = (value or '').strip()
    for fmt in ('%d%m%Y', '%d/%m/%Y', '%Y-%m-%d'):
        try:
            return datetime.strptime(v, fmt).strftime('%d/%m/%Y')
        except ValueError:
            continue
    return ''


def find_customer(rows, cccd: str) -> dict:
    hits = [r for r in rows if str(r['values'].get('National ID') or '').strip() == cccd]
    if not hits:
        raise ReviewRequired('CCCD không có trong danh sách bung của ngày.')
    if len(hits) > 1:
        raise ReviewRequired(f'CCCD trùng ở {len(hits)} dòng (' + ', '.join(str(r["line"]) for r in hits) + '); kiểm tra file.')
    return hits[0]


def package_kind(package_name: str):
    name = fold(package_name)
    if 'co ban' in name:
        return 'coban'
    if 'tieu chuan' in name:
        return 'tieuchuan'
    return None


def sex_kind(sex: str):
    s = fold(sex)
    return 'nam' if s == 'nam' else 'nu' if s == 'nu' else None


def fix_text(s: str) -> str:
    """Sửa chuỗi UTF-8 bị đọc nhầm thành Latin-1/cp1252 (chữ tiếng Việt bị vỡ, ví dụ 'Nguyá»…n') — lỗi gặp ở một số trình duyệt/đầu đọc."""
    if not re.search('[ÂÃÄÆá]', s or ''):
        return s
    for encoding in ('latin-1', 'cp1252'):
        try:
            fixed = s.encode(encoding).decode('utf-8')
        except (UnicodeEncodeError, UnicodeDecodeError):
            continue
        return fixed
    return s


def person(row: dict, scan: dict | None = None) -> dict:
    """Thông tin người khám: ưu tiên dữ liệu đọc từ thẻ CCCD; trường nào thẻ không có thì bổ sung từ ds bung (Excel)."""
    v = {k: ('' if x is None else str(x).strip()) for k, x in row['values'].items()}
    scan = scan or {}
    excel_name = ' '.join(p for p in (v.get('Patient Last Name'), v.get('Patient Middle Name'), v.get('Patient Given Name')) if p)
    return dict(
        name=(scan.get('name') or excel_name).strip(),
        dob=ddmmyyyy(scan.get('dob', '')) or ddmmyyyy(v.get('Date Of Birth', '')),
        sex=sex_kind(scan.get('sex', '')) or sex_kind(v.get('Sex', '')),
        address=(scan.get('address') or v.get('Patient Address', '')).strip(),
        cccd=scan.get('cccd') or v.get('National ID', ''),
        issued=ddmmyyyy(scan.get('issued', '')),
        phone=v.get('Business Phone Number', '').replace(' ', ''),     # chỉ có trong ds bung
        pid=v.get('Patient ID', ''),
        company=v.get('Policy Name', ''),
    )


def build_values(row: dict, scan: dict | None = None, today: date | None = None) -> dict:
    """Giá trị cho các trường của form. Trường không có dữ liệu thì không đưa vào (giữ chấm để viết tay).

    Họ tên, ngày sinh, giới tính, địa chỉ, số CCCD, ngày cấp: lấy từ thẻ CCCD nếu có; số điện thoại, PID, công ty: từ ds bung."""
    p = person(row, scan)
    today = today or date.today()
    full, birth, address = p['name'], p['dob'], p['address']
    config = {**DEFAULTS, **load_config()}
    values = {'HO_TEN': full.upper(), 'CCCD': p['cccd'], 'PID': p['pid']}
    sex = p['sex']
    for prefix in ('', 'P2_'):                      # trang 4 (không tiền tố) và trang 2 (P2_)
        values[prefix + 'NAM_BOX'] = BOX_ON if sex == 'nam' else BOX_OFF
        values[prefix + 'NU_BOX'] = BOX_ON if sex == 'nu' else BOX_OFF
    if birth:
        d = datetime.strptime(birth, '%d/%m/%Y').date()
        values['NGAY_SINH'] = values['P2_NGAY_SINH'] = birth
        values['TUOI'] = str(today.year - d.year - ((today.month, today.day) < (d.month, d.day)))
    parts = parse_address(address)
    if parts:
        values['TINH'], values['PHUONG_XA'], values['SO_NHA'] = parts
    elif address:
        values['SO_NHA'] = address
    if p['issued']:
        values['CAP_NGAY'] = p['issued']
    # Trang 2: họ tên IN HOA; tên người khai viết hoa chữ cái đầu mỗi từ.
    values['P2_HO_TEN'] = full.upper()
    values['P2_SDT'] = p['phone']
    values['P2_DIA_CHI'] = address
    values['P2_NGUOI_KHAI'] = values['P5_NGUOI_KHAI'] = ' '.join(w.capitalize() for w in full.split())   # P5: "Người đề nghị khám sức khỏe" (trang 5)
    # Trang 4: nơi làm việc = tên công ty (Policy Name); các mục mặc định lấy từ cấu hình.
    values['NOI_LAM_VIEC'] = p['company']
    for key in ('DOI_TUONG', 'LY_DO', 'NOI_CAP'):
        values[key] = config.get(key, '')
    return {k: x for k, x in values.items() if x != '' or k.endswith('_BOX')}


def check_scan(row: dict, scan: dict) -> list[str]:
    """So thông tin trên thẻ với ds bung (khi quét QR đủ 7 phần). Trả danh sách điểm không khớp."""
    problems = []
    v = {k: ('' if x is None else str(x).strip()) for k, x in row['values'].items()}
    full = ' '.join(p for p in (v.get('Patient Last Name'), v.get('Patient Middle Name'), v.get('Patient Given Name')) if p)
    if scan.get('name') and fold(scan['name']) != fold(full):
        problems.append(f'Họ tên trên thẻ ("{scan["name"]}") khác ds bung ("{full}")')
    if scan.get('dob') and ddmmyyyy(scan['dob']) != ddmmyyyy(v.get('Date Of Birth', '')):
        problems.append('Ngày sinh trên thẻ khác ds bung')
    if scan.get('sex') and sex_kind(scan['sex']) != sex_kind(v.get('Sex', '')):
        problems.append('Giới tính trên thẻ khác ds bung')
    return problems


def fill_docx(template: Path, out: Path, values: dict) -> list[str]:
    """Điền các content control có tag khớp `values`. Trả các tag đã điền."""
    doc = Document(str(template))
    filled = []
    for sdt in doc.element.body.iter(qn('w:sdt')):
        pr = sdt.find(qn('w:sdtPr'))
        tag = pr.find(qn('w:tag')).get(qn('w:val')) if pr is not None and pr.find(qn('w:tag')) is not None else None
        if tag not in values:
            continue
        texts = sdt.find(qn('w:sdtContent')).findall('.//' + qn('w:t'))
        if not texts:
            continue
        texts[0].text = values[tag]
        for extra in texts[1:]:
            extra.text = ''
        placeholder = pr.find(qn('w:showingPlcHdr'))
        if placeholder is not None:
            pr.remove(placeholder)
        filled.append(tag)
    out.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(out))
    return filled


def print_docx(path: Path, copies: int = 1):
    """In toàn bộ file bằng Microsoft Word (máy in mặc định). Nếu không có Word thì dùng lệnh 'print' của Windows."""
    try:
        import pythoncom
        import win32com.client
        pythoncom.CoInitialize()
        word = win32com.client.DispatchEx('Word.Application')
        word.Visible = False
        word.DisplayAlerts = 0
        try:
            document = word.Documents.Open(str(path), ReadOnly=True)
            document.PrintOut(Background=False, Copies=copies)
            document.Close(False)
        finally:
            word.Quit()
    except Exception:
        os.startfile(str(path), 'print')


def sample_scan(row: dict) -> str:
    """Chuỗi QR giả lập (đúng định dạng 7 phần của CCCD gắn chip) dựng từ một dòng ds bung. Ngày cấp để trống vì ds bung không có."""
    v = {k: ('' if x is None else str(x).strip()) for k, x in row['values'].items()}
    full = ' '.join(p for p in (v.get('Patient Last Name'), v.get('Patient Middle Name'), v.get('Patient Given Name')) if p)
    birth = ddmmyyyy(v.get('Date Of Birth', '')).replace('/', '')
    return '|'.join([v.get('National ID', ''), '', full, birth, v.get('Sex', ''), v.get('Patient Address', ''), ''])


def make_qr_png(text: str) -> bytes:
    import io
    import segno
    buffer = io.BytesIO()
    segno.make(text, error='m', encoding='utf-8').save(buffer, kind='png', scale=7, border=4)
    return buffer.getvalue()


def decode_qr(source) -> str:
    """Giải mã mã QR từ ảnh (đường dẫn hoặc bytes PNG/JPG). Thử nhiều tỉ lệ để đọc được ảnh chụp từ điện thoại."""
    import cv2
    import numpy as np
    data = source if isinstance(source, (bytes, bytearray)) else np.fromfile(str(source), dtype=np.uint8)   # fromfile: đọc được đường dẫn có dấu
    image = cv2.imdecode(np.frombuffer(data, np.uint8) if isinstance(data, (bytes, bytearray)) else data, cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise ReviewRequired('Không đọc được file ảnh.')
    detector = cv2.QRCodeDetector()
    for scale in (1.0, 0.5, 2.0, 0.25):
        trial = image if scale == 1.0 else cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_CUBIC)
        text, _, _ = detector.detectAndDecode(trial)
        if text:
            return text
    raise ReviewRequired('Không tìm thấy mã QR trong ảnh. Chụp rõ nét, không lóa, thấy trọn mã QR.')


def output_name(row: dict) -> str:
    v = row['values']
    full = ' '.join(str(v.get(k) or '') for k in ('Patient Last Name', 'Patient Middle Name', 'Patient Given Name'))
    return f"{row['line']:03d}_{fold(full).replace(' ', '_')}.docx"


def make_form(row: dict, scan: dict | None = None, package: str | None = None, out_dir: Path | None = None):
    """Chọn form theo giới tính + gói khám, điền và lưu. Trả (đường dẫn file, tên form, các tag đã điền)."""
    v = row['values']
    sex = person(row, scan)['sex']          # giới tính trên thẻ CCCD (nếu có), không thì theo ds bung
    if not sex:
        raise ReviewRequired('Không xác định được giới tính (thẻ CCCD và ds bung đều không có Nam/Nữ hợp lệ).')
    kind = package or package_kind(v.get('Package Name') or '')
    if not kind:
        raise ReviewRequired(f'Không xác định được gói khám từ Package Name "{v.get("Package Name") or ""}" (cần có "cơ bản" hoặc "tiêu chuẩn"). Hãy chọn gói thủ công.')
    template = templates_dir() / FORMS[(sex, kind)]
    out = (out_dir or day_folder() / 'phieu_in') / output_name(row)
    values = build_values(row, scan)
    try:
        filled = fill_docx(template, out, values)
    except PermissionError:
        # File của lần quét trước còn đang mở trong Word (bị khóa): lưu sang tên mới, không ghi đè.
        out = out.with_name(f'{out.stem}_{datetime.now():%H%M%S}{out.suffix}')
        filled = fill_docx(template, out, values)
    return out, FORMS[(sex, kind)], filled
