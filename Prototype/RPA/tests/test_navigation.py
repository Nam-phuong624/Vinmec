import subprocess
import win32gui
from pywinauto.timings import wait_until
from shared.paths import ROOT


def shot(engine,name):
    directory=ROOT/'docs'/'sidebar-evidence';directory.mkdir(exist_ok=True)
    subprocess.run(['powershell','-NoProfile','-File',str(ROOT/'scripts'/'capture_window.ps1'),
                    '-WindowHandle',str(engine.handle),'-Destination',str(directory/name)],check=True,capture_output=True)


def test_sidebar_groups_and_safe_reference_navigation(native_app):
    engine,_,_=native_app;engine.open_pid('DEMO0001')
    for group in ('registration','cashier','admission','discharge','transfer','appointments','visit','maintenance'):
        assert engine.control('nav-group-'+group,'Button').is_enabled()
    assert engine.control('nav-patient-profile','Button').is_visible()
    engine.click('nav-patient-profile')
    assert engine.read('pid')=='DEMO0001'
    engine.click('nav-patient-billing')
    assert 'ngoài phạm vi' in engine.read('message')
    assert engine.read('pid')=='DEMO0001' and engine.read('version')=='1'
    shot(engine,'oh-sidebar.png')
    engine.click('nav-group-registration')
    wait_until(5,.05,lambda:not win32gui.IsWindowVisible(engine.control('nav-patient-profile','Button').handle))
    engine.click('nav-group-registration')
    wait_until(5,.05,lambda:win32gui.IsWindowVisible(engine.control('nav-patient-profile','Button').handle))
    scroll=engine.control('navigation-scroll','Pane').handle
    win32gui.SendMessage(scroll,0x0115,7,0)  # SB_BOTTOM, independent sidebar scroll
    shot(engine,'oh-sidebar-bottom.png')
    assert engine.read('pid')=='DEMO0001'


def test_sidebar_collapse_and_compact_window_leave_save_available(native_app):
    engine,_,_=native_app;engine.open_pid('DEMO0001')
    engine.click('navigation-toggle')
    wait_until(5,.05,lambda:not win32gui.IsWindowVisible(engine.control('nav-patient-profile','Button').handle))
    for name in ('save-record','cancel-record','lock-record'):
        assert engine.control(name,'Button').is_visible()
    engine.click('navigation-toggle')
    wait_until(5,.05,lambda:win32gui.IsWindowVisible(engine.control('nav-patient-profile','Button').handle))
    bounds=win32gui.GetWindowRect(engine.handle)
    win32gui.MoveWindow(engine.handle,bounds[0],bounds[1],1120,680,True)
    wait_until(5,.05,lambda:not win32gui.IsWindowVisible(engine.control('nav-patient-profile','Button').handle))
    for name in ('save-record','cancel-record','lock-record'):
        assert engine.control(name,'Button').is_visible()
    shot(engine,'oh-sidebar-compact.png')
