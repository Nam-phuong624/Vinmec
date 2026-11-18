from collections import Counter
from pathlib import Path
from openpyxl import load_workbook
from shared.identity import ReviewRequired, dob, national_id, visit_datetime

MAPPING = {
    'pid': 'Patient ID', 'given': 'Patient Given Name', 'middle': 'Patient Middle Name',
    'last': 'Patient Last Name', 'dob': 'Date Of Birth', 'sex': 'Sex',
    'address': 'Patient Address', 'national_id': 'National ID',
}
PREPARATION_COLUMNS = {
    'phone': 'Business Phone Number', 'nationality': 'Nationality',
    'policy_code': 'Policy Code', 'policy_name': 'Policy Name',
    'package_code': 'Package Code', 'package_name': 'Package Name', 'visit_date': 'Visit Date Time',
}


def sheets(path: str | Path) -> list[str]:
    book = load_workbook(path, read_only=True, data_only=True)
    try:
        return book.sheetnames
    finally:
        book.close()


def read_roster(path: str | Path, sheet: str, company: str, batch: str,
                header_row: int = 2, mapping: dict | None = None, *, preparation=False) -> tuple[list[dict], list[str]]:
    if not company.strip() or not batch.strip():
        raise ReviewRequired('Cần gán công ty và đợt khám khi nạp danh sách.')
    if header_row < 1:
        raise ReviewRequired('Hàng tiêu đề phải từ 1 trở lên.')
    mapping = mapping or MAPPING
    book = load_workbook(path, read_only=True, data_only=True)
    try:
        if sheet not in book.sheetnames:
            raise ReviewRequired('Không có sheet đã chọn.')
        ws = book[sheet]
        header = next(ws.iter_rows(min_row=header_row, max_row=header_row, values_only=True), ())
        positions = {str(v).strip(): i for i, v in enumerate(header) if v is not None}
        missing = [label for key,label in mapping.items() if label not in positions and not (preparation and key=='pid')]
        if preparation:
            missing += [PREPARATION_COLUMNS[k] for k in ('package_code','visit_date')
                        if PREPARATION_COLUMNS[k] not in positions]
        if missing:
            raise ReviewRequired('Thiếu cột: ' + ', '.join(missing))
        rows, errors, invalid_cccd = [], [], []
        all_ids, all_pids = [], []
        for line, values in enumerate(ws.iter_rows(min_row=header_row + 1, values_only=True), header_row + 1):
            if not any(v is not None for v in values):
                continue
            data = {key: values[positions[label]] if label in positions else None for key, label in mapping.items()}
            try:
                data['national_id'] = national_id(data['national_id'])
            except ReviewRequired:
                invalid_cccd.append(line)
                continue
            all_ids.append(data['national_id'])
            if isinstance(data['pid'], str) and data['pid'].strip():
                all_pids.append(data['pid'].strip())
            try:
                if preparation and data['pid'] is None:
                    data['pid']=''
                if not isinstance(data['pid'], str) or (not preparation and not data['pid'].strip()):
                    raise ReviewRequired('PID phải là chuỗi không trống.')
                data['pid'] = data['pid'].strip()
                data['dob'] = dob(data['dob'])
                # OH convention: Last=family, Middle=middle, Given=personal name.
                data['name'] = ' '.join(str(data[k]).strip() for k in ('last', 'middle', 'given') if data[k])
                if not data['name']:
                    raise ReviewRequired('Thiếu họ tên.')
                for key,label in PREPARATION_COLUMNS.items():
                    value=values[positions[label]] if label in positions else ''
                    data[key]=str(value or '').strip()
                if preparation:
                    if not str(data.get('sex') or '').strip():
                        raise ReviewRequired('Thiếu giới tính.')
                    if not data['package_code']:
                        raise ReviewRequired('Thiếu mã gói khám.')
                    data['visit_date']=visit_datetime(values[positions[PREPARATION_COLUMNS['visit_date']]])
                data.update(company=company.strip(), batch=batch.strip(), line=line, sheet=sheet,
                            address=str(data['address'] or ''))
                rows.append(data)
            except ReviewRequired as exc:
                errors.append(f'Dòng {line}: {exc}')
        if invalid_cccd:
            raise ReviewRequired('Không nạp danh sách: CCCD bắt buộc và phải hợp lệ ở mọi dòng. Kiểm tra dòng: '
                                 + ', '.join(map(str, invalid_cccd)))
        for key in ('national_id', 'pid'):
            counts = Counter(all_ids if key == 'national_id' else all_pids)
            for row in rows:
                if counts[row[key]] > 1:
                    row['blocked'] = True
                    errors.append(f"Dòng {row['line']}: trùng {key}; lượt liên quan bị chặn.")
        if not rows:
            raise ReviewRequired('Không có dòng dữ liệu hợp lệ. ' + '; '.join(errors[:3]))
        return rows, errors
    finally:
        book.close()


def read_preparation(path, sheet, company, batch, header_row=2, mapping=None):
    return read_roster(path,sheet,company,batch,header_row,mapping,preparation=True)


def export_prepared(path: Path, rows: list[dict]):
    """Write a separate handoff file; never modify the source workbook."""
    from openpyxl import Workbook
    if not rows or any(not r.get('pid') for r in rows):
        raise ReviewRequired('Chỉ xuất các hồ sơ đã lưu và xác minh PID.')
    book=Workbook();sheet=book.active;sheet.title='DS_bung_DEMO'
    sheet.append([f"Kết quả RPA lần 1 — đã xác minh PID trên OH · {rows[0]['company']} · {rows[0]['batch']}"])
    columns={**MAPPING,**PREPARATION_COLUMNS}
    sheet.append(list(columns.values()))
    for row in rows:
        sheet.append([row.get(key,'') for key in columns])
        for cell in sheet[sheet.max_row]:
            if isinstance(cell.value,str):cell.data_type='s'
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_suffix('.pending.xlsx')
    book.save(temporary)
    temporary.replace(path)
