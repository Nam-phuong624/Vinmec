import json
from concurrent.futures import ThreadPoolExecutor
from threading import Event
import pytest
from openpyxl import load_workbook
from pywinauto.timings import wait_until
import win32gui
from shared.excel import read_preparation,read_roster,export_prepared
from shared.identity import ReviewRequired,parse_scan
from shared.paths import DEMO,ROOT
from oh_desktop.store import create,find_by_cccd,initialize,get


def rows():
    return read_preparation(DEMO/'new_customers_A.xlsx','DS_bung_DEMO','Công ty Demo A','DEMO-2026')[0]


def record(row):
    return dict(row,address_original=row['address'])


def test_new_roster_allows_empty_or_absent_pid_and_exports_handoff(tmp_path):
    source=rows();assert len(source)==3 and all(not r['pid'] for r in source)
    assert source[0]['package_code']=='KSK-A01'
    book=load_workbook(DEMO/'new_customers_A.xlsx');book.active.delete_cols(1)
    file=tmp_path/'no-pid.xlsx';book.save(file)
    assert len(read_preparation(file,'DS_bung_DEMO','A','B')[0])==3
    with pytest.raises(ReviewRequired):export_prepared(tmp_path/'not-ready.xlsx',source)
    handoff=[dict(source[0],pid='NEW000001')];output=tmp_path/'handoff.xlsx';export_prepared(output,handoff)
    reread,errors=read_roster(output,'DS_bung_DEMO','Công ty Demo A','DEMO-2026')
    assert not errors and reread[0]['pid']=='NEW000001'
    assert reread[0]['national_id']=='000888000001' and reread[0]['package_code']=='KSK-A01'


def test_preparation_cccd_and_package_are_required(tmp_path):
    book=load_workbook(DEMO/'new_customers_A.xlsx');book.active.cell(3,18).value=None
    path=tmp_path/'bad.xlsx';book.save(path)
    with pytest.raises(ReviewRequired,match='CCCD bắt buộc'):read_preparation(path,'DS_bung_DEMO','A','B')
    book=load_workbook(DEMO/'new_customers_A.xlsx');book.active.cell(3,13).value=None;book.save(path)
    valid,errors=read_preparation(path,'DS_bung_DEMO','A','B')
    assert len(valid)==2 and any('mã gói' in e for e in errors)


def test_appointment_time_is_preserved_through_create_and_export(tmp_path):
    from datetime import datetime
    book=load_workbook(DEMO/'new_customers_A.xlsx');book.active.cell(3,15).value=datetime(2026,11,18,7,30)
    path=tmp_path/'appointment.xlsx';book.save(path)
    source=read_preparation(path,'DS_bung_DEMO','Công ty Demo A','DEMO-2026')[0][0]
    assert source['visit_date']=='2026-11-18 07:30:00'
    database=tmp_path/'oh.sqlite3';initialize(database)
    saved=create(database,record(source));assert saved['visit_date']==source['visit_date']
    output=tmp_path/'handoff.xlsx';export_prepared(output,[dict(source,pid=saved['pid'])])
    assert read_roster(output,'DS_bung_DEMO','Công ty Demo A','DEMO-2026')[0][0]['visit_date']==source['visit_date']


def test_oh_allocates_pid_and_preserves_package_with_atomic_duplicate_guard(tmp_path):
    path=tmp_path/'oh.sqlite3';initialize(path);person=record(rows()[0])
    def attempt():
        try:return create(path,person)['pid']
        except ValueError:return 'blocked'
    with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(lambda _:attempt(),range(2)))
    assert sorted(results)==['NEW000001','blocked']
    saved=find_by_cccd(path,person['national_id'])
    assert saved['package_code']=='KSK-A01' and saved['visit_date']=='2026-11-18'
    assert saved['address']['province']==''  # no invented post-merger address


def save_creation(engine,pending):
    dialog=engine.app.window(handle=pending['dialog_handle'])
    engine.click('create-save',dialog)
    wait_until(8,.05,lambda:not win32gui.IsWindow(pending['dialog_handle']))
    return engine.verify_creation(pending)


def test_native_two_stage_end_to_end(native_app,tmp_path):
    engine,_,path=native_app
    source=rows()[0]
    pending=engine.fill_creation(source)
    assert engine.verify_creation(pending) is None
    completed=save_creation(engine,pending)
    assert completed['pid'].startswith('NEW')
    output=tmp_path/'ready.xlsx';export_prepared(output,[completed])
    roster,_=read_roster(output,'DS_bung_DEMO','Công ty Demo A','DEMO-2026')
    engine.open_pid(completed['pid'])
    scan=json.loads((DEMO/'new_scans.json').read_text(encoding='utf-8'))[0]['scan']
    proposal=engine.prepare(parse_scan(scan),roster,'Công ty Demo A','DEMO-2026')
    address={'province':'Thành phố Demo','ward':'Phường Mới','street':'12 Đường Demo'}
    reception=engine.fill(proposal,address,True)
    before=engine.read('version');engine.click('save-record')
    wait_until(8,.05,lambda:engine.read('version')!=before)
    assert engine.verify_saved(reception)
    saved=get(path,completed['pid'])
    assert saved['package_code']=='KSK-A01' and saved['address']==address
    assert saved['national_id']==source['national_id']
    with pytest.raises(ReviewRequired,match='đã có hồ sơ PID'):engine.fill_creation(source)
    with pytest.raises(ReviewRequired,match='đã có PID'):engine.fill_creation(completed)


def test_creation_cancel_and_stop_do_not_create_pid(native_app):
    engine,_,path=native_app;source=rows()[0]
    stop=Event();stop.set()
    with pytest.raises(ReviewRequired,match='Đã dừng'):engine.fill_creation(source,stop)
    pending=engine.fill_creation(source)
    engine.click('create-cancel',engine.app.window(handle=pending['dialog_handle']))
    wait_until(5,.05,lambda:not win32gui.IsWindow(pending['dialog_handle']))
    with pytest.raises(ReviewRequired):engine.verify_creation(pending)
    assert not find_by_cccd(path,source['national_id'])


def test_creation_changed_saved_package_not_exported(native_app):
    engine,_,path=native_app;pending=engine.fill_creation(rows()[0])
    dialog=engine.app.window(handle=pending['dialog_handle'])
    engine.write('create-package_code','OTHER-PACKAGE',dialog)
    engine.click('create-save',dialog)
    wait_until(8,.05,lambda:not win32gui.IsWindow(pending['dialog_handle']))
    with pytest.raises(ReviewRequired,match='khác Excel'):engine.verify_creation(pending)


def test_stop_during_creation_closes_form_and_allocates_nothing(native_app,monkeypatch):
    engine,_,path=native_app;source=rows()[0];stop=Event();write=engine.write
    def typed(name,value,parent=None):
        result=write(name,value,parent)
        if name=='create-national_id':stop.set()
        return result
    monkeypatch.setattr(engine,'write',typed)
    with pytest.raises(ReviewRequired,match='Đã dừng'):engine.fill_creation(source,stop)
    assert not find_by_cccd(path,source['national_id'])


def test_creation_native_evidence(native_app):
    import subprocess
    engine,_,_=native_app;pending=engine.fill_creation(rows()[0])
    evidence=ROOT/'docs'/'two-stage-evidence';evidence.mkdir(exist_ok=True)
    dialog=engine.app.window(handle=pending['dialog_handle'])
    subprocess.run(['powershell','-NoProfile','-File',str(ROOT/'scripts'/'capture_window.ps1'),
                    '-WindowHandle',str(dialog.handle),'-Destination',str(evidence/'stage1-create.png')],check=True,capture_output=True)
    completed=save_creation(engine,pending)
    subprocess.run(['powershell','-NoProfile','-File',str(ROOT/'scripts'/'capture_window.ps1'),
                    '-WindowHandle',str(engine.handle),'-Destination',str(evidence/'stage1-pid-created.png')],check=True,capture_output=True)
