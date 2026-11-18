import subprocess
import win32gui
from pywinauto.timings import wait_until
from shared.paths import ROOT
from oh_desktop.store import initialize,search_patients,create
from shared.excel import read_preparation
from shared.paths import DEMO


def test_browse_store_searches_names_ids_and_company_with_pagination(tmp_path):
    path=tmp_path/'oh.sqlite3';initialize(path)
    all_rows=search_patients(path)
    assert all_rows['total']==20 and all_rows['items'][0]['pid']=='DEMO0020'
    assert search_patients(path,'nguyen an')['total']==4
    assert search_patients(path,'DEMO0001')['items'][0]['name']=='Nguyễn Văn An'
    assert search_patients(path,'000999000002')['items'][0]['pid']=='DEMO0002'
    assert search_patients(path,'cong ty demo b')['total']==10
    first=search_patients(path,limit=5);second=search_patients(path,offset=5,limit=5)
    assert len(first['items'])==len(second['items'])==5 and first['items'][0]!=second['items'][0]
    assert search_patients(path,'khong co nguoi nay')['total']==0


def open_browser(engine,button='browse-patients'):
    engine.click(button)
    handle=engine.find_window('OH · Danh sách hồ sơ')
    dialog=engine.app.window(handle=handle);dialog.wait('visible',timeout=8)
    engine.cache_controls(dialog,handle)
    wait_until(8,.05,lambda:'Đang nạp' not in engine.read('patient-count',dialog))
    return dialog


def search(engine,dialog,text):
    engine.write('patient-query',text,dialog);engine.click('patient-search',dialog)


def test_native_patient_list_search_open_without_remembering_pid(native_app):
    engine,_,_=native_app
    dialog=open_browser(engine)
    assert 'Tổng 20' in engine.read('patient-count',dialog)
    search(engine,dialog,'Tran Thi Binh')
    assert 'Tổng 2' in engine.read('patient-count',dialog)
    # Opening the automatically selected search result requires no PID input.
    handle=dialog.handle;engine.click('patient-open',dialog)
    wait_until(8,.05,lambda:not win32gui.IsWindow(handle))
    wait_until(8,.05,lambda:engine.read('name')=='Trần Thị Bình')
    assert engine.snapshot()['record']['pid'] in ('DEMO0002','DEMO0012')
    assert engine.read('pid-search')==engine.read('pid')


def test_browser_includes_newly_created_records_and_handles_empty_results(native_app):
    engine,_,path=native_app
    source=read_preparation(DEMO/'new_customers_A.xlsx','DS_bung_DEMO','Công ty Demo A','DEMO-2026')[0][0]
    saved=create(path,dict(source,address_original=source['address']))
    dialog=open_browser(engine,'nav-patient-list')
    assert 'Tổng 21' in engine.read('patient-count',dialog)
    search(engine,dialog,source['national_id'])
    assert 'Tổng 1' in engine.read('patient-count',dialog)
    engine.click('patient-open',dialog)
    wait_until(8,.05,lambda:engine.read('pid')==saved['pid'])
    dialog=open_browser(engine)
    search(engine,dialog,'nobody-matches-this')
    assert 'Không tìm thấy' in engine.read('patient-count',dialog)
    assert not engine.control('patient-open','Button',dialog).is_enabled()
    engine.click('patient-close',dialog)
    assert engine.read('pid')==saved['pid']


def test_browser_guards_unsaved_changes_and_native_render(native_app):
    engine,_,_=native_app;engine.open_pid('DEMO0001')
    engine.write('national_id','000999000001')
    engine.click('browse-patients')
    wait_until(5,.05,lambda:'Lưu hoặc hủy' in engine.read('message'))
    assert engine.read('pid')=='DEMO0001'
    engine.click('cancel-record')
    dialog=open_browser(engine)
    folder=ROOT/'docs'/'patient-browser-evidence';folder.mkdir(exist_ok=True)
    subprocess.run(['powershell','-NoProfile','-File',str(ROOT/'scripts'/'capture_window.ps1'),
                    '-WindowHandle',str(dialog.handle),'-Destination',str(folder/'patient-list.png')],check=True,capture_output=True)
    engine.click('patient-close',dialog)


def test_native_browser_pages_through_all_records(native_app):
    engine,_,path=native_app
    source=read_preparation(DEMO/'new_customers_A.xlsx','DS_bung_DEMO','Công ty Demo A','DEMO-2026')[0][0]
    for i in range(55):
        create(path,dict(source,national_id=f'000777{i+1:06d}',name=f'Khách thử {i+1}',address_original=source['address']))
    dialog=open_browser(engine)
    assert '1–50 / Tổng 75' in engine.read('patient-count',dialog)
    assert not engine.control('patient-previous','Button',dialog).is_enabled()
    engine.click('patient-next',dialog)
    assert '51–75 / Tổng 75' in engine.read('patient-count',dialog)
    assert not engine.control('patient-next','Button',dialog).is_enabled()
    engine.click('patient-previous',dialog)
    assert '1–50 / Tổng 75' in engine.read('patient-count',dialog)
    engine.click('patient-close',dialog)
