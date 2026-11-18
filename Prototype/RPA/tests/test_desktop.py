"""Exercise Tk state transitions; native OH integration is covered separately."""
from copy import deepcopy
import json
import subprocess
import time
import tkinter as tk
from shared.paths import ROOT, DEMO
from rpa_tool.app import ReceptionApp
from rpa_tool.contracts import Proposal
from shared.excel import read_roster
from shared.identity import parse_scan


def test_desktop_state_and_layout(monkeypatch,tmp_path):
    monkeypatch.setattr(ReceptionApp,'worker',lambda self: self.events.put(('ready',None)))
    root=tk.Tk()
    app=ReceptionApp(root)
    monkeypatch.setattr(app,'handoff_path',lambda:tmp_path/'not-created.xlsx')
    try:
        root.update();app.load()
        app.phase.set('2. Khách đến — tiếp đón');app.load()
        assert len(app.rows)==10
        scan=json.loads((DEMO/'scans.json').read_text(encoding='utf-8'))[0]['scan']
        # Selecting demo mode must preserve the loaded roster.
        app.events.put(('demo',scan));app.poll();root.update()
        assert len(app.rows)==10
        record=json.loads((DEMO/'patients.json').read_text(encoding='utf-8'))[0]
        record.update(version=1)
        proposal=Proposal({'record':record,'saved':deepcopy(record)},parse_scan(scan),app.rows[0],1)
        app.events.put(('prepared',proposal));app.poll();root.update()
        assert str(app.fill_button['state'])=='disabled'
        app.confirmed.set(True);root.update()
        assert str(app.fill_button['state'])=='normal'
        app.address['ward'].set('Phường Mới');root.update()
        assert not app.confirmed.get() and str(app.fill_button['state'])=='disabled'
        app.confirmed.set(True)
        app.set_busy(True);root.update()
        assert str(app.scan_entry['state'])=='disabled'
        app.cancel()
        app.events.put(('filled',{'pid':'DEMO0001'}));app.poll();root.update()
        assert app.pending is None and app.proposal is None
        app.set_busy(False)
        app.info.set('KHỚP · DEMO0001 · Nguyễn Văn An\nCCCD: ********0001 · 1985-03-01\nNguồn địa chỉ Excel: địa chỉ cũ giả lập\nOH hiện tại: 1 Đường Mẫu, Phường Cũ, Thành phố Demo')
        app.status.set('Đối chiếu khớp. Hỏi khách, sửa địa chỉ và đánh dấu xác nhận.')
        root.update()
        evidence=ROOT/'docs'/'evidence';evidence.mkdir(exist_ok=True)
        # Capture the real running RPA externally for visual evidence. Sending
        # synchronous PrintWindow into a Tk window pumped by root.update can
        # deadlock; this test verifies widget state and scrolling directly.
        app.canvas.yview_moveto(1);root.update()
        assert app.fill_button.winfo_rooty() < root.winfo_rooty()+root.winfo_height()
    finally:
        app.close()


def test_live_desktop_native_boot(native_app):
    engine,process,path=native_app
    root=tk.Tk();app=ReceptionApp(root,process_id=process.pid)
    try:
        deadline=time.monotonic()+15
        while time.monotonic()<deadline:
            root.update()
            if app.status.get().startswith('OH đã mở'): break
            if 'Không mở' in app.status.get(): raise AssertionError(app.status.get())
            time.sleep(.05)
        assert app.status.get().startswith('OH đã mở')
        app.load()
        assert len(app.rows)==3
        app.demo_scan()
        deadline=time.monotonic()+10
        while app.busy and time.monotonic()<deadline:
            root.update();time.sleep(.05)
        assert 'chưa mở hồ sơ' in app.status.get()
    finally:
        app.close()
        app.worker_thread.join(timeout=7)
        assert not app.worker_thread.is_alive()


def test_preparation_gui_exports_and_hands_off_to_reception(monkeypatch,tmp_path):
    from shared.excel import read_preparation
    monkeypatch.setattr(ReceptionApp,'worker',lambda self:self.events.put(('ready',None)))
    root=tk.Tk();app=ReceptionApp(root)
    output=tmp_path/'handoff.xlsx';monkeypatch.setattr(app,'handoff_path',lambda:output)
    try:
        root.update();app.load()
        assert len(app.rows)==3 and str(app.create_button['state'])=='normal'
        app.events.put(('creation_filled',{'kind':'creation'}));app.poll();root.update()
        assert str(app.phase_box['state'])=='disabled'
        ready=dict(app.rows[0],pid='NEW000001')
        app.events.put(('created',ready));app.poll();root.update()
        assert output.exists() and app.rows[0]['pid']=='NEW000001'
        assert str(app.create_button['state'])=='disabled'
        app.customer_box.current(1);app.controls()
        assert str(app.create_button['state'])=='normal'
        app.use_handoff();root.update()
        assert app.phase.get().startswith('2.') and app.rows[0]['pid']=='NEW000001'
        assert app.file.get()==str(output)
    finally:app.close()


def test_phase_selector_shows_one_workflow_and_hides_reception_excel(monkeypatch,tmp_path):
    monkeypatch.setattr(ReceptionApp,'worker',lambda self:self.events.put(('ready',None)))
    root=tk.Tk();app=ReceptionApp(root)
    monkeypatch.setattr(app,'handoff_path',lambda:tmp_path/'no-handoff.xlsx')
    try:
        root.update();app.load()
        initial_file=app.file.get()
        assert app.data_frame.winfo_ismapped() and app.prep_frame.winfo_ismapped()
        assert not app.reception_frame.winfo_ismapped() and not app.reception_context.winfo_ismapped()
        app.phase.set('2. Khách đến — tiếp đón');root.update()
        assert not app.prep_frame.winfo_ismapped() and not app.data_frame.winfo_ismapped()
        assert app.reception_frame.winfo_ismapped() and app.reception_context.winfo_ismapped()
        assert not app.rows and 'Chưa nạp' in app.roster_summary.get()
        app.toggle_roster_editor();root.update()
        assert app.data_frame.winfo_ismapped()
        app.file.set(str(DEMO/'company_A.xlsx'));app.load();root.update()
        assert len(app.rows)==10 and '10 khách' in app.roster_summary.get()
        assert not app.data_frame.winfo_ismapped()
        app.clear();root.update()
        assert len(app.rows)==10  # new visitor reuses the already loaded roster
        app.phase.set('1. Chuẩn bị — tạo PID / bung gói');root.update()
        assert len(app.rows)==3 and app.file.get()==initial_file
        assert app.prep_frame.winfo_ismapped() and not app.reception_frame.winfo_ismapped()
        app.phase.set('2. Khách đến — tiếp đón');root.update()
        assert len(app.rows)==10 and not app.data_frame.winfo_ismapped()
    finally:app.close()


def test_reception_selector_automatically_loads_verified_handoff(monkeypatch,tmp_path):
    from shared.excel import read_preparation,export_prepared
    monkeypatch.setattr(ReceptionApp,'worker',lambda self:self.events.put(('ready',None)))
    root=tk.Tk();app=ReceptionApp(root)
    output=tmp_path/'ready.xlsx'
    prepared=read_preparation(DEMO/'new_customers_A.xlsx','DS_bung_DEMO','Công ty Demo A','DEMO-2026')[0][0]
    export_prepared(output,[dict(prepared,pid='NEW000001')])
    monkeypatch.setattr(app,'handoff_path',lambda:output)
    try:
        root.update();app.phase.set('2. Khách đến — tiếp đón');root.update()
        assert app.rows[0]['pid']=='NEW000001' and '1 khách' in app.roster_summary.get()
        assert not app.data_frame.winfo_ismapped() and not app.prep_frame.winfo_ismapped()
        assert app.reception_frame.winfo_ismapped()
    finally:app.close()
