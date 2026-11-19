"""Tiến trình RPA riêng (để nhóm J có thể "giết" nó đúng một bước). Đọc cấu hình JSON, chạy các dòng, in kết quả từng dòng."""
import json
import os
import sys
import threading
from pathlib import Path

cfg = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
HERE = Path(__file__).resolve().parent
sys.path.insert(0, os.environ.get('KT_SRC') or str(HERE.parent))
sys.path.insert(0, str(HERE))
sys.stdout.reconfigure(encoding='utf-8')
import pythoncom
pythoncom.CoInitializeEx(0)
from shared.excel import read_daily
from rpa_tool import ohdemo_engine as E
from hooks import Hooks

header, rows = read_daily(cfg['xlsx'])
byline = {r['line']: r for r in rows}
items = [byline[n] for n in cfg['lines']]
eng = E.OhDemoRPA()
stop = threading.Event()


def act(p):
    if p['do'] == 'kill_rpa':
        sys.stdout.flush()
        os._exit(137)                       # như bị Task Manager kết thúc: không dọn dẹp gì
    if p['do'] == 'set_stop':
        stop.set()


Hooks(eng, cfg.get('plan', []), act)


def emit(tag, line, text):
    print(json.dumps(dict(tag=tag, line=line, text=text), ensure_ascii=False), flush=True)


if cfg['mode'] == 'sau':
    from rpa_tool.runner import run_rows
    run_rows(eng, [(str(r['line']), r['line'], r['values'], r) for r in items], stop,
             lambda iid, text: emit('row', int(iid), text), Path(cfg['folder']), header,
             file_name=Path(cfg['xlsx']).name)
else:                                       # 'truoc': đúng như vòng lặp của app.py trước khi sửa
    for r in items:
        if stop.is_set():
            emit('row', r['line'], 'Đã dừng'); continue
        emit('row', r['line'], 'Đang xử lý…')
        try:
            emit('row', r['line'], eng.process(r, stop))
        except E.NeedManual as exc:
            emit('row', r['line'], 'Cần điền tay · ' + str(exc))
        except Exception as exc:
            emit('row', r['line'], 'Lỗi · ' + str(exc))
emit('end', 0, '')
