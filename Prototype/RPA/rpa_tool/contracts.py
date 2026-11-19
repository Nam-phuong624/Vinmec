from datetime import datetime, timezone
import json
from shared.paths import RUNTIME


def audit(event, **fields):
    """Nhật ký kỹ thuật: chỉ ghi sự kiện, số dòng và PID; không ghi dữ liệu cá nhân."""
    RUNTIME.mkdir(exist_ok=True)
    with (RUNTIME/'audit.jsonl').open('a',encoding='utf-8') as stream:
        stream.write(json.dumps(dict(at=datetime.now(timezone.utc).isoformat(),event=event,**fields))+'\n')
