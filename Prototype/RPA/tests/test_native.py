import json
import subprocess
import time
from threading import Event
import pytest
from pywinauto.timings import wait_until
from shared.paths import DEMO, ROOT
from shared.excel import read_roster
from shared.identity import parse_scan, ReviewRequired

ADDRESS={'province':'Thành phố Demo','ward':'Phường Mới','street':'12 Đường Demo'}


def prepare(engine,index=0):
    scan=json.loads((DEMO/'scans.json').read_text(encoding='utf-8'))[index]
    letter='A' if index<10 else 'B'
    rows,_=read_roster(DEMO/f'company_{letter}.xlsx','DS_bung_DEMO',scan['company'],'DEMO-2026')
    return engine.prepare(parse_scan(scan['scan']),rows,scan['company'],'DEMO-2026')


def save_and_wait(engine):
    before=engine.read('version')
    engine.click('save-record')
    wait_until(8,.05,lambda:engine.read('version')!=before)


def test_native_complete_flow_and_readback(native_app):
    engine,_,_=native_app
    engine.open_pid('DEMO0001')
    proposal=prepare(engine)
    pending=engine.fill(proposal,ADDRESS,True)
    assert engine.snapshot()['record']['address']==ADDRESS
    assert not engine.verify_saved(pending)
    save_and_wait(engine)
    assert engine.verify_saved(pending)
    assert not engine.snapshot()['dirty']


def test_native_wrong_pid_changed_preview_and_reload(native_app):
    engine,_,_=native_app
    engine.open_pid('DEMO0002')
    with pytest.raises(ReviewRequired,match='Sai PID'): prepare(engine)
    engine.open_pid('DEMO0001');proposal=prepare(engine)
    engine.write('national_id','000999000001')
    with pytest.raises(ReviewRequired,match='bị sửa'):engine.fill(proposal,ADDRESS,True)
    with pytest.raises(ReviewRequired,match='chưa lưu'):prepare(engine)
    engine.click('cancel-record')
    proposal=prepare(engine)
    engine.open_pid('DEMO0002')
    with pytest.raises(ReviewRequired,match='Hồ sơ đã đổi'):engine.fill(proposal,ADDRESS,True)


def test_native_confirmation_and_stop(native_app,monkeypatch):
    engine,_,path=native_app
    engine.open_pid('DEMO0001');proposal=prepare(engine)
    with pytest.raises(ReviewRequired,match='xác nhận'):engine.fill(proposal,ADDRESS,False)
    stop=Event();stop.set()
    with pytest.raises(ReviewRequired,match='Đã dừng'):engine.fill(proposal,ADDRESS,True,stop)
    stop.clear();check=engine.check
    def checked(*args,**kwargs):
        if engine.read('national_id'):stop.set()
        return check(*args,**kwargs)
    monkeypatch.setattr(engine,'check',checked)
    with pytest.raises(ReviewRequired,match='Đã dừng'):engine.fill(proposal,ADDRESS,True,stop)
    assert not engine.snapshot()['locked'] and engine.snapshot()['dirty']
    from oh_desktop.store import get
    assert get(path,'DEMO0001')['national_id']==''
    engine.click('cancel-record')
    assert engine.read('national_id')==''


def test_native_conflicting_save_is_not_completed(native_app):
    engine,_,path=native_app
    engine.open_pid('DEMO0001');pending=engine.fill(prepare(engine),ADDRESS,True)
    # A second writer is a test setup action; the RPA itself never touches storage.
    from oh_desktop.store import get,save
    other=get(path,'DEMO0001');other['address']['ward']='Phường khác';save(path,other)
    engine.click('save-record')
    wait_until(5,.05,lambda:'Hồ sơ đã thay đổi' in engine.read('message'))
    assert not engine.verify_saved(pending)
    assert engine.snapshot()['dirty']


def test_native_repeated_fill_and_modal_cancel(native_app):
    engine,_,_=native_app
    engine.open_pid('DEMO0001');pending=engine.fill(prepare(engine),ADDRESS,True)
    save_and_wait(engine);assert engine.verify_saved(pending)
    again=engine.fill(prepare(engine),ADDRESS,True)
    assert not engine.snapshot()['dirty']
    assert not engine.verify_saved(again)
    engine.click('edit-address');dialog=engine.address_dialog();hwnd=dialog.handle
    engine.write('address-ward','Chưa áp dụng',dialog);engine.click('close-address',dialog)
    import win32gui
    wait_until(5,.05,lambda:not win32gui.IsWindow(hwnd))
    assert engine.snapshot()['record']['address']==ADDRESS


def test_native_unknown_pid_and_lock(native_app):
    engine,_,_=native_app
    with pytest.raises(ReviewRequired,match='chưa mở'):engine.snapshot()
    engine.open_pid('DEMO0001');engine.click('lock-record')
    for name in ('pid-search','open-record','save-record','reload-record','cancel-record'):
        assert not engine.control(name,'Edit' if name=='pid-search' else 'Button').is_enabled()
    engine.click('lock-record')
    with pytest.raises(ReviewRequired,match='chưa mở'):engine.open_pid('UNKNOWN')
    assert 'Không tìm thấy PID' in engine.read('message')


def test_native_closed_window_and_missing_control(native_app):
    engine,process,_=native_app
    engine.open_pid('DEMO0001');proposal=prepare(engine)
    engine.window.close();process.wait(timeout=5)
    with pytest.raises(Exception):engine.fill(proposal,ADDRESS,True)


def test_native_timing_and_screenshots(native_app):
    engine,_,_=native_app
    evidence=ROOT/'docs'/'native-evidence';evidence.mkdir(exist_ok=True)
    timings=[]
    for i in range(20):
        engine.open_pid(f'DEMO{i+1:04d}')
        pending=engine.fill(prepare(engine,i),ADDRESS,True)
        timings.append(round(pending['elapsed_ms'],1))
        save_and_wait(engine);assert engine.verify_saved(pending)
    report=dict(samples=20,milliseconds=timings,under_5000ms=sum(v<=5000 for v in timings),
                mode='Native WinForms + pywinauto Windows UI Automation; visible desktop',
                excludes='Human address confirmation and save time')
    (ROOT/'docs'/'native-timing.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    engine.open_pid('DEMO0001');engine.window.set_focus()
    subprocess.run(['powershell','-NoProfile','-File',str(ROOT/'scripts'/'capture_window.ps1'),
                    '-WindowHandle',str(engine.handle),'-Destination',str(evidence/'oh-native.png')],check=True,capture_output=True)
    engine.click('edit-address');dialog=engine.address_dialog()
    subprocess.run(['powershell','-NoProfile','-File',str(ROOT/'scripts'/'capture_window.ps1'),
                    '-WindowHandle',str(dialog.handle),'-Destination',str(evidence/'oh-native-address.png')],check=True,capture_output=True)
    engine.click('close-address',dialog)
    assert report['under_5000ms']>=19
