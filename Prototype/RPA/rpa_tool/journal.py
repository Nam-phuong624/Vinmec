"""Nhật ký tiến độ từng dòng, ghi NGAY khi bắt đầu và khi kết thúc một dòng (đóng chương trình đột ngột vẫn còn dấu vết).

Chỉ ghi tên file, số dòng, sự kiện và loại kết quả; không ghi họ tên, CCCD hay số điện thoại.
"""
import json
from datetime import datetime, timezone
from pathlib import Path
from shared import paths


def _file(runtime, file_name) -> Path:
    safe = ''.join(c if c.isalnum() or c in '._-' else '_' for c in str(file_name))
    return Path(runtime) / f'journal_{safe}.jsonl'


def record(file_name, line, event, kind=''):
    """event: 'start' | 'end'; kind: created / updated / same / manual / error (khi event == 'end')."""
    paths.RUNTIME.mkdir(exist_ok=True)
    with _file(paths.RUNTIME, file_name).open('a', encoding='utf-8') as stream:
        stream.write(json.dumps(dict(at=datetime.now(timezone.utc).isoformat(), line=line, event=event, kind=kind)) + '\n')
        stream.flush()


def unfinished(runtime, file_name) -> set:
    """Các dòng đã bắt đầu nhưng chưa kết thúc (lần ghi cuối của dòng là 'start') = đã bị ngắt giữa chừng."""
    path = _file(runtime, file_name)
    last = {}
    if path.exists():
        for text in path.read_text(encoding='utf-8').splitlines():
            try:
                item = json.loads(text)
            except ValueError:
                continue                                    # dòng cuối có thể bị cắt dở khi tiến trình chết
            last[item['line']] = item['event']
    return {line for line, event in last.items() if event == 'start'}
