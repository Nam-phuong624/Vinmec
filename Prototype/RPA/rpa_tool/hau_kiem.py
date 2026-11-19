"""Kiểm tra và hoàn tác SAU khi RPA đã chạy (không cần sửa OH):

  doi_soat(...)    chỉ đọc: mở lại từng hồ sơ đã xử lý và so với dữ liệu Excel; báo Khớp / LỆCH / TRÙNG / KHÔNG TÌM THẤY.
  khoi_phuc(...)   trả hồ sơ ĐÃ CẬP NHẬT về giá trị trước lượt chạy, nhưng chỉ khi hồ sơ chưa bị ai sửa tiếp.
                   Hồ sơ TẠO MỚI không xóa được bằng giao diện: chỉ lập danh sách để người có quyền xử lý.
Hai hàm đều ghi báo cáo .xlsx vào thư mục ngày và gọi emit(text) để hiện tiến độ.
"""
from collections import OrderedDict
from pathlib import Path
from rpa_tool import audit_trail
from rpa_tool.audit_trail import FIELDS, LABEL, fields, write_report
from rpa_tool.ohdemo_engine import fold
from shared.identity import ReviewRequired

AUDIT_REPORT = 'bao_cao_doi_soat.xlsx'
RESTORE_REPORT = 'bao_cao_khoi_phuc.xlsx'


def _diff(a, b):
    return [LABEL[k] + f': "{_s(a[k])}" ≠ "{_s(b[k])}"' for k in FIELDS if a[k] != b[k]]


def _s(v):
    return '; '.join(v) if isinstance(v, list) else str(v)


def doi_soat(engine, folder, file_name, rows, emit=lambda t: None, stop=None):
    """rows: các dòng Excel (đã read_daily). Trả về (danh sách kết quả, số bất thường). Không ghi gì vào OH."""
    entries = OrderedDict()
    for e in audit_trail.read_entries(folder, file_name):
        entries[e['line']] = e                               # lần xử lý cuối của mỗi dòng
    results, bad = [], 0
    for row in rows:
        if stop is not None and stop.is_set():
            break
        e = entries.get(row['line'])
        if not e:
            results.append([row['line'], '', 'Bỏ qua', 'Không có nhật ký xử lý (dòng lỗi / cần điền tay / chưa chạy)']); continue
        rec, manual = e['expected'], e.get('manual') or []
        try:
            cur = engine.read_back(e['pid'])
        except ReviewRequired as exc:
            results.append([row['line'], e['pid'], 'KHÔNG TÌM THẤY', str(exc)[:160]]); bad += 1; emit(f'dòng {row["line"]}: không tìm thấy {e["pid"]}'); continue
        gap = engine.mismatch(cur, rec, manual)
        full = ' '.join(x for x in (rec['first'], rec['middle'], rec['last']) if x)
        dup = []
        if engine.search(full) == 'list':
            dup = [r['pid'] for r in engine.result_rows() if fold(r['name']) == fold(full) and r['dob'][-4:] == rec['dob'][-4:]]
        if gap:
            results.append([row['line'], e['pid'], 'LỆCH', '; '.join(gap)]); bad += 1
        elif len(dup) > 1:
            results.append([row['line'], e['pid'], 'TRÙNG', 'Có ' + str(len(dup)) + ' hồ sơ cùng tên và năm sinh: ' + ', '.join(dup)]); bad += 1
        else:
            results.append([row['line'], e['pid'], 'Khớp', ''])
        emit(f'dòng {row["line"]}: {results[-1][2]}')
    write_report(Path(folder) / AUDIT_REPORT, ['Dòng Excel', 'PID', 'Kết quả đối soát', 'Chi tiết'], results)
    return results, bad


def khoi_phuc(engine, folder, file_name, emit=lambda t: None, stop=None):
    """Khôi phục các hồ sơ đã CẬP NHẬT trong lượt chạy về giá trị trước. Trả (danh sách kết quả, số hồ sơ đã khôi phục)."""
    per = OrderedDict()
    created = []
    for e in audit_trail.read_entries(folder, file_name):
        if e['action'] == 'cập nhật':
            if e['pid'] not in per:
                per[e['pid']] = dict(line=e['line'], before=e['before'], after=e['after'])
            else:
                per[e['pid']]['after'] = e['after']          # nhiều lần cập nhật: về giá trị trước lần đầu, so với giá trị sau lần cuối
        elif e['action'] == 'tạo':
            created.append(e)
    results, done = [], 0
    for pid, v in per.items():
        if stop is not None and stop.is_set():
            break
        try:
            cur = engine.read_back(pid)
            gap = _diff(fields(cur), v['after'])
            if gap:
                results.append([v['line'], pid, 'BỎ QUA', 'Hồ sơ đã bị thay đổi sau lượt chạy của RPA; không tự khôi phục để khỏi ghi đè thay đổi của người khác. ' + '; '.join(gap)])
                emit(f'{pid}: bỏ qua (đã bị sửa sau đó)'); continue
            engine.search(pid)
            engine.wait_for(lambda: 'view-pid' in engine.index, 'mở hồ sơ ' + pid)
            engine.click('edit-toggle')
            engine.wait_for(lambda: 'edit-pid' in engine.index, 'mở Edit để khôi phục')
            manual = engine.restore_fields(pid, v['before'])
            back = engine.read_back(pid)
            left = [g for g in _diff(fields(back), v['before']) if not g.startswith(LABEL['addresses'])]
            if left:
                results.append([v['line'], pid, 'KHÔNG KHÔI PHỤC ĐƯỢC HẾT', '; '.join(left + manual)])
            else:
                done += 1
                results.append([v['line'], pid, 'Đã khôi phục', '; '.join(manual)])
            emit(f'{pid}: {results[-1][2]}')
        except ReviewRequired as exc:
            results.append([v['line'], pid, 'LỖI', str(exc)[:200]])
            try:
                engine.clear_boxes(); engine.leave_edit()
            except Exception:
                pass
    for e in created:
        results.append([e['line'], e['pid'], 'CẦN NGƯỜI CÓ QUYỀN XỬ LÝ', 'Hồ sơ do RPA tạo mới: không xóa được bằng giao diện; vô hiệu hoặc gộp theo quy trình của OH.'])
    write_report(Path(folder) / RESTORE_REPORT, ['Dòng Excel', 'PID', 'Kết quả', 'Chi tiết'], results)
    return results, done
