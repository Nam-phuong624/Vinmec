"""SQLite persistence owned by OH; desktop automation never imports this module."""
import json
import sqlite3
import unicodedata
from contextlib import contextmanager
from shared.paths import DEMO, RUNTIME
from shared.identity import dob, national_id, visit_datetime


@contextmanager
def database(path):
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    try:
        with connection:
            yield connection
    finally:
        connection.close()


def initialize(path=None, reset=False):
    path = path or RUNTIME/'oh.sqlite3'
    path.parent.mkdir(parents=True, exist_ok=True)
    with database(path) as connection:
        connection.execute('CREATE TABLE IF NOT EXISTS patients (pid TEXT PRIMARY KEY, data TEXT NOT NULL, version INTEGER NOT NULL)')
        connection.execute('CREATE TABLE IF NOT EXISTS pid_sequence (id INTEGER PRIMARY KEY, value INTEGER NOT NULL)')
        connection.execute('INSERT OR IGNORE INTO pid_sequence VALUES (1, 0)')
        if reset:
            connection.execute('DELETE FROM patients')
            connection.execute('UPDATE pid_sequence SET value=0 WHERE id=1')
        for record in json.loads((DEMO/'patients.json').read_text(encoding='utf-8')):
            connection.execute('INSERT OR IGNORE INTO patients VALUES (?, ?, 1)',
                               (record['pid'],json.dumps(record,ensure_ascii=False)))


def get(path, pid):
    with database(path) as connection:
        row=connection.execute('SELECT data, version FROM patients WHERE pid=?',(pid,)).fetchone()
    if row is None:
        raise ValueError('Không tìm thấy PID.')
    return dict(**json.loads(row['data']),version=row['version'])


def search_patients(path,query='',offset=0,limit=50):
    """Browse persisted OH records, newest first, with literal accent-insensitive search."""
    if not isinstance(query,str) or len(query)>250:
        raise ValueError('Từ khóa tìm kiếm không hợp lệ.')
    if not isinstance(offset,int) or offset<0 or not isinstance(limit,int) or not 1<=limit<=100:
        raise ValueError('Trang danh sách không hợp lệ.')
    def fold(value):
        value=unicodedata.normalize('NFD',str(value).casefold().replace('đ','d'))
        return ''.join(c for c in value if unicodedata.category(c)!='Mn')
    columns=('pid','name','dob','national_id','company','batch','package_code','visit_date')
    phrase=fold(query).strip();tokens=phrase.split()
    with database(path) as connection:
        records=connection.execute('SELECT data FROM patients ORDER BY rowid DESC').fetchall()
    matches=[]
    for item in records:
        record=json.loads(item['data'])
        name=fold(record.get('name',''))
        if any(phrase in fold(record.get(key,'')) for key in columns) or all(token in name for token in tokens):
            matches.append({key:str(record.get(key,'') or '') for key in columns})
    return dict(items=matches[offset:offset+limit],total=len(matches),offset=offset,limit=limit)


def save(path, record):
    address=record.get('address')
    if not isinstance(address,dict) or any(not isinstance(address.get(k),str) or not address[k].strip()
            or len(address[k])>250 for k in ('province','ward','street')):
        raise ValueError('Cần nhập đủ tỉnh/thành, phường/xã và số nhà/đường.')
    nid=record.get('national_id','')
    if not isinstance(nid,str) or (nid and (len(nid)!=12 or not nid.isascii() or not nid.isdigit())):
        raise ValueError('CCCD phải có 12 chữ số.')
    with database(path) as connection:
        row=connection.execute('SELECT data, version FROM patients WHERE pid=?',(record['pid'],)).fetchone()
        if row is None:
            raise ValueError('Không tìm thấy PID.')
        if row['version']!=record.get('version'):
            raise ValueError('Hồ sơ đã thay đổi; tải lại và đối chiếu.')
        result=json.loads(row['data'])
        result.update(national_id=nid,address={k:address[k].strip() for k in ('province','ward','street')})
        changed=connection.execute('UPDATE patients SET data=?, version=version+1 WHERE pid=? AND version=?',
            (json.dumps(result,ensure_ascii=False),record['pid'],record['version'])).rowcount
        if changed!=1:
            raise ValueError('Hồ sơ đã thay đổi; tải lại và đối chiếu.')
    return dict(**result,version=row['version']+1)


def find_by_cccd(path,nid):
    nid=national_id(nid)
    with database(path) as connection:
        rows=connection.execute('SELECT data, version FROM patients WHERE json_extract(data,\'$.national_id\')=?',(nid,)).fetchall()
    if len(rows)>1:
        raise ValueError('Có nhiều hồ sơ cùng CCCD; cần kiểm tra thủ công.')
    return dict(**json.loads(rows[0]['data']),version=rows[0]['version']) if rows else {}


def create(path,record):
    """OH allocates the PID, with duplicate check and allocation in one transaction."""
    nid=national_id(record.get('national_id'))
    required=('name','sex','company','batch','package_code')
    if any(not isinstance(record.get(key),str) or not record[key].strip() for key in required):
        raise ValueError('Thiếu tên, giới tính, công ty/đợt hoặc mã gói khám.')
    birth=dob(record.get('dob'));visit=visit_datetime(record.get('visit_date'))
    with database(path) as connection:
        connection.execute('BEGIN IMMEDIATE')
        existing=connection.execute("SELECT pid FROM patients WHERE json_extract(data,'$.national_id')=?",(nid,)).fetchone()
        if existing:
            raise ValueError('CCCD đã có hồ sơ PID '+existing['pid']+'. Không tạo mới.')
        while True:
            connection.execute('UPDATE pid_sequence SET value=value+1 WHERE id=1')
            number=connection.execute('SELECT value FROM pid_sequence WHERE id=1').fetchone()['value']
            pid=f'NEW{number:06d}'
            if not connection.execute('SELECT 1 FROM patients WHERE pid=?',(pid,)).fetchone():break
        fields=('name','sex','company','batch','phone','nationality','policy_code','policy_name',
                'package_code','package_name','address_original')
        result={key:str(record.get(key,'')).strip() for key in fields}
        result.update(pid=pid,national_id=nid,dob=birth,visit_date=visit,
                      address={'province':'','ward':'','street':''})
        connection.execute('INSERT INTO patients VALUES (?,?,1)',(pid,json.dumps(result,ensure_ascii=False)))
    return dict(**result,version=1)
