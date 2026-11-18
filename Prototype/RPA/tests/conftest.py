import threading
import site
import sys
from pathlib import Path
if sys.prefix == sys.base_prefix:
    site.addsitedir(str(Path(__file__).resolve().parents[1]/'.deps'))
import pytest
from oh_desktop.store import initialize
from scripts.generate_demo import main


@pytest.fixture(scope='session', autouse=True)
def demo_data():
    main()


@pytest.fixture
def app(tmp_path):
    from oh_mock.app import create_app
    path = tmp_path / 'test.sqlite3'
    initialize(path)
    return create_app(path)


@pytest.fixture
def live_server(app):
    from werkzeug.serving import make_server
    server = make_server('127.0.0.1', 0, app, threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f'http://127.0.0.1:{server.server_port}'
    server.shutdown()
    thread.join(timeout=3)


@pytest.fixture(scope='session')
def browser():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        instance = pw.chromium.launch(channel='msedge', headless=True)
        yield instance
        instance.close()


@pytest.fixture
def page(browser, live_server):
    context = browser.new_context(viewport={'width':1440, 'height':1000})
    page = context.new_page()
    page.goto(live_server)
    yield page
    context.close()


@pytest.fixture
def native_app(tmp_path):
    import os
    from oh_desktop.launcher import launch
    from rpa_tool.desktop_engine import DesktopRPA
    path=tmp_path/'native.sqlite3'
    initialize(path)
    env=os.environ.copy()
    for key,part in [('APPDATA','Roaming'),('LOCALAPPDATA','Local'),('TEMP','Temp'),('TMP','Temp')]:
        directory=tmp_path/part;directory.mkdir(exist_ok=True);env[key]=str(directory)
    process=launch(path,title='OH Native Test',env=env)
    try:
        engine=DesktopRPA(process.pid,timeout=8)
        yield engine,process,path
    finally:
        if process.poll() is None:
            try:
                engine.window.close()
                process.wait(timeout=3)
            except Exception:
                process.terminate();process.wait(timeout=3)
