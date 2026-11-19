"""Vết thay đổi của RPA: ghi "trước/sau" của từng hồ sơ để kiểm tra, đối soát và khôi phục.

Các file nằm trong thư mục ngày của ds bung (đã .gitignore, chứa dữ liệu cá nhân thật của khách; không đưa vào repo):
  nhat_ky_thay_doi.jsonl     mỗi dòng đã xử lý xong một bản ghi (PID, hành động, giá trị trước, giá trị sau, dữ liệu Excel mong đợi)
  bao_cao_thay_doi.xlsx      bản đọc được cho người duyệt: mỗi trường đã đổi một dòng, giá trị cũ → mới
"""
import json
from datetime import datetime
from pathlib import Path
from openpyxl import Workbook

LOG_NAME = 'nhat_ky_thay_doi.jsonl'
REPORT_NAME = 'bao_cao_thay_doi.xlsx'
FIELDS = ('title', 'first', 'middle', 'last', 'sex', 'dob', 'phone', 'nationality', 'addresses')
LABEL = dict(title='Title', first='Họ', middle='Đệm', last='Tên', sex='Giới tính', dob='Ngày sinh', phone='SĐT', nationality='Quốc tịch', addresses='Địa chỉ')


def fields(cur) -> dict:
    return {k: cur[k] for k in FIELDS}


def expected(rec) -> dict:
    """Phần dữ liệu Excel cần để đối soát lại sau này."""
    keys = ('title', 'first', 'middle', 'last', 'sex', 'dob', 'phone', 'nationality', 'address', 'address_parts')
    return {k: (list(rec[k]) if k == 'address_parts' and rec[k] else rec[k]) for k in keys}


def record(folder, entry: dict):
    entry = dict(entry, at=datetime.now().isoformat(timespec='seconds'))
    path = Path(folder) / LOG_NAME
    with path.open('a', encoding='utf-8') as stream:
        stream.write(json.dumps(entry, ensure_ascii=False) + '\n')
        stream.flush()
    return entry


def read_entries(folder, file_name=None) -> list:
    path = Path(folder) / LOG_NAME
    out = []
    if path.exists():
        for text in path.read_text(encoding='utf-8').splitlines():
            try:
                item = json.loads(text)
            except ValueError:
                continue                                     # dòng cuối bị cắt dở khi tiến trình chết
            if file_name is None or item.get('file') == file_name:
                out.append(item)
    return out


def _fmt(value):
    return '; '.join(value) if isinstance(value, list) else ('' if value is None else str(value))


def write_report(path: Path, header: list, rows: list) -> Path | None:
    book = Workbook()
    sheet = book.active
    sheet.append(header)
    for row in rows:
        sheet.append(list(row))
        for cell in sheet[sheet.max_row]:
            if isinstance(cell.value, str):
                cell.data_type = 's'
    for column in sheet.columns:
        sheet.column_dimensions[column[0].column_letter].width = 26
    tmp = Path(path).with_name('~' + Path(path).name)
    book.save(tmp)
    tmp.replace(path)
    return Path(path)


def write_change_report(folder, entries=None):
    """Bản đọc được: mỗi trường đã đổi một dòng (tạo mới: liệt kê các trường đã điền)."""
    entries = read_entries(folder) if entries is None else entries
    rows = []
    for e in entries:
        before, after = e.get('before'), e['after']
        for key in FIELDS:
            old = None if before is None else before[key]
            if before is not None and old == after[key]:
                continue
            if before is None and not after[key]:
                continue
            rows.append([e['line'], e['pid'], e['action'], LABEL[key], _fmt(old), _fmt(after[key]), e['at']])
        if e['action'] == 'giữ':
            rows.append([e['line'], e['pid'], 'giữ', '(không đổi)', '', '', e['at']])
        for m in e.get('manual') or []:
            rows.append([e['line'], e['pid'], e['action'], 'CẦN ĐIỀN TAY', '', m, e['at']])
    return write_report(Path(folder) / REPORT_NAME, ['Dòng Excel', 'PID', 'Hành động', 'Trường', 'Giá trị cũ', 'Giá trị mới', 'Giờ'], rows)
