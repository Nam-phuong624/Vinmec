"""Quy tắc chuẩn hóa ngày và CCCD dùng chung; không ghi vào OH."""
from datetime import date, datetime
import re


class ReviewRequired(ValueError):
    pass


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
