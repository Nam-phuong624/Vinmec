"""Chuẩn bị dữ liệu quay demo (toàn bộ là dữ liệu GIẢ).

- Cất file/thư mục cũ của ngày hôm nay (ds lỗi, phieu_in, file Excel khác) sang thư mục sao lưu, không xóa.
- Ghi 1 file ds bung mới gồm 7 dòng, mỗi dòng ứng với một kết quả khác nhau của RPA.
Chạy:  python chuan_bi_demo.py        (chạy lại để đưa dữ liệu về trạng thái ban đầu trước mỗi lần quay)
"""
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from openpyxl import Workbook

ROOT = Path(__file__).resolve().parents[2]
DS_BUNG = ROOT / 'ds bung'
TODAY = datetime.now()
FOLDER = DS_BUNG / TODAY.strftime('%d-%m-%Y')
BACKUP = ROOT.parent / f'ds bung_truoc_demo_{TODAY:%d-%m-%Y_%H%M%S}'
FILE = FOLDER / f'DS_bung_{TODAY:%Y%m%d}_demo_{TODAY:%H%M%S}.xlsx'

HEADER = ['Patient ID', 'Title', 'Patient Given Name', 'Patient Middle Name', 'Patient Last Name', 'Date Of Birth', 'Sex',
          'Patient Address', 'Business Phone Number', 'Nationality', 'Policy Code', 'Policy Name', 'Package Code', 'Package Name',
          'Visit Date Time', 'Patient Work Queue', 'Attending Doctor Number', 'National ID', 'Passport Number',
          'Requesting Cost Centre', 'Pricing Class']
CO_BAN, TIEU_CHUAN = 'Gói khám sức khỏe tổng quát cơ bản', 'Gói khám sức khỏe tổng quát tiêu chuẩn'


def row(pid, title, given, middle, last, dob, sex, addr, phone, pkg, cccd):
    pcode = 'PKG-01' if pkg == CO_BAN else 'PKG-02'
    return [pid, title, given, middle, last, dob, sex, addr, phone, 'Việt Nam', 'POL-DEMO', 'Công ty TNHH Demo', pcode, pkg,
            None, None, None, cccd, None, None, None]


# (kết quả RPA mong đợi, dòng dữ liệu)
ROWS = [
    ('Đã cập nhật (trùng DEMO0001: cùng tên + năm sinh 1980; Excel có địa chỉ mới)',
     row('VM101', 'Ông', 'Mẫu', 'Văn', 'Nguyễn', '15/02/1980', 'Nam', 'Số 10 Đường Láng, Phường Láng Hạ, Hà Nội', '0900000001', CO_BAN, '001080000101')),
    ('Đã tạo (người mới)',
     row('VM102', 'Ông', 'Long', 'Hoàng', 'Lê', '08/07/1988', 'Nam', '25 Nguyễn Trãi, Phường Thanh Xuân, Hà Nội', '0912000102', CO_BAN, '001088000102')),
    ('Đã tạo (người mới, nữ, gói tiêu chuẩn)',
     row('VM103', 'Bà', 'Hà', 'Thu', 'Phạm', '14/11/1992', 'Nữ', 'Xã Kiều Phú, Hà Nội', '0912000103', TIEU_CHUAN, '001192000103')),
    ('Đã tạo (người mới, nam, gói tiêu chuẩn)',
     row('VM104', 'Ông', 'Quân', 'Minh', 'Đỗ', '30/03/1979', 'Nam', '7 Hàng Bài, Phường Hàng Bài, Hà Nội', '0912000104', TIEU_CHUAN, '001079000104')),
    ('Cần điền tay (địa chỉ chỉ có 1 phần)',
     row('VM105', 'Bà', 'Lan', 'Thị', 'Vũ', '02/09/1985', 'Nữ', 'Hà Nội', '0912000105', CO_BAN, '001185000105')),
    ('LỖI (SĐT mất số 0 đầu do Excel) → ghi vào ds lỗi.xlsx, không nhập vào OH',
     row('VM106', 'Ông', 'Bình', 'Văn', 'Hoàng', '19/12/1983', 'Nam', '3 Tây Sơn, Phường Quang Trung, Hà Nội', 912000106, CO_BAN, '001083000106')),
    ('LỖI (tên có chữ số) → ghi vào ds lỗi.xlsx, không nhập vào OH',
     row('VM107', 'Bà', 'Mai2', 'Thị', 'Bùi', '05/05/1991', 'Nữ', '9 Chùa Bộc, Phường Trung Liệt, Hà Nội', '0912000107', TIEU_CHUAN, '001191000107')),
]


# Người thật của chính người quay (CCCD, SĐT) KHÔNG nằm trong repo: đọc từ rieng_tu.json (đã .gitignore), nếu có.
# Mẫu: {"nguoi": [{"pid": "VM108", "title": "Ông", "given": "Nam", "middle": "Trần Phương", "last": "Chử", "dob": "06/02/2004",
#                  "sex": "Nam", "addr": "...", "phone": "...", "cccd": "...", "goi": "tieuchuan"}]}
PRIVATE = Path(__file__).with_name('rieng_tu.json')
if PRIVATE.exists():
    for n in json.loads(PRIVATE.read_text(encoding='utf-8')).get('nguoi', []):
        pkg = CO_BAN if n.get('goi') == 'coban' else TIEU_CHUAN
        ROWS.append(('Đã tạo (người quay demo; dùng để quét CCCD ở In_Phieu)',
                     row(n['pid'], n['title'], n['given'], n['middle'], n['last'], n['dob'], n['sex'], n['addr'], n['phone'], pkg, n['cccd'])))


def main():
    FOLDER.mkdir(parents=True, exist_ok=True)
    moved = []
    for item in FOLDER.iterdir():
        if item.name == FILE.name:
            continue
        BACKUP.mkdir(exist_ok=True)
        try:
            shutil.move(str(item), str(BACKUP / item.name))
            moved.append(item.name)
        except PermissionError:
            print(f'CẢNH BÁO: "{item.name}" đang được mở bởi chương trình khác (Excel/Word?), chưa cất được. Đóng nó rồi chạy lại.')
    wb = Workbook()
    ws = wb.active
    ws.append(['Main (Mandatory)'] + [None] * (len(HEADER) - 1))
    ws.append(HEADER)
    for _, data in ROWS:
        ws.append(data)
    for col in ws.columns:
        ws.column_dimensions[col[0].column_letter].width = 22
    wb.save(FILE)
    print(f'Đã ghi {FILE} ({len(ROWS)} dòng)')
    if moved:
        print(f'Đã cất {len(moved)} mục cũ sang {BACKUP}: ' + ', '.join(moved))
    print('Kết quả mong đợi:')
    for i, (expect, _) in enumerate(ROWS, 1):
        print(f'  dòng {i}: {expect}')


if __name__ == '__main__':
    sys.exit(main())
