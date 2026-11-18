"""Private CLI used only by OHDesktop.exe; no TCP listener or web server."""
from pathlib import Path
import json
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from oh_desktop.store import get, save, find_by_cccd, create, search_patients

if __name__=='__main__':
    sys.stdin.reconfigure(encoding='utf-8')
    sys.stdout.reconfigure(encoding='utf-8')
    try:
        path=Path(sys.argv[1])
        request=json.load(sys.stdin)
        if request.get('action')=='get':
            result=get(path,request['pid'])
        elif request.get('action')=='save':
            result=save(path,request['record'])
        elif request.get('action')=='find':
            result=find_by_cccd(path,request['national_id'])
        elif request.get('action')=='create':
            result=create(path,request['record'])
        elif request.get('action')=='list':
            result=search_patients(path,request.get('query',''),request.get('offset',0),request.get('limit',50))
        else:
            raise ValueError('Thao tác không hợp lệ.')
        print(json.dumps(dict(ok=True,record=result),ensure_ascii=False))
    except Exception as exc:
        print(json.dumps(dict(ok=False,error=str(exc)),ensure_ascii=False))
