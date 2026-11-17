"""Kiểm tra API và luồng hai trình duyệt bằng hồ sơ giả lập, không cần thiết bị thật."""
import base64
import http.client
import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest

from server import DemoServer, PairError, PairStore

sys.stdout.reconfigure(encoding='utf-8')
PAYLOAD = '000000000001||NGƯỜI BỆNH MẪU|01011990|Nam|Phường Trúc Bạch, Quận Ba Đình, Thành phố Hà Nội|01012021'


class StoreTests(unittest.TestCase):
    def test_continuous_ack_retry_and_expiry(self):
        store = PairStore()
        owner = store.create('test', continuous=True)
        sender = store.join({'code': owner['code']}, 'phone')
        args = (owner['id'], sender['senderToken'])
        store.send(*args, {'payload': PAYLOAD, 'requestId': 'first'})
        with self.assertRaises(PairError):
            store.acknowledge(owner['id'], sender['senderToken'], 1)
        with self.assertRaises(PairError):
            store.send(*args, {'payload': PAYLOAD, 'requestId': 'second'})
        store.acknowledge(owner['id'], owner['ownerToken'], 1)
        store.send(*args, {'payload': PAYLOAD, 'requestId': 'first'})
        self.assertEqual(store.poll(owner['id'], owner['ownerToken'])['status'], 'paired')
        store.send(*args, {'payload': PAYLOAD, 'requestId': 'second'})
        with self.assertRaises(PairError):
            store.acknowledge(owner['id'], owner['ownerToken'], 1)
        self.assertEqual(store.poll(owner['id'], owner['ownerToken'])['sequence'], 2)
        store.acknowledge(owner['id'], owner['ownerToken'], 2)
        self.assertIsNone(store.sessions[owner['id']]['payload'])

    def setUp(self):
        self.now = [0]
        self.store = PairStore(clock=lambda: self.now[0])

    def test_isolation_and_once(self):
        first, second = self.store.create('test'), self.store.create('test')
        sender = self.store.join({'code': first['code']}, 'phone')
        with self.assertRaises(PairError) as error:
            self.store.poll(first['id'], sender['senderToken'])
        self.assertEqual(error.exception.status, 403)
        with self.assertRaises(PairError):
            self.store.send(second['id'], sender['senderToken'], {'payload': PAYLOAD})
        with self.assertRaises(PairError):
            self.store.join({'joinToken': first['joinToken']}, 'phone2')
        self.store.send(first['id'], sender['senderToken'], {'payload': PAYLOAD, 'sample': True})
        # Điện thoại gửi một lần; desktop có thể đọc lại trước khi ACK.
        for _ in range(2):
            self.assertEqual(self.store.poll(first['id'], first['ownerToken'])['payload'], PAYLOAD)
        self.assertEqual(self.store.poll(second['id'], second['ownerToken'])['status'], 'waiting')
        with self.assertRaises(PairError):
            self.store.send(first['id'], sender['senderToken'], {'payload': PAYLOAD})
        self.store.finish(first['id'], first['ownerToken'])
        self.assertNotIn(first['id'], self.store.sessions)
        with self.assertRaises(PairError):
            self.store.poll(first['id'], first['ownerToken'])

    def test_expiry_cancel_validation_and_rate(self):
        session = self.store.create('test')
        sender = self.store.join({'joinToken': session['joinToken']}, 'phone')
        with self.assertRaises(PairError):
            self.store.send(session['id'], sender['senderToken'], {'payload': 'invalid'})
        self.assertIsNone(self.store.sessions[session['id']]['payload'])
        self.now[0] = 601
        with self.assertRaises(PairError) as error:
            self.store.poll(session['id'], session['ownerToken'])
        self.assertEqual(error.exception.status, 410)
        self.assertFalse(self.store.sessions)
        for _ in range(8):
            with self.assertRaises(PairError):
                self.store.join({'code': 'not-found'}, 'brute')
        with self.assertRaises(PairError) as error:
            self.store.join({'code': 'not-found'}, 'brute')
        self.assertEqual(error.exception.status, 429)
        self.now[0] += 61
        session = self.store.create('test')
        self.store.finish(session['id'], session['ownerToken'])
        with self.assertRaises(PairError):
            self.store.join({'code': session['code']}, 'phone')


class HttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = DemoServer(('127.0.0.1', 0))
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def request(self, method, path, body=None, headers=None):
        conn = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=10)
        request_headers = {'Content-Type': 'application/json', **(headers or {})}
        conn.request(method, path, body=json.dumps(body).encode() if body is not None else None, headers=request_headers)
        result = conn.getresponse()
        data = result.read()
        conn.close()
        return result.status, data

    def test_boundaries(self):
        self.assertEqual(self.request('GET', '/server.py')[0], 404)
        self.assertEqual(self.request('GET', '/../server.py')[0], 404)
        self.assertEqual(self.request('GET', '/', headers={'Host': 'malicious.test:8765'})[0], 403)
        self.assertEqual(self.request('POST', '/api/pair', {}, {'Origin': 'https://other.test'})[0], 403)
        self.assertEqual(self.request('POST', '/api/pair', {}, {'Content-Type': 'text/plain'})[0], 415)
        self.assertEqual(self.request('POST', '/api/pair', {'large': 'x' * 20000})[0], 413)
        status, raw = self.request('POST', '/api/pair', {})
        self.assertEqual(status, 201)
        owner = json.loads(raw)
        self.assertEqual(self.request('GET', f'/api/pair/{owner["id"]}/result')[0], 403)
        status, raw = self.request('POST', '/api/join', {'code': owner['code']})
        self.assertEqual(status, 200)
        sender = json.loads(raw)
        headers = {'Authorization': 'Bearer ' + sender['senderToken']}
        self.assertEqual(self.request('POST', f'/api/pair/{owner["id"]}/send', {'payload': PAYLOAD, 'sample': True}, headers)[0], 200)
        status, raw = self.request('GET', f'/api/pair/{owner["id"]}/result', headers={'Authorization': 'Bearer ' + owner['ownerToken']})
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(raw)['payload'], PAYLOAD)


def browser_flow():
    from playwright.sync_api import sync_playwright
    server = DemoServer(('0.0.0.0', 0))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f'http://127.0.0.1:{server.server_port}'
    phone_base = f'http://{server.addresses[0]}:{server.server_port}' if server.addresses else base
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(channel='chrome', headless=True)
            desktop_context = browser.new_context(viewport={'width': 1440, 'height': 1100})
            phone_context = browser.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True)
            desktop, phone = desktop_context.new_page(), phone_context.new_page()
            errors = []
            desktop.on('pageerror', lambda error: errors.append(str(error)))
            phone.on('pageerror', lambda error: errors.append(str(error)))
            desktop.goto(base)
            desktop.locator('#create-pair').click()
            desktop.wait_for_selector('#pair-session', state='visible')
            code = desktop.locator('#pair-code').inner_text().replace(' ', '')
            assert len(code) == 8
            qr_link = desktop.evaluate('''() => {
              const canvas=document.getElementById('pair-qr'), context=canvas.getContext('2d');
              const pixels=context.getImageData(0,0,canvas.width,canvas.height);
              return jsQR(pixels.data,pixels.width,pixels.height).data;
            }''')
            from urllib.parse import urlsplit
            fragment = urlsplit(qr_link).fragment
            assert 'join=' in fragment
            phone.goto(phone_base + '/?phone=1#' + fragment)
            phone.wait_for_selector('#phone-connected', state='visible')
            assert phone.locator('#send-phone').is_disabled()
            assert phone.locator('#phone-photo-file').get_attribute('capture') == 'environment'
            assert phone.locator('#phone-gallery-file').get_attribute('capture') is None
            assert phone.locator('#phone-live').count() == 0
            assert phone.locator('#phone-enable-camera').count() == 0
            assert phone.locator('video').count() == 0
            if server.addresses:
                assert phone.evaluate('window.isSecureContext') is False
            assert phone.evaluate('location.hash') == ''
            assert phone.evaluate('localStorage.length') == 0
            qr_data = phone.evaluate('''payload => {
              qrcode.stringToBytes=qrcode.stringToBytesFuncs['UTF-8'];
              const qr=qrcode(0,'M');qr.addData(payload);qr.make();
              const scale=6, quiet=4, n=qr.getModuleCount(),canvas=document.createElement('canvas');
              canvas.width=canvas.height=(n+quiet*2)*scale;
              const ctx=canvas.getContext('2d');ctx.fillStyle='white';ctx.fillRect(0,0,canvas.width,canvas.height);ctx.fillStyle='black';
              for(let r=0;r<n;r++)for(let c=0;c<n;c++)if(qr.isDark(r,c))ctx.fillRect((c+quiet)*scale,(r+quiet)*scale,scale,scale);
              return canvas.toDataURL('image/png');
            }''', PAYLOAD)
            phone.locator('#phone-photo-file').set_input_files({'name': 'cccd-gia-lap.png', 'mimeType': 'image/png', 'buffer': base64.b64decode(qr_data.split(',')[1])})
            phone.wait_for_function("!document.getElementById('send-phone').disabled")
            assert phone.locator('#person-name').inner_text() == 'NGƯỜI BỆNH MẪU'
            assert all(session['payload'] is None for session in server.store.sessions.values())
            assert phone.evaluate('document.documentElement.scrollWidth <= innerWidth')
            phone.screenshot(path=str(Path(tempfile.gettempdir()) / 'vinmec-phone-pair.png'), full_page=True)
            phone.locator('#send-phone').click()
            phone.wait_for_function("document.getElementById('phone-status').textContent.includes('Đã gửi')")
            desktop.wait_for_function("document.getElementById('person-name').textContent === 'NGƯỜI BỆNH MẪU'")
            desktop.wait_for_function("document.getElementById('pair-status').textContent.includes('Đã nhận QR')")
            assert 'Phường Ba Đình' in desktop.locator('#new-address').inner_text()
            assert phone.locator('#person-name').inner_text() == ''
            assert phone.locator('#payload').input_value() == ''
            assert all(s['payload'] is None for s in server.store.sessions.values())
            # Gửi ảnh tiếp theo, không cần xác nhận địa chỉ hoặc ghép lại.
            assert not desktop.locator('#verified').is_checked()
            phone.locator('#phone-gallery-file').set_input_files({'name': 'anh-thu-hai.png', 'mimeType': 'image/png', 'buffer': base64.b64decode(qr_data.split(',')[1])})
            phone.wait_for_function("!document.getElementById('send-phone').disabled")
            assert next(iter(server.store.sessions.values()))['sequence'] == 1
            phone.locator('#send-phone').click()
            import time
            deadline = time.monotonic() + 8
            while any(s['sequence'] != 2 or s['payload'] is not None for s in server.store.sessions.values()) and time.monotonic() < deadline:
                desktop.wait_for_timeout(100)
            assert all(s['sequence'] == 2 and s['payload'] is None for s in server.store.sessions.values())
            desktop.screenshot(path=str(Path(tempfile.gettempdir()) / 'vinmec-desktop-pair.png'), full_page=True)
            # Mã nhập tay, hủy và mã hết hạn không thể ghép tiếp.
            desktop.locator('#create-pair').click()
            desktop.wait_for_selector('#pair-session', state='visible')
            code = desktop.locator('#pair-code').inner_text().replace(' ', '')
            phone.goto(phone_base + '/?phone=1')
            phone.locator('#join-code').fill(code)
            phone.locator('#join-pair').click()
            phone.wait_for_selector('#phone-connected', state='visible')
            desktop.locator('#cancel-pair').click()
            desktop.wait_for_selector('#pair-session', state='hidden')
            desktop.wait_for_function('''async () => { const response=await fetch('/api/network');return response.ok; }''')
            # Close chạy bất đồng bộ từ thao tác reset; đợi server xử lý.
            import time
            deadline = time.monotonic() + 5
            while server.store.sessions and time.monotonic() < deadline:
                time.sleep(.05)
            assert not server.store.sessions
            assert not errors, errors
            browser.close()
        print('PASS: hai trình duyệt độc lập, ghép QR/mã tay, ảnh QR Unicode, chỉ gửi khi bấm, tự điền/ánh xạ, xóa RAM, hủy phiên và mobile 390px.')
    finally:
        server.shutdown()
        server.server_close()


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise SystemExit(1)
    browser_flow()
