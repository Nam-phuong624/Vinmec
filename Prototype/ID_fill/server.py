"""Máy chủ demo LAN: ghép điện thoại, chuyển QR liên tiếp; dữ liệu chỉ trong RAM."""
import argparse
from collections import defaultdict, deque
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import ipaddress
import json
from pathlib import Path
import secrets
import socket
import threading
import time
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent
TTL = 600
MAX_BODY = 16384
STATIC_FILES = {'index.html', 'styles.css', 'patient-profile.css', 'patient-profile.js', 'research-history.js', 'research-mapper.js', 'app.js', 'pair.js', 'core.js', 'data.js', 'history.js', 'vendor/jsQR.js', 'vendor/zxing.js', 'vendor/qrcode.js'}


def lan_addresses():
    addresses = set()
    try:
        for item in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            address = ipaddress.ip_address(item[4][0])
            if address.is_private and not address.is_loopback and not address.is_link_local:
                addresses.add(str(address))
    except OSError:
        pass
    return sorted(addresses)


class PairError(Exception):
    def __init__(self, status, message):
        self.status, self.message = status, message


def validate_payload(value):
    if not isinstance(value, str) or len(value.encode('utf-8')) > 8192:
        raise PairError(400, 'Chuỗi QR quá dài hoặc không hợp lệ.')
    fields = [part.strip() for part in value.strip().split('|')]
    if len(fields) != 7:
        raise PairError(400, 'Cần QR CCCD có đủ 7 trường.')
    number, old, name, birth, sex, address, issued = fields
    if not (number.isascii() and number.isdigit() and len(number) == 12):
        raise PairError(400, 'Số CCCD không hợp lệ.')
    if old and not (old.isascii() and old.isdigit() and len(old) == 9):
        raise PairError(400, 'Số CMND cũ không hợp lệ.')
    if not name or not address or len(name) > 200 or len(address) > 2000 or sex.lower() not in ('nam', 'nữ', 'nu'):
        raise PairError(400, 'Thông tin trong QR chưa hợp lệ.')
    try:
        dates = []
        for value in (birth, issued):
            if len(value) != 8 or not value.isascii() or not value.isdigit():
                raise ValueError()
            parsed = datetime.strptime(value, '%d%m%Y')
            if parsed.year < 1900 or parsed.date() > datetime.now().date():
                raise ValueError()
            dates.append(parsed)
        if dates[1] < dates[0]:
            raise ValueError()
    except ValueError:
        raise PairError(400, 'Ngày sinh hoặc ngày cấp chưa hợp lệ.') from None
    return '|'.join(fields)


class PairStore:
    def __init__(self, clock=time.monotonic):
        self.clock = clock
        self.lock = threading.Lock()
        self.sessions = {}
        self.attempts = defaultdict(deque)

    def cleanup(self):
        now = self.clock()
        for key in list(self.sessions):
            if self.sessions[key]['expires'] <= now:
                del self.sessions[key]
        for key in list(self.attempts):
            queue = self.attempts[key]
            while queue and queue[0] < now - 60:
                queue.popleft()
            if not queue:
                del self.attempts[key]

    def limit(self, key, maximum):
        self.cleanup()
        queue = self.attempts[key]
        if len(queue) >= maximum:
            raise PairError(429, 'Thử ghép quá nhiều lần. Đợi một phút rồi thử lại.')
        queue.append(self.clock())

    def authorized(self, session_id, token, role):
        self.cleanup()
        session = self.sessions.get(session_id)
        if not session:
            raise PairError(410, 'Phiên đã hết hạn hoặc bị hủy. Tạo mã mới trên máy tính.')
        expected = session.get(role)
        if not expected or not isinstance(token, str) or not secrets.compare_digest(expected, token):
            raise PairError(403, 'Không có quyền truy cập phiên này.')
        return session

    def create(self, peer, continuous=False):
        with self.lock:
            self.limit(('create', peer), 12)
            if len(self.sessions) >= 100:
                raise PairError(429, 'Đã có quá nhiều phiên. Đợi phiên cũ hết hạn.')
            session_id, owner, join = secrets.token_urlsafe(18), secrets.token_urlsafe(32), secrets.token_urlsafe(24)
            codes = {session['code'] for session in self.sessions.values()}
            code = f'{secrets.randbelow(100000000):08d}'
            while code in codes:
                code = f'{secrets.randbelow(100000000):08d}'
            self.sessions[session_id] = {'owner': owner, 'join': join, 'code': code,
                                         'expires': self.clock() + TTL, 'sender': None,
                                         'state': 'waiting', 'payload': None, 'sample': False,
                                         'continuous': continuous, 'sequence': 0, 'request': None}
            return {'id': session_id, 'ownerToken': owner, 'joinToken': join, 'code': code, 'expiresIn': TTL}

    def join(self, body, peer):
        with self.lock:
            self.limit(('join', peer), 8)
            self.limit(('join-global', ''), 60)
            code, token = body.get('code'), body.get('joinToken')
            if not isinstance(code, str) and not isinstance(token, str):
                raise PairError(400, 'Nhập mã ghép trên máy tính.')
            match = None
            for session_id, session in self.sessions.items():
                if ((isinstance(code, str) and secrets.compare_digest(session['code'], code)) or
                        (isinstance(token, str) and secrets.compare_digest(session['join'], token))):
                    match = (session_id, session)
                    break
            if not match:
                raise PairError(404, 'Mã không đúng hoặc đã hết hạn.')
            session_id, session = match
            if session['state'] != 'waiting':
                raise PairError(409, 'Mã đã được dùng. Tạo phiên mới trên máy tính nếu cần ghép lại.')
            sender = secrets.token_urlsafe(32)
            session.update(sender=sender, state='paired')
            return {'id': session_id, 'senderToken': sender, 'expiresIn': max(0, int(session['expires'] - self.clock()))}

    def send(self, session_id, token, body):
        with self.lock:
            session = self.authorized(session_id, token, 'sender')
            request = body.get('requestId')
            if request is not None and (not isinstance(request, str) or not 1 <= len(request) <= 100):
                raise PairError(400, 'Mã lượt quét không hợp lệ.')
            if request and request == session['request']:
                return {'status': 'received'}
            if session['state'] != 'paired':
                raise PairError(409, 'Máy tính chưa nhận xong lượt trước. Đợi một chút rồi gửi lại.')
            payload = validate_payload(body.get('payload'))
            sample = body.get('sample', False)
            if not isinstance(sample, bool):
                raise PairError(400, 'Trạng thái dữ liệu mẫu không hợp lệ.')
            session.update(payload=payload, sample=sample, state='received',
                           sequence=session['sequence'] + 1, request=request)
            return {'status': 'received'}

    def poll(self, session_id, token):
        with self.lock:
            session = self.authorized(session_id, token, 'owner')
            result = {'status': session['state'], 'expiresIn': max(0, int(session['expires'] - self.clock())),
                      'continuous': session['continuous'], 'sequence': session['sequence']}
            if session['state'] == 'received':
                result.update(payload=session['payload'], sample=session['sample'])
            return result

    def acknowledge(self, session_id, token, sequence):
        with self.lock:
            session = self.authorized(session_id, token, 'owner')
            if not session['continuous'] or sequence != session['sequence']:
                raise PairError(409, 'Lượt quét đã thay đổi.')
            session.update(payload=None, sample=False, state='paired')
            return {'status': 'paired'}

    def finish(self, session_id, token):
        with self.lock:
            self.authorized(session_id, token, 'owner')
            del self.sessions[session_id]
            return {'status': 'closed'}


class DemoServer(ThreadingHTTPServer):
    daemon_threads = True

    def server_bind(self):
        # Windows cho phép SO_REUSEADDR chiếm lại cổng đang nghe, khiến hai bản
        # demo nhận yêu cầu lẫn nhau. Giữ độc quyền cổng khi hệ điều hành hỗ trợ.
        if hasattr(socket, 'SO_EXCLUSIVEADDRUSE'):
            self.allow_reuse_address = False
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()

    def __init__(self, address, store=None):
        super().__init__(address, Handler)
        self.store = store or PairStore()
        self.addresses = lan_addresses()
        self.allowed_hosts = {'localhost', '127.0.0.1', *self.addresses}
        self.scheme = 'http'


class Handler(BaseHTTPRequestHandler):
    server_version = 'VinmecDemo'

    def log_message(self, *_args):
        pass  # Không ghi URL, mã phiên, token hoặc dữ liệu QR ra log.

    def setup(self):
        super().setup()
        self.connection.settimeout(10)

    def respond(self, status, data, mime='application/json; charset=utf-8'):
        raw = json.dumps(data, ensure_ascii=False).encode('utf-8') if isinstance(data, dict) else data
        self.send_response(status)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(len(raw)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('X-Frame-Options', 'DENY')
        self.end_headers()
        self.wfile.write(raw)

    def check_host(self):
        host = self.headers.get('Host', '')
        try:
            parsed = urlsplit('http://' + host)
            valid = parsed.hostname in self.server.allowed_hosts and parsed.port == self.server.server_port
        except ValueError:
            valid = False
        if not valid:
            raise PairError(403, 'Địa chỉ truy cập không hợp lệ.')
        origin = self.headers.get('Origin')
        if origin and origin != self.server.scheme + '://' + host:
            raise PairError(403, 'Không cho phép yêu cầu từ trang khác.')

    def local_only(self):
        if not ipaddress.ip_address(self.client_address[0]).is_loopback:
            raise PairError(403, 'Tạo và nhận phiên trên máy tính qua địa chỉ localhost.')

    def token(self):
        auth = self.headers.get('Authorization', '')
        return auth[7:] if auth.startswith('Bearer ') else ''

    def body(self):
        if self.headers.get_content_type() != 'application/json':
            raise PairError(415, 'Yêu cầu cần có định dạng JSON.')
        try:
            size = int(self.headers.get('Content-Length', '0'))
        except ValueError:
            raise PairError(400, 'Kích thước yêu cầu không hợp lệ.') from None
        if not 0 < size <= MAX_BODY:
            raise PairError(413, 'Yêu cầu quá lớn hoặc rỗng.')
        try:
            result = json.loads(self.rfile.read(size).decode('utf-8'))
        except (ValueError, UnicodeError):
            raise PairError(400, 'Nội dung JSON không hợp lệ.') from None
        if not isinstance(result, dict):
            raise PairError(400, 'Nội dung cần là một đối tượng JSON.')
        return result

    def do_GET(self):
        try:
            self.check_host()
            path = urlsplit(self.path).path
            if path.startswith('/api/pair/'):
                self.local_only()
                parts = path.strip('/').split('/')
                if len(parts) == 4 and parts[3] == 'result':
                    return self.respond(200, self.server.store.poll(parts[2], self.token()))
                raise PairError(404, 'Không có chức năng này.')
            if path == '/api/network':
                self.local_only()
                scheme = 'http'
                port = self.server.server_port
                return self.respond(200, {
                    'phoneUrls': [f'{scheme}://{address}:{port}/?phone=1' for address in self.server.addresses],
                    'httpsEnabled': False})
            file = path.lstrip('/') or 'index.html'
            if file not in STATIC_FILES:
                raise PairError(404, 'Không tìm thấy trang.')
            mime = {'.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8'}[Path(file).suffix]
            self.respond(200, (ROOT / file).read_bytes(), mime)
        except PairError as error:
            self.respond(error.status, {'error': error.message})
        except (OSError, TimeoutError):
            pass

    def do_POST(self):
        try:
            self.check_host()
            path = urlsplit(self.path).path
            body = self.body()
            if path == '/api/pair':
                self.local_only()
                return self.respond(201, self.server.store.create(self.client_address[0], body.get('continuous') is True))
            if path == '/api/join':
                return self.respond(200, self.server.store.join(body, self.client_address[0]))
            parts = path.strip('/').split('/')
            if len(parts) == 4 and parts[:2] == ['api', 'pair']:
                if parts[3] == 'send':
                    return self.respond(200, self.server.store.send(parts[2], self.token(), body))
                if parts[3] == 'close':
                    self.local_only()
                    return self.respond(200, self.server.store.finish(parts[2], self.token()))
                if parts[3] == 'ack':
                    self.local_only()
                    return self.respond(200, self.server.store.acknowledge(parts[2], self.token(), body.get('sequence')))
            raise PairError(404, 'Không có chức năng này.')
        except PairError as error:
            self.respond(error.status, {'error': error.message})
        except (OSError, TimeoutError):
            pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--bind', default='0.0.0.0')
    args = parser.parse_args()
    try:
        server = DemoServer((args.bind, args.port))
    except OSError:
        print('Khong mo duoc cong. Dung server cu bang Ctrl+C roi chay lai start-demo.cmd.')
        raise SystemExit(1)
    print(f'May tinh: http://127.0.0.1:{args.port}', flush=True)
    for address in server.addresses:
        print(f'Dien thoai cung Wi-Fi: http://{address}:{args.port}/?phone=1', flush=True)
    print('Demo LAN: du lieu chuyen tiep tam trong RAM, khong luu file. Ctrl+C de dung.', flush=True)
    def cleanup_loop():
        while True:
            time.sleep(10)
            with server.store.lock:
                server.store.cleanup()
    threading.Thread(target=cleanup_loop, daemon=True).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
