import json
import time
from threading import Event
import pytest
from playwright.sync_api import expect
from shared.paths import DEMO, ROOT
from shared.excel import read_roster
from shared.identity import ReviewRequired, parse_scan
from rpa_tool.engine import BrowserRPA

ADDRESS={'province':'Thành phố Demo','ward':'Phường Mới','street':'12 Đường Demo'}


def open_pid(page,pid='DEMO0001'):
    page.locator('#pid-input').fill(pid)
    page.locator('#open-record').click()
    page.wait_for_function('(pid)=>window.ohSnapshot?.()?.record.pid===pid && !window.ohSnapshot().loading',arg=pid)


def prepare(page,index=0):
    letter='A' if index<10 else 'B'
    scans=json.loads((DEMO/'scans.json').read_text(encoding='utf-8'))
    scan=scans[index]
    rows,_=read_roster(DEMO/f'company_{letter}.xlsx','DS_bung_DEMO',scan['company'],'DEMO-2026')
    engine=BrowserRPA(page)
    return engine,engine.prepare(parse_scan(scan['scan']),rows,scan['company'],'DEMO-2026')


def test_complete_flow_persists_and_repeat_is_idempotent(page):
    open_pid(page)
    engine,proposal=prepare(page)
    with pytest.raises(ReviewRequired,match='xác nhận'): engine.fill(proposal,ADDRESS,False)
    pending=engine.fill(proposal,ADDRESS,True)
    assert engine.snapshot()['record']['address']==ADDRESS
    assert not engine.verify_saved(pending)
    page.locator('#save').click()
    expect(page.locator('#message')).to_contain_text('thành công')
    assert engine.verify_saved(pending)
    engine,proposal=prepare(page)
    again=engine.fill(proposal,ADDRESS,True)
    assert engine.snapshot()['record']['address']==ADDRESS
    assert isinstance(engine.snapshot()['record']['address'],dict)
    assert not engine.verify_saved(again)


def test_wrong_pid_and_external_edit_block(page):
    open_pid(page,'DEMO0002')
    with pytest.raises(ReviewRequired,match='Sai PID'): prepare(page)
    open_pid(page)
    engine,proposal=prepare(page)
    page.locator('#national-id').fill('000999000001')
    with pytest.raises(ReviewRequired,match='bị sửa'): engine.fill(proposal,ADDRESS,True)
    with pytest.raises(ReviewRequired,match='chưa lưu'): prepare(page)


def test_switch_patient_after_preview(page):
    open_pid(page);engine,proposal=prepare(page)
    open_pid(page,'DEMO0002')
    with pytest.raises(ReviewRequired,match='Hồ sơ đã đổi'): engine.fill(proposal,ADDRESS,True)
    assert engine.snapshot()['record']['pid']=='DEMO0002'


def test_stop_does_not_save_and_unlocks(page):
    open_pid(page);engine,proposal=prepare(page)
    stop=Event();stop.set()
    with pytest.raises(ReviewRequired,match='Đã dừng'): engine.fill(proposal,ADDRESS,True,stop)
    assert not engine.snapshot()['locked']
    assert engine.snapshot()['saved']['national_id']==''


def test_stop_mid_fill_does_not_save_and_unlocks(page,monkeypatch):
    open_pid(page);engine,proposal=prepare(page)
    stop=Event();original=engine.check
    def checked(*args,**kwargs):
        current=engine.snapshot()
        if current['record']['national_id']: stop.set()
        return original(*args,**kwargs)
    monkeypatch.setattr(engine,'check',checked)
    with pytest.raises(ReviewRequired,match='Đã dừng'): engine.fill(proposal,ADDRESS,True,stop)
    current=engine.snapshot()
    assert not current['locked'] and current['saved']['national_id']==''
    assert current['record']['national_id']=='000999000001'


def test_save_failure_and_cancel(page):
    open_pid(page);engine,proposal=prepare(page)
    pending=engine.fill(proposal,ADDRESS,True)
    page.route('**/api/patients/DEMO0001',lambda route: route.fulfill(status=503,json={'error':'Lỗi lưu giả lập'}))
    page.locator('#save').click()
    expect(page.locator('#message')).to_contain_text('Lỗi lưu giả lập')
    assert not engine.verify_saved(pending)
    page.locator('#cancel').click()
    assert engine.snapshot()['record']==engine.snapshot()['saved']


def test_missing_selector_times_out_without_saving(page):
    open_pid(page);engine,proposal=prepare(page)
    page.set_default_timeout(200)
    page.locator('#edit-address').evaluate('(element)=>element.remove()')
    with pytest.raises(Exception): engine.fill(proposal,ADDRESS,True)
    assert not engine.snapshot()['locked']
    assert engine.snapshot()['saved']['version']==1


def test_closed_page_reports_error(page):
    open_pid(page);engine,proposal=prepare(page);page.close()
    with pytest.raises(Exception): engine.fill(proposal,ADDRESS,True)


def test_lock_prevents_switching_and_saving(page):
    open_pid(page);page.locator('#lock-record').click()
    for selector in ('#pid-input','#open-record','#save','#cancel'):
        expect(page.locator(selector)).to_be_disabled()
    page.locator('#lock-record').click()
    expect(page.locator('#save')).to_be_enabled()


def test_unknown_pid_resets_profile(page):
    open_pid(page)
    page.locator('#pid-input').fill('NOTFOUND');page.locator('#open-record').click()
    expect(page.locator('#message')).to_contain_text('Không tìm thấy')
    expect(page.locator('#profile')).to_be_hidden()


def test_timing_twenty_patients(page):
    results=[]
    for i in range(20):
        open_pid(page,f'DEMO{i+1:04d}')
        engine,proposal=prepare(page,i)
        pending=engine.fill(proposal,ADDRESS,True)
        results.append(round(pending['elapsed_ms'],1))
        page.locator('#save').click()
        expect(page.locator('#message')).to_contain_text('thành công')
        assert engine.verify_saved(pending)
    report={'samples':20,'milliseconds':results,'under_5000ms':sum(v<=5000 for v in results),
            'browser':page.context.browser.version,'mode':'headless Edge; local synthetic fixtures',
            'excludes':'Human address confirmation and save time'}
    (ROOT/'docs'/'timing.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    assert report['under_5000ms']>=19


def test_rendered_viewports_and_keyboard(page):
    evidence=ROOT/'docs'/'evidence';evidence.mkdir(exist_ok=True)
    for w,h in [(1440,1000),(820,1000),(390,844)]:
        page.set_viewport_size({'width':w,'height':h})
        open_pid(page)
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
        page.screenshot(path=str(evidence/f'oh-{w}x{h}.png'),full_page=True)
    page.locator('#edit-address').focus()
    page.keyboard.press('Enter')
    expect(page.locator('#address-dialog')).to_be_visible()
    for key,value in ADDRESS.items():
        page.locator('#'+key).fill(value)
    page.screenshot(path=str(evidence/'oh-address-mobile.png'),full_page=True)
    page.locator('#apply-address').click()
    expect(page.locator('#address-summary')).to_contain_text('Phường Mới')
    assert page.locator('#pid-input').get_attribute('id')=='pid-input'


def test_content_states_and_keyboard_focus(page):
    evidence=ROOT/'docs'/'evidence';evidence.mkdir(exist_ok=True)
    page.set_viewport_size({'width':1440,'height':1000})
    page.screenshot(path=str(evidence/'state-empty.png'),full_page=True)
    expect(page.locator('#pid-input')).to_be_focused()
    page.keyboard.type('UNKNOWN');page.keyboard.press('Enter')
    expect(page.locator('#message')).to_have_class('error')
    page.screenshot(path=str(evidence/'state-error.png'),full_page=True)
    open_pid(page)
    record=BrowserRPA(page).snapshot()['saved']
    held=[]
    page.route('**/api/patients/DEMO0001',lambda route: held.append(route))
    page.locator('#open-record').click()
    expect(page.locator('#message')).to_contain_text('Đang mở')
    page.screenshot(path=str(evidence/'state-loading.png'),full_page=True)
    assert held
    held[0].fulfill(status=200,json=record)
    page.unroute('**/api/patients/DEMO0001')
    page.wait_for_function('window.ohSnapshot?.() && !window.ohSnapshot().loading')
    engine,proposal=prepare(page)
    pending=engine.fill(proposal,ADDRESS,True)
    page.screenshot(path=str(evidence/'state-partial.png'),full_page=True)
    assert engine.snapshot()['saved']['version']==1
    page.locator('#save').click()
    expect(page.locator('#message')).to_have_class('success')
    page.screenshot(path=str(evidence/'state-success.png'),full_page=True)
    assert engine.verify_saved(pending)
    page.locator('#edit-address').focus();page.keyboard.press('Enter')
    expect(page.locator('#address-dialog')).to_be_visible()
    page.keyboard.press('Tab')
    assert page.evaluate("document.activeElement.closest('dialog')!==null")
    page.keyboard.press('Escape')
    expect(page.locator('#address-dialog')).to_be_hidden()
