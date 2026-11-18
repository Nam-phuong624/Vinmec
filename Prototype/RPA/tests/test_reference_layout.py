import subprocess
from shared.paths import ROOT


def capture(engine,name):
    folder=ROOT/'docs'/'reference-evidence';folder.mkdir(exist_ok=True)
    subprocess.run(['powershell','-NoProfile','-File',str(ROOT/'scripts'/'capture_window.ps1'),
                    '-WindowHandle',str(engine.handle),'-Destination',str(folder/name)],check=True,capture_output=True)


def test_reference_labels_names_and_rendered_layout(native_app):
    engine,_,_=native_app
    engine.open_pid('DEMO0001')
    assert engine.read('local-name-0')=='An'
    assert engine.read('local-name-1')=='Văn'
    assert engine.read('local-name-2')=='Nguyễn'
    assert engine.read('name')=='Nguyễn Văn An'
    for name in ('identification-section-header','contact-section-header','personal-section-header','employment-section-header'):
        assert engine.control(name,'Button').is_enabled()
    assert engine.control('profile-tabs','Tab').is_visible()
    capture(engine,'patient-profile.png')
    import win32gui
    scroll=engine.control('profile-scroll','Pane').handle
    win32gui.SendMessage(scroll,0x0115,3,0)  # WM_VSCROLL / SB_PAGEDOWN
    capture(engine,'patient-profile-personal.png')
    win32gui.SendMessage(scroll,0x0115,6,0)  # SB_TOP
    # The body scrolls independently; save/cancel remain available at minimum size.
    bounds=win32gui.GetWindowRect(engine.handle)
    win32gui.MoveWindow(engine.handle,bounds[0],bounds[1],1120,680,True)
    for name in ('save-record','cancel-record','lock-record'):
        assert engine.control(name,'Button').is_visible()
    capture(engine,'patient-profile-compact.png')


def test_missing_pid_clears_reference_name_parts(native_app):
    engine,_,_=native_app
    engine.open_pid('DEMO0001')
    engine.write('pid-search','NOT-FOUND');engine.click('open-record')
    from pywinauto.timings import wait_until
    wait_until(5,.05,lambda:engine.read('pid')=='')
    for name in ('local-name-0','local-name-1','local-name-2','name','age-display'):
        assert engine.read(name)==''
