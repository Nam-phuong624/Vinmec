"""Chuyển workbook công khai của NSO sang dữ liệu tĩnh, không cần thư viện ngoài."""
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path
import xml.etree.ElementTree as ET

source = Path(sys.argv[1])
ns = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
with zipfile.ZipFile(source) as archive:
    strings = [''.join(item.itertext()) for item in ET.fromstring(archive.read('xl/sharedStrings.xml')).findall('s:si', ns)]
    sheet = ET.fromstring(archive.read('xl/worksheets/sheet2.xml'))
    records = []
    for row in sheet.findall('.//s:sheetData/s:row', ns)[2:]:
        cells = {}
        for cell in row.findall('s:c', ns):
            value = cell.find('s:v', ns)
            value = value.text if value is not None else ''
            cells[re.sub(r'\d', '', cell.get('r'))] = (strings[int(value)] if cell.get('t') == 's' and value else value).strip()
        if not cells.get('C') or not cells.get('E'):
            continue
        records.append([cells.get(col, '') for col in 'ABCDEFGH'])
data = {
    'source': 'https://danhmuchanhchinh.nso.gov.vn/TAPTIN/BangChuyendoiĐVHCmoi_cu_final.xlsx',
    'retrievedAt': '2026-11-10',
    'effectiveFrom': '2025-07-01',
    'sheet': 'Tổng hợp_không merge ',
    'sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
    'columns': ['newProvince', 'newCommune', 'newCode', 'oldCommune', 'oldCode', 'change', 'oldDistrict', 'oldProvince'],
    'records': records,
}
Path(__file__).with_name('data.js').write_text('window.ADDRESS_DATA = ' + json.dumps(data, ensure_ascii=False, separators=(',', ':')) + ';\n', encoding='utf-8')
print(f'Imported {len(records)} source rows; SHA256 {data["sha256"]}')
