"""Generate fictional fixtures; never load the private reference workbook."""
import json
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from shared.paths import DEMO

HEADERS = ['Patient ID', 'Title', 'Patient Given Name', 'Patient Middle Name', 'Patient Last Name',
           'Date Of Birth', 'Sex', 'Patient Address', 'Business Phone Number', 'Nationality',
           'Policy Code', 'Policy Name', 'Package Code', 'Package Name', 'Visit Date Time',
           'Patient Work Queue', 'Attending Doctor Number', 'National ID', 'Passport Number',
           'Requesting Cost Centre', 'Pricing Class']


def workbook(path, people, broken=False):
    book = Workbook()
    ws = book.active
    ws.title = 'DS_bung_DEMO'
    ws.append(['Main (Mandatory) — DỮ LIỆU GIẢ'])
    ws.append(HEADERS)
    for p in people:
        last, middle, given = p['name'].split(' ', 2)
        ws.append([p['pid'], 'Ông' if p['sex'] == 'Nam' else 'Bà', given, middle, last,
                   p['dob'], p['sex'], p['address_original'], p.get('phone',''), p.get('nationality','Việt Nam'),
                   p.get('policy_code',''), p.get('policy_name',''), p.get('package_code',''),p.get('package_name',''),
                   p.get('visit_date','2026-11-17'), '', '', p['demo_national_id'], '', '', ''])
    if broken:
        # A duplicate CCCD, a duplicate PID, and an invalid numeric identifier.
        ws.cell(4, 18, ws.cell(3, 18).value)
        ws.cell(6, 1, ws.cell(5, 1).value)
        if broken != 'duplicates':
            ws.cell(7, 18, 123)
    for c in ws[2]:
        c.font = Font(color='FFFFFF', bold=True)
        c.fill = PatternFill('solid', fgColor='186B78')
    ws.freeze_panes = 'A3'
    ws.column_dimensions['A'].width = 18
    ws.column_dimensions['R'].width = 20
    book.save(path)


def main():
    DEMO.mkdir(exist_ok=True)
    names = ['Nguyễn Văn An', 'Trần Thị Bình', 'Lê Minh Châu', 'Phạm Hoàng Dũng', 'Vũ Ngọc Hà',
             'Đặng Thị Lan', 'Bùi Quang Minh', 'Đỗ Tuấn Nam', 'Hồ Thu Phương', 'Nguyễn Văn An']
    patients, scans = [], []
    for i in range(20):
        company = 'Công ty Demo A' if i < 10 else 'Công ty Demo B'
        identity = dict(format='VINMEC-DEMO-1', national_id=f'000999{i+1:06d}', name=names[i % 10],
                        dob=f'{1985 + i % 12}-03-{i % 20 + 1:02d}', sex='Nam' if i % 2 == 0 else 'Nữ',
                        address='Địa chỉ cũ giả lập')
        person = dict(pid=f'DEMO{i+1:04d}', name=identity['name'], dob=identity['dob'], sex=identity['sex'],
                      national_id='' if i % 2 == 0 else identity['national_id'],
                      demo_national_id=identity['national_id'], company=company, batch='DEMO-2026',
                      address=dict(province='Thành phố Demo', ward='Phường Cũ', street=f'{i+1} Đường Mẫu'),
                      address_original='Địa chỉ cũ giả lập')
        patients.append(person)
        scans.append(dict(pid=person['pid'], company=company, scan=json.dumps(identity, ensure_ascii=False)))
    (DEMO / 'patients.json').write_text(json.dumps(patients, ensure_ascii=False, indent=2), encoding='utf-8')
    (DEMO / 'scans.json').write_text(json.dumps(scans, ensure_ascii=False, indent=2), encoding='utf-8')
    for letter, group in (('A', patients[:10]), ('B', patients[10:])):
        workbook(DEMO / f'company_{letter}.xlsx', group)
    workbook(DEMO / 'errors.xlsx', patients[:10], broken=True)
    workbook(DEMO / 'duplicates.xlsx', patients[:10], broken='duplicates')
    newcomers=[];new_scans=[]
    for i,name in enumerate(['Nguyễn Minh Anh','Trần Ngọc Mai','Lê Hoàng Sơn']):
        person=dict(pid='',name=name,dob=f'199{i}-05-12',sex='Nữ' if i<2 else 'Nam',
                    demo_national_id=f'000888{i+1:06d}',address_original=f'{i+1} Đường Mẫu, địa chỉ nguồn Excel',
                    phone=f'090000000{i}',nationality='Việt Nam',policy_code='HD-DEMO-A',policy_name='Hợp đồng Demo A',
                    package_code='KSK-A01',package_name='Khám sức khỏe định kỳ Demo A',visit_date='2026-11-18')
        newcomers.append(person)
        scan=dict(format='VINMEC-DEMO-1',national_id=person['demo_national_id'],name=name,dob=person['dob'],
                  sex=person['sex'],address=person['address_original'])
        new_scans.append(dict(pid='',company='Công ty Demo A',scan=json.dumps(scan,ensure_ascii=False)))
    workbook(DEMO/'new_customers_A.xlsx',newcomers)
    (DEMO/'new_scans.json').write_text(json.dumps(new_scans,ensure_ascii=False,indent=2),encoding='utf-8')
    (DEMO / 'cards.html').write_text('<!doctype html><meta charset="utf-8"><title>Thẻ demo</title>'
        '<style>body{font:16px Arial}article{border:1px solid;padding:16px;break-inside:avoid;margin:12px}pre{white-space:pre-wrap;overflow-wrap:anywhere}</style>'
        '<h1>Thẻ demo — dữ liệu giả, không phải CCCD thật</h1>' + ''.join(
            f"<article><b>{p['pid']} · {p['company']}</b><p>{p['name']}</p><pre>{s['scan']}</pre></article>"
            for p, s in zip(patients, scans)), encoding='utf-8')
    print('Generated 20 fictional patients, company A/B workbooks, error fixtures and demo cards.')


if __name__ == '__main__':
    main()
