"""Chèn "hành động" vào giữa các bước của RPA để mô phỏng người dùng can thiệp, hoặc ngắt tiến trình đúng một bước.

Bọc các hàm bước của OhDemoRPA (search, open_pid, click, set_text, select, read_edit, apply, add_address, save_edit).
Mỗi lần gọi sinh khóa như 'click:edit-save' hoặc 'set_text:edit-phone'; kế hoạch nói: trước/sau khóa nào (lần thứ mấy,
trong dòng Excel nào) thì thực hiện hành động nào.
"""
from collections import Counter

NAMES = ('search', 'open_pid', 'click', 'set_text', 'select', 'read_edit', 'apply', 'add_address', 'save_edit')


class Hooks:
    def __init__(self, eng, plan, act):
        self.eng, self.act = eng, act
        self.plan = [dict(p, done=False) for p in plan]
        self.counts, self.trace, self.errors, self.line = Counter(), [], [], None
        orig_process = eng.process

        def process(row, *a, **k):
            self.counts.clear()
            self.line = row.get('line')
            self.trace.append(f'== dòng {self.line}')
            return orig_process(row, *a, **k)
        eng.process = process
        for name in NAMES:
            setattr(eng, name, self._wrap(name, getattr(eng, name)))

    def _wrap(self, name, orig):
        def call(*a, **k):
            key = f'{name}:{a[0]}' if name in ('click', 'set_text', 'select') and a else name
            self.counts[key] += 1
            n = self.counts[key]
            self._fire('before', key, n)
            result = orig(*a, **k)
            self._fire('after', key, n)
            return result
        return call

    def _fire(self, when, key, n):
        self.trace.append(f'{when}:{key}#{n}')
        for p in self.plan:
            if (not p['done'] and p['when'] == when and p['key'] == key and p.get('nth', 1) == n
                    and p.get('line') in (None, self.line)):
                p['done'] = True
                self.trace.append(f'>> {p["do"]} {p.get("arg", "")}'.strip())
                try:
                    self.act(p)
                except Exception as exc:                      # lỗi của chính hành động giả lập, không phải của RPA
                    self.errors.append(f'{p["do"]}: {type(exc).__name__}: {exc}')
