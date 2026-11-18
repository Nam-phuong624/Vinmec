"""Pure identity rules shared by the importer and RPA; no OH writes."""
from dataclasses import dataclass
from datetime import date, datetime
import json
import re
import unicodedata


class ReviewRequired(ValueError):
    pass


def normalized(value: str) -> str:
    return ' '.join(unicodedata.normalize('NFC', str(value)).casefold().split())


def dob(value) -> str:
    if isinstance(value, (date, datetime)):
        return value.strftime('%Y-%m-%d')
    for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d%m%Y'):
        try:
            return datetime.strptime(str(value).strip(), fmt).strftime('%Y-%m-%d')
        except ValueError:
            continue
    raise ReviewRequired('Ngày sinh không hợp lệ.')


def national_id(value) -> str:
    if not isinstance(value, str) or not re.fullmatch(r'[0-9]{12}', value.strip()):
        raise ReviewRequired('CCCD phải là chuỗi 12 chữ số, giữ nguyên số 0 đầu.')
    return value.strip()


def visit_datetime(value) -> str:
    """Preserve an appointment time when the Excel field includes it."""
    if isinstance(value,datetime):
        return value.isoformat(sep=' ',timespec='seconds')
    if isinstance(value,date):return value.isoformat()
    text=str(value or '').strip()
    for fmt in ('%Y-%m-%d %H:%M:%S','%Y-%m-%dT%H:%M:%S','%Y-%m-%d %H:%M',
                '%d/%m/%Y %H:%M:%S','%d/%m/%Y %H:%M'):
        try:return datetime.strptime(text,fmt).isoformat(sep=' ',timespec='seconds')
        except ValueError:continue
    try:return dob(text)
    except ReviewRequired as exc:raise ReviewRequired('Ngày/giờ khám không hợp lệ.') from exc


@dataclass(frozen=True)
class Identity:
    national_id: str
    name: str
    dob: str
    sex: str = ''
    address: str = ''


def parse_scan(raw: str, mode: str = 'demo') -> Identity:
    """Demo uses JSON. QR pipe mode is explicit and must be verified per device."""
    try:
        if mode == 'demo':
            obj = json.loads(raw)
            if obj.get('format') != 'VINMEC-DEMO-1':
                raise ValueError()
        elif mode == 'qr-pipe':
            parts = raw.strip().split('|')
            if len(parts) != 7:
                raise ValueError()
            obj = dict(zip(('national_id', 'old_id', 'name', 'dob', 'sex', 'address', 'issued'), parts))
        else:
            raise ValueError()
        if not str(obj.get('name', '')).strip():
            raise ValueError()
        return Identity(national_id(obj['national_id']), str(obj['name']).strip(),
                        dob(obj['dob']), str(obj.get('sex', '')), str(obj.get('address', '')))
    except (ValueError, KeyError, TypeError, AttributeError) as exc:
        raise ReviewRequired('Chuỗi CCCD lỗi hoặc thiếu thông tin; quét lại và kiểm tra chế độ đọc.') from exc


def match_identity(identity: Identity, rows: list[dict], company: str, batch: str,
                   current: dict) -> dict:
    scoped = [r for r in rows if r['company'] == company and r['batch'] == batch]
    matches = [r for r in scoped if r['national_id'] == identity.national_id]
    if not matches:
        raise ReviewRequired('CCCD không có trong công ty/đợt khám đã chọn.')
    if len(matches) != 1:
        raise ReviewRequired('Trùng CCCD trong danh sách; kiểm tra các dòng nguồn.')
    row = matches[0]
    if row.get('blocked'):
        raise ReviewRequired('Trùng CCCD/PID trong file nguồn, kể cả dòng không đủ dữ liệu; kiểm tra danh sách.')
    if sum(r['pid'] == row['pid'] for r in scoped) != 1:
        raise ReviewRequired('Trùng PID trong danh sách; kiểm tra các dòng nguồn.')
    if not current or current.get('pid') != row['pid']:
        raise ReviewRequired(f"Sai PID đang mở. Excel: {row['pid']}; OH: {current.get('pid', 'chưa mở')}.")
    if current.get('company') != company or current.get('batch') != batch:
        raise ReviewRequired('Công ty/đợt khám trên OH khác danh sách đã chọn.')
    for source in (row, current):
        if normalized(source.get('name', '')) != normalized(identity.name):
            raise ReviewRequired('Họ tên CCCD, Excel và OH không khớp; kiểm tra thủ công.')
        if dob(source.get('dob', '')) != identity.dob:
            raise ReviewRequired('Ngày sinh CCCD, Excel và OH không khớp.')
    if current.get('national_id') and current['national_id'] != identity.national_id:
        raise ReviewRequired('CCCD đã có trên OH khác CCCD đang quét.')
    return row
