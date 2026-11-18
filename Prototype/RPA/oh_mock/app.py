"""Local-only simulated OH. RPA must operate its browser UI, not these routes."""
import json
import sqlite3
from contextlib import contextmanager
from flask import Flask, jsonify, render_template, request
from shared.paths import DEMO, RUNTIME


def create_app(db_path=None):
    app = Flask(__name__)
    app.config['DB'] = str(db_path or RUNTIME / 'oh.sqlite3')
    app.config['MAX_CONTENT_LENGTH'] = 64 * 1024

    @contextmanager
    def connect():
        con = sqlite3.connect(app.config['DB'])
        con.row_factory = sqlite3.Row
        try:
            with con:
                yield con
        finally:
            con.close()

    @app.before_request
    def local_only():
        # Reject foreign origins and DNS rebinding; the demo has no remote use case.
        if request.host.split(':')[0] not in ('127.0.0.1', 'localhost'):
            return jsonify(error='Chỉ dùng localhost.'), 403
        if request.method != 'GET' and request.headers.get('Origin') not in (
                None, f'http://{request.host}'):
            return jsonify(error='Nguồn yêu cầu không hợp lệ.'), 403

    @app.get('/')
    def index():
        return render_template('index.html')

    @app.get('/api/patients/<pid>')
    def patient(pid):
        with connect() as con:
            row = con.execute('SELECT data, version FROM patients WHERE pid=?', (pid,)).fetchone()
        if row is None:
            return jsonify(error='Không tìm thấy PID.'), 404
        return jsonify(**json.loads(row['data']), version=row['version'])

    @app.post('/api/patients/<pid>')
    def save(pid):
        body = request.get_json(silent=True) or {}
        address = body.get('address')
        nid = body.get('national_id', '')
        if not isinstance(address, dict) or any(not isinstance(address.get(k), str)
                or not address[k].strip() or len(address[k]) > 250 for k in ('province', 'ward', 'street')):
            return jsonify(error='Cần nhập đủ tỉnh/thành, phường/xã và số nhà/đường.'), 400
        if nid and (not isinstance(nid, str) or len(nid) != 12 or not nid.isascii() or not nid.isdigit()):
            return jsonify(error='CCCD phải có 12 chữ số.'), 400
        with connect() as con:
            row = con.execute('SELECT data, version FROM patients WHERE pid=?', (pid,)).fetchone()
            if row is None:
                return jsonify(error='Không tìm thấy PID.'), 404
            if row['version'] != body.get('version'):
                return jsonify(error='Hồ sơ đã thay đổi; mở lại và đối chiếu.'), 409
            record = json.loads(row['data'])
            record.update(address={k: address[k].strip() for k in ('province', 'ward', 'street')},
                          national_id=nid)
            changed = con.execute('UPDATE patients SET data=?, version=version+1 WHERE pid=? AND version=?',
                                 (json.dumps(record, ensure_ascii=False), pid, row['version'])).rowcount
            if changed != 1:
                return jsonify(error='Hồ sơ đã thay đổi; mở lại.'), 409
        return jsonify(**record, version=row['version'] + 1)

    return app


def initialize(db_path=None, reset=False):
    path = db_path or RUNTIME / 'oh.sqlite3'
    RUNTIME.mkdir(exist_ok=True)
    con = sqlite3.connect(path)
    try:
        with con:
            con.execute('CREATE TABLE IF NOT EXISTS patients (pid TEXT PRIMARY KEY, data TEXT NOT NULL, version INTEGER NOT NULL)')
            if reset:
                con.execute('DELETE FROM patients')
            for record in json.loads((DEMO / 'patients.json').read_text(encoding='utf-8')):
                con.execute('INSERT OR IGNORE INTO patients VALUES (?, ?, 1)',
                            (record['pid'], json.dumps(record, ensure_ascii=False)))
    finally:
        con.close()


if __name__ == '__main__':
    initialize()
    create_app().run(host='127.0.0.1', port=8765, debug=False, threaded=True)
