"""Vòng lặp xử lý danh sách của RPA (dùng chung cho cửa sổ app và cho kiểm thử).

Mỗi dòng: ghi nhật ký bắt đầu → xử lý → ghi nhật ký kết thúc; dòng Lỗi / Cần điền tay được ghi NGAY vào ds lỗi.xlsx
(không đợi cả lượt chạy xong) để tắt RPA giữa chừng cũng không mất danh sách dòng phải xử lý tay.
"""
from pathlib import Path
from shared.excel import write_errors
from rpa_tool import audit_trail, journal
from rpa_tool.ohdemo_engine import NeedManual

MANUAL = 'Cần điền tay'


def run_rows(engine, items, stop, emit, folder, header, prior_errors=(), file_name=''):
    """items: [(iid, line, values, row)]. emit(iid, văn bản trạng thái). prior_errors: [(row, lý do)] đã có từ trước (dòng Cần điền tay)."""
    counts = dict(created=0, updated=0, same=0, manual=0, error=0)
    errors = list(prior_errors)

    def note(row, reason):
        errors.append((row, reason))
        try:
            write_errors(Path(folder), header, errors)
        except OSError:
            pass                                            # file đang mở trong Excel: lần ghi sau/cuối lượt sẽ thử lại

    def trail(line):
        """Ghi vết trước/sau của dòng vừa xong (nếu có hồ sơ liên quan) ngay lập tức."""
        change = getattr(engine, 'last_change', None)
        if not change:
            return
        try:
            audit_trail.record(folder, dict(file=file_name, line=line, **change))
            audit_trail.write_change_report(folder)
        except OSError:
            pass                                            # file báo cáo đang mở trong Excel: nhật ký .jsonl vẫn đã được ghi

    for iid, line, _values, row in items:
        if stop.is_set():
            emit(iid, 'Đã dừng')
            continue
        emit(iid, 'Đang xử lý…')
        journal.record(file_name, line, 'start')
        try:
            text = engine.process(row, stop)
            kind = 'created' if text.startswith('Đã tạo') else 'updated' if text.startswith('Đã cập nhật') else 'same'
            counts[kind] += 1
            trail(line)
            emit(iid, text)
        except NeedManual as exc:
            kind = 'manual'
            counts['manual'] += 1
            trail(line)
            emit(iid, f'{MANUAL} · {exc}')
            note(row, str(exc))
        except Exception as exc:
            kind = 'error'
            counts['error'] += 1
            emit(iid, 'Lỗi · ' + str(exc))
            note(row, str(exc))
        journal.record(file_name, line, 'end', kind)
    return counts
