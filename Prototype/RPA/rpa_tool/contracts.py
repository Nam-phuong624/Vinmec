from dataclasses import dataclass
from datetime import datetime, timezone
import json
from shared.identity import Identity
from shared.paths import RUNTIME


@dataclass(frozen=True)
class Proposal:
    snapshot: dict
    identity: Identity
    row: dict
    match_ms: float


def audit(event, **fields):
    RUNTIME.mkdir(exist_ok=True)
    with (RUNTIME/'audit.jsonl').open('a',encoding='utf-8') as stream:
        stream.write(json.dumps(dict(at=datetime.now(timezone.utc).isoformat(),event=event,**fields))+'\n')
