from copy import deepcopy
import json
import pytest
from openpyxl import load_workbook
from shared.paths import DEMO
from shared.excel import read_roster
from shared.identity import Identity, ReviewRequired, match_identity, parse_scan


def load_a():
    return read_roster(DEMO/'company_A.xlsx', 'DS_bung_DEMO', 'Công ty Demo A', 'DEMO-2026')


def person():
    return json.loads((DEMO/'patients.json').read_text(encoding='utf-8'))[0]


def identity():
    raw = json.loads((DEMO/'scans.json').read_text(encoding='utf-8'))[0]['scan']
    return parse_scan(raw)


def test_cccd_leading_zero_and_name_order():
    rows, errors = load_a()
    assert not errors and len(rows) == 10
    assert rows[0]['national_id'] == '000999000001'
    assert rows[0]['name'] == 'Nguyễn Văn An'
    assert match_identity(identity(), rows, 'Công ty Demo A', 'DEMO-2026', person()) == rows[0]


@pytest.mark.parametrize('value', [None, '', 123456789012, '123', '00099900000x'])
def test_any_missing_or_invalid_cccd_blocks_entire_excel(tmp_path, value):
    book = load_workbook(DEMO/'company_A.xlsx')
    book.active.cell(4,18).value = value
    path = tmp_path/'invalid.xlsx'; book.save(path)
    with pytest.raises(ReviewRequired, match='CCCD bắt buộc'):
        read_roster(path,'DS_bung_DEMO','A','B')


def test_wrong_sheet_and_headers_are_rejected():
    with pytest.raises(ReviewRequired): read_roster(DEMO/'company_A.xlsx','bad','A','B')
    with pytest.raises(ReviewRequired): read_roster(DEMO/'company_A.xlsx','DS_bung_DEMO','A','B',1)


@pytest.mark.parametrize('change', ['pid','dob','name','national_id','company','batch'])
def test_mismatched_oh_identity_is_blocked(change):
    rows, _ = load_a(); current = person()
    current[change] = '1999-01-01' if change == 'dob' else 'DIFFERENT'
    with pytest.raises(ReviewRequired):
        match_identity(identity(), rows, 'Công ty Demo A','DEMO-2026',current)


@pytest.mark.parametrize('key', ['national_id','pid'])
def test_duplicate_identifiers_block(key):
    rows, _ = load_a(); duplicate = deepcopy(rows[1]); duplicate[key]=rows[0][key]
    with pytest.raises(ReviewRequired, match='Trùng'):
        match_identity(identity(), rows+[duplicate], 'Công ty Demo A','DEMO-2026',person())


def test_same_name_does_not_select_wrong_person():
    rows, _ = load_a()
    assert rows[0]['name'] == rows[9]['name']
    assert match_identity(identity(),rows,'Công ty Demo A','DEMO-2026',person())['pid'] == 'DEMO0001'


@pytest.mark.parametrize('raw', ['', '{}', 'not-json', '[]', '{"format":"VINMEC-DEMO-1"}'])
def test_bad_scans_rejected(raw):
    with pytest.raises(ReviewRequired): parse_scan(raw)


def test_explicit_pipe_adapter():
    result = parse_scan('000999000001||Nguyễn Văn An|01031985|Nam|Địa chỉ cũ|01012020', 'qr-pipe')
    assert result.national_id == '000999000001' and result.dob == '1985-03-01'


def test_not_found_cccd_rejected():
    rows,_=load_a()
    with pytest.raises(ReviewRequired, match='không có'):
        match_identity(Identity('000999999999','Không Có','2000-01-01'),rows,'Công ty Demo A','DEMO-2026',person())


def test_custom_mapping_xlsm_and_formula_missing_value(tmp_path):
    from shared.excel import MAPPING
    book=load_workbook(DEMO/'company_A.xlsx')
    book.active.cell(2,18,'Số CCCD')
    mapping={**MAPPING,'national_id':'Số CCCD'}
    path=tmp_path/'custom.xlsm';book.save(path)
    rows,errors=read_roster(path,'DS_bung_DEMO','A','B',mapping=mapping)
    assert len(rows)==10 and not errors
    book.active.cell(3,18,'="000999000001"');book.save(path)
    with pytest.raises(ReviewRequired,match='CCCD bắt buộc'):
        read_roster(path,'DS_bung_DEMO','A','B',mapping=mapping)


def test_duplicate_file_reports_lines_and_blocks_affected_identity():
    rows,errors=read_roster(DEMO/'duplicates.xlsx','DS_bung_DEMO','Công ty Demo A','DEMO-2026')
    assert any('Dòng 3' in error for error in errors)
    with pytest.raises(ReviewRequired,match='Trùng'):
        match_identity(identity(),rows,'Công ty Demo A','DEMO-2026',person())


def test_duplicate_cccd_on_invalid_pid_row_cannot_be_silently_ignored(tmp_path):
    book=load_workbook(DEMO/'company_A.xlsx')
    book.active.cell(4,1).value=None
    book.active.cell(4,18).value=book.active.cell(3,18).value
    path=tmp_path/'duplicate-invalid-row.xlsx';book.save(path)
    rows,errors=read_roster(path,'DS_bung_DEMO','Công ty Demo A','DEMO-2026')
    assert errors
    with pytest.raises(ReviewRequired,match='Trùng'):
        match_identity(identity(),rows,'Công ty Demo A','DEMO-2026',person())
