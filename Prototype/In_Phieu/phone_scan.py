"""Điện thoại Android làm đầu quét CCCD — cùng cơ chế với "demo - ql vật tư" (scan.html + relay):

  máy tính chạy server HTTP (chỉ localhost, dùng với `adb reverse`) và HTTPS (cả LAN, chứng chỉ tự ký vì camera chỉ bật được trên HTTPS);
  máy tính hiện QR ghép đôi = https://<IP>:<cổng>/scan.html?t=<token>; điện thoại mở trang, bật camera, đọc mã QR của CCCD
  rồi gửi chuỗi lên máy tính (POST /api/relay/<token>); máy tính xử lý và trả kết quả để điện thoại hiển thị.

Chuỗi QR chỉ nằm trong bộ nhớ, không ghi log. Mọi yêu cầu đều phải có đúng token ghép đôi của phiên.
"""
import datetime
import hmac
import http.server
import ipaddress
import json
import os
import queue
import re
import secrets
import socket
import ssl
import threading
import time
from pathlib import Path

HTTP_PORT = int(os.environ.get('IN_PHIEU_HTTP_PORT', 8780))
HTTPS_PORT = int(os.environ.get('IN_PHIEU_HTTPS_PORT', 8743))
MAX_BODY = 6 * 1024 * 1024
_ROUTE = re.compile(r'^/api/(relay|result|ping|decode)/([A-Za-z0-9_-]{6,64})$')

PAGE = r"""<!doctype html>
<html lang="vi"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Quét CCCD</title>
<style>
*{box-sizing:border-box}body{margin:0;font-family:system-ui,sans-serif;background:#0f172a;color:#fff;min-height:100vh;display:flex;flex-direction:column}
header{padding:14px 16px;font-weight:700;font-size:17px;display:flex;justify-content:space-between;align-items:center}
#link{font-size:13px;font-weight:600;color:#fca5a5}#link.ok{color:#4ade80}
#stage{position:relative;flex:1;min-height:55vh;background:#000;display:flex;align-items:center;justify-content:center;overflow:hidden}
video{width:100%;height:100%;object-fit:cover;position:absolute;inset:0}
#aim{position:relative;width:72%;aspect-ratio:1/1;max-height:80%;border:3px solid rgba(255,255,255,.85);border-radius:14px;box-shadow:0 0 0 100vmax rgba(0,0,0,.35)}
#aim.hit{border-color:#22c55e}#aim.bad{border-color:#ef4444}
#start{position:absolute;z-index:2;font:inherit;font-size:20px;font-weight:700;padding:20px 36px;border:0;border-radius:16px;background:#2563eb;color:#fff}
#info{padding:14px 16px;min-height:96px}
#res{font-size:19px;font-weight:700;word-break:break-word}#res.ok{color:#4ade80}#res.warn{color:#fde047}#res.bad{color:#fca5a5;font-size:16px;font-weight:500}
#hist{list-style:none;margin:8px 0 0;padding:0;font-size:14px;color:#cbd5e1;max-height:18vh;overflow:auto}
#hist li{padding:4px 0;border-bottom:1px solid #1e293b}
</style></head><body>
<header><span>📱 Quét mã QR trên CCCD</span><span id="link">Chưa kết nối</span></header>
<div id="stage"><video id="v" playsinline muted></video><div id="aim"></div><button id="start">📷 Bật camera</button></div>
<div id="info"><div id="res">Đưa mã QR ở mặt sau CCCD vào khung — tự gửi lên máy tính.</div><ul id="hist"></ul></div>
<script>
const token = new URLSearchParams(location.search).get('t') || '';
const $ = id => document.getElementById(id), res = $('res'), vid = $('v'), aim = $('aim'), start = $('start'), hist = $('hist'), link = $('link');
const say = (t, c) => { res.className = c || ''; res.textContent = t; };
if (!token) { say('Thiếu mã ghép đôi. Hãy quét lại QR hiện trên máy tính.', 'bad'); start.disabled = true; }
const COOLDOWN = 3000, last = {code: '', t: 0};
let det = null, busy = false, waiting = false, stream = null;
if ('BarcodeDetector' in window) { try { det = new BarcodeDetector({formats: ['qr_code']}); } catch (_) { det = new BarcodeDetector(); } }

// Một số trình duyệt đọc chuỗi UTF-8 của QR thành chuỗi Latin-1 (chữ tiếng Việt bị vỡ): thử đọc lại đúng UTF-8.
function fixText(s) {
  if (!/[ÂÃÄÆá]/.test(s)) return s;
  try { const b = Uint8Array.from(s, c => c.charCodeAt(0)); if (b.some((x, i) => s.charCodeAt(i) > 255)) return s; return new TextDecoder('utf-8', {fatal: true}).decode(b); } catch (_) { return s; }
}
async function api(path, opt) { const r = await fetch('/api/' + path + '/' + encodeURIComponent(token), opt); if (!r.ok) throw new Error((await r.json().catch(() => ({}))).error || 'Lỗi kết nối máy tính.'); return r.json(); }
async function ping() { try { await api('ping'); link.textContent = '● Đã kết nối máy tính'; link.className = 'ok'; } catch (_) { link.textContent = '○ Mất kết nối'; link.className = ''; } }
ping(); setInterval(ping, 5000);

async function send(code) {
  const now = Date.now();
  if (code === last.code && now - last.t < COOLDOWN) return;
  last.code = code; last.t = now; waiting = true;
  try {
    const sent = await api('relay', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({code})});
    say('Đã gửi lên máy tính, đang xử lý…', '');
    const end = Date.now() + 12000;
    while (Date.now() < end) {                       // chờ máy tính trả kết quả để hiện ngay trên điện thoại
      await new Promise(r => setTimeout(r, 700));
      const r = await fetch('/api/result/' + encodeURIComponent(token) + '?after=' + sent.seq).then(x => x.json());
      if (r.seq >= sent.seq && r.text) {
        say(r.text, r.ok ? 'ok' : 'bad'); aim.className = r.ok ? 'hit' : 'bad'; setTimeout(() => aim.className = '', 900);
        const li = document.createElement('li'); li.textContent = new Date().toLocaleTimeString('vi-VN') + ' — ' + r.text; hist.prepend(li);
        if (navigator.vibrate) navigator.vibrate(r.ok ? 80 : [60, 60, 60]);
        waiting = false; return;
      }
    }
    say('Đã gửi nhưng máy tính chưa phản hồi.', 'bad');
  } catch (e) { say(e.message, 'bad'); }
  waiting = false;
}

const cv = document.createElement('canvas');
async function serverDecode() {                       // trình duyệt không có BarcodeDetector → gửi khung hình lên máy tính để đọc
  const k = Math.min(1, 1000 / Math.max(vid.videoWidth, vid.videoHeight));
  cv.width = Math.round(vid.videoWidth * k); cv.height = Math.round(vid.videoHeight * k);
  cv.getContext('2d').drawImage(vid, 0, 0, cv.width, cv.height);
  const blob = await new Promise(r => cv.toBlob(r, 'image/jpeg', 0.85));
  const r = await fetch('/api/decode/' + encodeURIComponent(token), {method: 'POST', body: blob});
  return r.ok ? ((await r.json()).codes || [])[0] || '' : '';
}
async function tick() {
  if (!stream) return;
  if (!busy && !waiting && vid.readyState >= 2 && vid.videoWidth) {
    busy = true;
    try { const code = det ? ((await det.detect(vid))[0] || {}).rawValue : await serverDecode(); if (code) await send(fixText(code.trim())); } catch (_) {}
    busy = false;
  }
  setTimeout(tick, det ? 150 : 500);
}
start.onclick = async () => {
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) { say('Trình duyệt không cho bật camera. Hãy mở bằng địa chỉ https:// (bấm "Nâng cao → Tiếp tục" khi báo chứng chỉ).', 'bad'); return; }
  try { stream = await navigator.mediaDevices.getUserMedia({video: {facingMode: {ideal: 'environment'}, width: {ideal: 1280}, height: {ideal: 720}}, audio: false}); }
  catch (e) { say('Không bật được camera: ' + (e.name === 'NotAllowedError' ? 'bạn chưa cho phép dùng camera.' : e.message), 'bad'); return; }
  vid.srcObject = stream; await vid.play(); start.hidden = true; say('Đang quét… đưa mã QR vào khung.');
  try { if (navigator.wakeLock) navigator.wakeLock.request('screen'); } catch (_) {}
  tick();
};
</script></body></html>
"""


def lan_ip() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(('10.255.255.255', 1))
            return s.getsockname()[0]
    except OSError:
        return '127.0.0.1'


def ensure_cert(directory: Path, ip: str):
    """Chứng chỉ tự ký (SAN: localhost + IP máy tính); tạo lại khi IP đổi."""
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID
    directory.mkdir(parents=True, exist_ok=True)
    crt, key, stamp = directory / 'cert.pem', directory / 'key.pem', directory / 'ip.txt'
    if crt.exists() and key.exists() and stamp.exists() and stamp.read_text().strip() == ip:
        return crt, key
    private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'In Phieu CCCD')])
    now = datetime.datetime.now(datetime.timezone.utc)
    san = [x509.DNSName('localhost'), x509.IPAddress(ipaddress.ip_address('127.0.0.1')), x509.IPAddress(ipaddress.ip_address(ip))]
    cert = (x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(private.public_key())
            .serial_number(x509.random_serial_number()).not_valid_before(now - datetime.timedelta(days=1))
            .not_valid_after(now + datetime.timedelta(days=825)).add_extension(x509.SubjectAlternativeName(san), False)
            .sign(private, hashes.SHA256()))
    crt.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    key.write_bytes(private.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.TraditionalOpenSSL, serialization.NoEncryption()))
    stamp.write_text(ip)
    return crt, key


class PhoneLink:
    """Một phiên ghép đôi: token, hàng đợi chuỗi QR gửi từ điện thoại, và kết quả xử lý trả lại điện thoại."""

    def __init__(self, cert_dir: Path, decoder=None):
        self.token = secrets.token_urlsafe(8)
        self.codes = queue.Queue()
        self.cert_dir = cert_dir
        self.decoder = decoder            # bytes ảnh → chuỗi QR (dùng khi trình duyệt không có BarcodeDetector)
        self.seq = 0
        self.result = {'seq': 0, 'text': '', 'ok': True}
        self.last_seen = 0.0
        self.ip = lan_ip()
        self.servers = []
        self.lock = threading.Lock()

    @property
    def url(self) -> str:
        return f'https://{self.ip}:{HTTPS_PORT}/scan.html?t={self.token}'

    @property
    def usb_url(self) -> str:
        return f'http://localhost:{HTTP_PORT}/scan.html?t={self.token}'

    def connected(self) -> bool:
        return time.time() - self.last_seen < 12

    def publish(self, text: str, ok: bool):
        with self.lock:
            self.result = {'seq': self.seq, 'text': text, 'ok': ok}

    def start(self):
        link = self
        crt, key = ensure_cert(self.cert_dir, self.ip)

        class Handler(http.server.BaseHTTPRequestHandler):
            protocol_version = 'HTTP/1.1'

            def log_message(self, *args):     # không ghi log: URL chứa token, nội dung chứa dữ liệu CCCD
                pass

            def _send(self, status, body, ctype='application/json; charset=utf-8'):
                data = body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False).encode('utf-8')
                self.send_response(status)
                self.send_header('Content-Type', ctype)
                self.send_header('Content-Length', str(len(data)))
                self.send_header('Cache-Control', 'no-store')
                self.end_headers()
                self.wfile.write(data)

            def _route(self):
                path = self.path.split('?', 1)[0]
                if path in ('/', '/scan.html'):
                    return 'page', ''
                m = _ROUTE.match(path)
                if not m:
                    return None, ''
                if not hmac.compare_digest(m.group(2), link.token):
                    return 'denied', ''
                return m.group(1), m.group(2)

            def do_GET(self):
                kind, _ = self._route()
                if kind == 'page':
                    return self._send(200, PAGE.encode('utf-8'), 'text/html; charset=utf-8')
                if kind == 'denied':
                    return self._send(403, {'error': 'Mã ghép đôi không đúng. Quét lại QR trên máy tính.'})
                link.last_seen = time.time() if kind in ('ping', 'result') else link.last_seen
                if kind == 'ping':
                    return self._send(200, {'ok': True})
                if kind == 'result':
                    return self._send(200, link.result)
                self._send(404, {'error': 'Không tìm thấy.'})

            def do_POST(self):
                kind, _ = self._route()
                if kind == 'denied':
                    return self._send(403, {'error': 'Mã ghép đôi không đúng. Quét lại QR trên máy tính.'})
                if kind not in ('relay', 'decode'):
                    return self._send(404, {'error': 'Không tìm thấy.'})
                try:
                    size = int(self.headers.get('Content-Length', 0))
                except ValueError:
                    size = -1
                if not 0 <= size <= MAX_BODY:
                    return self._send(413, {'error': 'Dữ liệu quá lớn.'})
                body = self.rfile.read(size)
                link.last_seen = time.time()
                if kind == 'relay':
                    try:
                        code = str(json.loads(body.decode('utf-8')).get('code', '')).strip()[:600]
                    except (ValueError, AttributeError):
                        code = ''
                    if not code:
                        return self._send(400, {'error': 'Thiếu nội dung mã QR.'})
                    with link.lock:
                        link.seq += 1
                        seq = link.seq
                    link.codes.put(code)
                    return self._send(200, {'ok': True, 'seq': seq})
                codes = []
                if link.decoder:
                    try:
                        codes = [link.decoder(body)]
                    except Exception:
                        codes = []
                self._send(200, {'codes': codes})

        class Server(http.server.ThreadingHTTPServer):
            daemon_threads = True

            def handle_error(self, request, client_address):   # bắt tay TLS lỗi (chưa tin chứng chỉ...) không phải lỗi chương trình
                pass

        http_server = Server(('127.0.0.1', HTTP_PORT), Handler)
        https_server = Server(('0.0.0.0', HTTPS_PORT), Handler)
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(str(crt), str(key))
        https_server.socket = context.wrap_socket(https_server.socket, server_side=True)
        self.servers = [http_server, https_server]
        for server in self.servers:
            threading.Thread(target=server.serve_forever, daemon=True).start()

    def stop(self):
        for server in self.servers:
            try:
                server.shutdown()
                server.server_close()
            except Exception:
                pass
        self.servers = []
