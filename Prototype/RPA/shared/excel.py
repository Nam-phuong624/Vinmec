"""Đọc danh sách bung gói của ngày hiện tại từ ds bung/DD-MM-YYYY/. Không ghi vào file nguồn."""
from datetime import date, datetime
from pathlib import Path
from openpyxl import load_workbook
from shared.identity import ReviewRequired, dob, national_id, visit_datetime
from shared.paths import DS_BUNG


ERROR_FILE = 'ds lỗi.xlsx'


def write_errors(folder: Path, header: list[str], items: list[tuple[dict, str]]) -> Path | None:
    """Ghi các dòng lỗi (nguyên các cột gốc + số dòng + lý do) vào 'ds lỗi.xlsx' để điền thủ công.

    Ghi lại toàn bộ mỗi lần chạy; không có dòng lỗi thì xóa file cũ do RPA tạo để tránh nhầm.
    """
    from openpyxl import Workbook
    path = Path(folder) / ERROR_FILE
    if not items:
        path.unlink(missing_ok=True)
        return None
    book = Workbook()
    sheet = book.active
    sheet.title = 'ds lỗi'
    sheet.append(['Dòng trong file gốc', 'Lý do lỗi'] + header)
    for row, reason in items:
        sheet.append([row['line'], reason] + [('' if v is None else v) for v in row['values'].values()])
        for cell in sheet[sheet.max_row]:
            if isinstance(cell.value, str):
                cell.data_type = 's'  # giữ nguyên chuỗi, kể cả số 0 đầu của CCCD
    temporary = path.with_name('~ds lỗi.tmp.xlsx')
    book.save(temporary)
    temporary.replace(path)
    return path


def day_folder(day: date | None = None, base: Path = DS_BUNG) -> Path:
    # DS_BUNG_DAY=DD-MM-YYYY chỉ dùng khi thử với dữ liệu ngày khác; mặc định là ngày hệ thống.
    import os
    override = os.environ.get('DS_BUNG_DAY')
    if day is None and override:
        return base / override
    return base / (day or date.today()).strftime('%d-%m-%Y')


def find_daily_file(day: date | None = None, base: Path = DS_BUNG) -> Path:
    """File .xlsx mới nhất trong thư mục của đúng ngày; không đoán file của ngày khác."""
    folder = day_folder(day, base)
    if not folder.is_dir():
        raise ReviewRequired(f'Chưa có thư mục của ngày hôm nay: {folder}')
    files = [p for p in folder.glob('*.xlsx') if not p.name.startswith('~$') and p.name != ERROR_FILE]
    if not files:
        raise ReviewRequired(f'Thư mục {folder} chưa có file .xlsx.')
    return max(files, key=lambda p: (p.stat().st_mtime, p.name))


def read_daily(path: str | Path) -> tuple[list[str], list[dict]]:
    """Trả về (tiêu đề, các dòng). Mỗi dòng: line, cells (đủ mọi cột, dạng chuỗi), values (gốc)."""
    book = load_workbook(path, read_only=True, data_only=True)
    try:
        ws = book[book.sheetnames[0]]
        header, header_line, lines = None, 0, []
        for line, values in enumerate(ws.iter_rows(values_only=True), 1):
            if header is None:
                names = [str(v).strip() if v is not None else '' for v in values]
                if 'National ID' in names and 'Patient ID' in names:
                    header, header_line = names, line
                elif line >= 10:
                    break
                continue
            lines.append((line, values))
        if header is None:
            raise ReviewRequired('Không tìm thấy hàng tiêu đề (cần cột Patient ID và National ID).')
        header = [h or f'Cột {i + 1}' for i, h in enumerate(header)]
        rows = []
        for line, values in lines:
            if not any(v is not None and str(v).strip() for v in values):
                continue
            values = list(values) + [None] * (len(header) - len(values))
            values = values[:len(header)]
            rows.append(dict(line=line, values=dict(zip(header, values)),
                             cells=[('' if v is None else str(v)) for v in values]))
        if not rows:
            raise ReviewRequired('File không có dòng dữ liệu.')
        return header, rows
    finally:
        book.close()


def parse_address(text: str):
    """Tách địa chỉ tự do thành (tỉnh/thành, phường/xã, số nhà/đường). Trả None nếu không tách được.

    Quy ước: các cấp ngăn cách bằng dấu phẩy, cấp cuối là tỉnh/thành, cấp áp chót là phường/xã.
    Chỉ có 2 phần: phường/xã để trống. Không suy diễn địa giới và không chuyển đổi địa chỉ sau sáp nhập.
    """
    parts = [p.strip() for p in str(text or '').split(',') if p.strip()]
    if len(parts) >= 3:
        return parts[-1], parts[-2], ', '.join(parts[:-2])
    if len(parts) == 2:
        return parts[1], '', parts[0]
    return None


def ohdemo_record(row: dict) -> dict:
    """Ánh xạ một dòng Excel sang các trường của OHDemo (Patient Profile). Ném ReviewRequired nếu thiếu/sai.

    Excel: Patient Last Name = họ, Middle = tên đệm, Given = tên. OH hiển thị theo thứ tự họ, đệm, tên.
    """
    v = {k: ('' if x is None else str(x).strip()) for k, x in row['values'].items()}
    last, middle, given = v.get('Patient Last Name', ''), v.get('Patient Middle Name', ''), v.get('Patient Given Name', '')
    if not last or not given:
        raise ReviewRequired('Thiếu họ hoặc tên.')
    sex = v.get('Sex', '')
    if sex not in ('Nam', 'Nữ', 'Khác'):
        raise ReviewRequired('Giới tính phải là Nam / Nữ / Khác.')
    birth = dob(row['values'].get('Date Of Birth'))               # YYYY-MM-DD
    y, m, d = birth.split('-')
    phone = v.get('Business Phone Number', '').replace(' ', '')
    if len(phone) < 8 or not phone.isdigit():
        raise ReviewRequired('Số điện thoại phải gồm chữ số (tối thiểu 8).')
    address = v.get('Patient Address', '')
    return dict(
        title=v.get('Title', ''), first=last, middle=middle, last=given,
        full_name=' '.join(p for p in (last, middle, given) if p),
        sex=sex, dob=f'{d}/{m}/{y}', year=y, phone=phone,
        nationality=v.get('Nationality', ''),
        address=address, address_parts=parse_address(address),
    )


def oh_record(row: dict, batch: str, visit_default: str) -> dict:
    """Ánh xạ một dòng Excel sang các ô của hộp 'Tạo hồ sơ' trên OH.

    Excel không có cột Công ty/Đợt khám: dùng Policy Name làm công ty, đợt là tên thư mục ngày.
    Nếu Visit Date Time trống thì dùng ngày của thư mục. Ném ReviewRequired nếu dòng không đủ dữ liệu.
    """
    v = {k: ('' if x is None else (x if isinstance(x, (date, datetime)) else str(x).strip())) for k, x in row['values'].items()}
    name = ' '.join(str(v[k]) for k in ('Patient Last Name', 'Patient Middle Name', 'Patient Given Name') if v.get(k))
    if not name:
        raise ReviewRequired('Thiếu họ tên.')
    sex = str(v.get('Sex') or '')
    if not sex:
        raise ReviewRequired('Thiếu giới tính.')
    if not v.get('Package Code'):
        raise ReviewRequired('Thiếu mã gói khám.')
    company = str(v.get('Policy Name') or '')
    if not company:
        raise ReviewRequired('Thiếu Policy Name (dùng làm công ty).')
    return dict(
        name=name,
        national_id=national_id(row['values'].get('National ID')),
        dob=dob(v.get('Date Of Birth')),
        sex=sex,
        phone=str(v.get('Business Phone Number') or ''),
        nationality=str(v.get('Nationality') or ''),
        address_original=str(v.get('Patient Address') or ''),
        company=company,
        batch=batch,
        policy_code=str(v.get('Policy Code') or ''),
        policy_name=company,
        package_code=str(v['Package Code']),
        package_name=str(v.get('Package Name') or ''),
        visit_date=visit_datetime(v.get('Visit Date Time') or visit_default),
    )
