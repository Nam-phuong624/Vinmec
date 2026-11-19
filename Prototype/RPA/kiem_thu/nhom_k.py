"""Nhóm K: phát hiện và hoàn tác SAU khi RPA đã ghi (không cần sửa OH).

Chạy:  python kiem_thu\\nhom_k.py        → kiem_thu/ket_qua_k.json   (KT_ONLY=K01,K02 để chạy vài ca)
Kiểm tra bốn khả năng: (1) vết trước/sau đầy đủ và đúng; (2) khôi phục hồ sơ cũ về giá trị trước, từ chối khi đã bị người khác sửa;
(3) đối soát chỉ đọc không ghi gì vào OH; (4) đối soát phát hiện lệch, trùng, hồ sơ mất. Mọi thay đổi trong OH đều được đọc lại độc lập.
"""
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.argv = [sys.argv[0], 'sau']
sys.path.insert(0, str(HERE))
import nhom_i_j as IJ
from openpyxl import load_workbook
from rpa_tool import audit_trail, hau_kiem
from rpa_tool.runner import run_rows

K, E, TMP = IJ.K, IJ.E, IJ.TMP
LOGF = HERE / 'tien_do_k.log'
GROUP = 'K. Phát hiện và hoàn tác sau khi RPA đã ghi'


def log(text):
    line = f'{datetime.now():%H:%M:%S} {text}'
    print(line, flush=True)
    with LOGF.open('a', encoding='utf-8') as f:
        f.write(line + '\n')


def fl(cur):
    return IJ.fields(cur)


def no_addr(d):
    return {k: v for k, v in d.items() if k != 'addresses'}


def edit_phone(eng, pid, phone):
    """Người khác sửa SĐT hồ sơ qua giao diện (mô phỏng thay đổi sau lượt chạy của RPA)."""
    eng.leave_edit()
    assert eng.search(pid) == 'view'
    eng.click('edit-toggle')
    eng.wait_for(lambda: 'edit-pid' in eng.index, 'edit')
    eng.set_text('edit-phone', phone)
    eng.save_edit(pid)
    eng.leave_edit()


def run_ok(ctx, rows, folder, name, header):
    items = [(str(r['line']), r['line'], r['row']['values'], r['row']) for r in rows]
    out = []
    run_rows(ctx.eng, items, ctx.stop, lambda iid, text: out.append(text), folder, header, file_name=name)
    return out


def setup(sid, kinds):
    rows = [IJ.make_row(k) for k in kinds]
    xlsx, header = IJ.write_rows(rows, sid)
    folder = TMP / f'f_{sid}'
    folder.mkdir(exist_ok=True)
    for old in folder.iterdir():
        old.unlink()
    return rows, xlsx, header, folder


def pid_of(entries, line):
    return next(e['pid'] for e in entries if e['line'] == line)


def others_unchanged(after, base, allow=()):
    bad = []
    for pid in IJ.DEMO_IDS:
        if pid in allow:
            continue
        if after.get(pid) is None or fl(after[pid]) != fl(base[pid]):
            bad.append(f'{pid} bị đổi ngoài ý muốn: ' + '; '.join(f'{k}: {base[pid][k]!r} → {after[pid][k]!r}' for k in fl(base[pid]) if after.get(pid) and after[pid][k] != base[pid][k]))
    return bad


def scenario(sid, title, risk, fn):
    return dict(id=sid, title=title, risk=risk, fn=fn)


# ------------------------------------------------------------------------------------------------------ các ca
def k01(ctx, base):
    rows, xlsx, header, folder = setup('K01', ['U', 'N', 'N'])
    out = run_ok(ctx, rows, folder, xlsx.name, header)
    ctx.tidy()
    after = IJ.snap(ctx.eng)
    es = audit_trail.read_entries(folder, xlsx.name)
    issues = []
    if len(es) != 3:
        issues.append(f'R1 nhật ký có {len(es)} mục, cần 3')
        return issues, f'trạng thái: {out}'
    u, n1, n2 = (next(e for e in es if e['line'] == r['line']) for r in rows)
    if u['action'] != 'cập nhật' or u['before'] != fl(base['DEMO0001']):
        issues.append(f'R1 vết "trước" không bằng giá trị gốc đọc từ OH: {u["before"]} ≠ {fl(base["DEMO0001"])}')
    if u['after'] != fl(after['DEMO0001']):
        issues.append('R1 vết "sau" của hồ sơ cập nhật không bằng giá trị thật trong OH')
    for e in (n1, n2):
        if e['action'] != 'tạo' or e['before'] is not None or e['after'] != fl(after[e['pid']]):
            issues.append(f'R1 vết của hồ sơ tạo mới {e["pid"]} sai')
    sheet = load_workbook(folder / audit_trail.REPORT_NAME).active
    rep = [[c.value for c in r] for r in sheet.iter_rows(min_row=2)]
    if not any(r[0] == rows[0]['line'] and r[3] == 'SĐT' and r[4] == '0900000001' and r[5] == '0900000009' for r in rep):
        issues.append('R1 báo cáo đọc được thiếu dòng đổi SĐT 0900000001 → 0900000009')
    for r in rows[1:]:
        if not any(x[0] == r['line'] for x in rep):
            issues.append(f'R1 báo cáo thiếu hồ sơ tạo mới ở dòng {r["line"]}')
    issues += ['S1 ' + b for b in others_unchanged(after, base, ('DEMO0001',))]
    return issues, f'{len(es)} mục nhật ký, {len(rep)} dòng báo cáo'


def k02(ctx, base):
    rows, xlsx, header, folder = setup('K02', ['U', 'N', 'N'])
    run_ok(ctx, rows, folder, xlsx.name, header)
    ctx.tidy()
    mid = IJ.snap(ctx.eng)
    results, done = hau_kiem.khoi_phuc(ctx.eng, folder, xlsx.name)
    ctx.tidy()
    after = IJ.snap(ctx.eng)
    issues = []
    if no_addr(fl(after['DEMO0001'])) != no_addr(fl(base['DEMO0001'])):
        issues.append('R2 DEMO0001 chưa về giá trị trước lượt chạy')
    if not any(r[1] == 'DEMO0001' and r[2] == 'Đã khôi phục' and 'xóa tay' in r[3] for r in results):
        issues.append('R2 báo cáo không ghi nhận khôi phục DEMO0001 kèm việc xóa địa chỉ tay')
    pids = [e['pid'] for e in audit_trail.read_entries(folder, xlsx.name) if e['action'] == 'tạo']
    for pid in pids:
        if fl(after[pid]) != fl(mid[pid]):
            issues.append(f'R2 hồ sơ tạo mới {pid} bị thay đổi khi khôi phục')
        if not any(r[1] == pid and r[2] == 'CẦN NGƯỜI CÓ QUYỀN XỬ LÝ' for r in results):
            issues.append(f'R2 hồ sơ tạo mới {pid} không được liệt kê cho người có quyền xử lý')
    issues += ['S1 ' + b for b in others_unchanged(after, base, ('DEMO0001',))]
    return issues, f'đã khôi phục {done} hồ sơ; kết quả: ' + ' | '.join(f'{r[1]}: {r[2]}' for r in results)


def k03(ctx, base):
    rows, xlsx, header, folder = setup('K03', ['U', 'N'])
    run_ok(ctx, rows, folder, xlsx.name, header)
    ctx.tidy()
    edit_phone(ctx.eng, 'DEMO0001', '0987654321')           # người khác sửa tiếp sau lượt chạy của RPA
    results, done = hau_kiem.khoi_phuc(ctx.eng, folder, xlsx.name)
    ctx.tidy()
    after = IJ.snap(ctx.eng)
    issues = []
    if after['DEMO0001']['phone'] != '0987654321':
        issues.append('R3 khôi phục đã ghi đè thay đổi của người khác (SĐT không còn 0987654321)')
    if not any(r[1] == 'DEMO0001' and r[2] == 'BỎ QUA' for r in results):
        issues.append('R3 không báo "BỎ QUA" cho hồ sơ đã bị sửa sau lượt chạy')
    if done != 0:
        issues.append(f'R3 đã khôi phục {done} hồ sơ dù bị sửa sau đó')
    return issues, ' | '.join(f'{r[1]}: {r[2]}' for r in results)


def k04(ctx, base):
    rows, xlsx, header, folder = setup('K04', ['U', 'N', 'N'])
    run_ok(ctx, rows, folder, xlsx.name, header)
    ctx.tidy()
    before = IJ.snap(ctx.eng)
    results, bad = hau_kiem.doi_soat(ctx.eng, folder, xlsx.name, [r['row'] for r in rows])
    ctx.tidy()
    after = IJ.snap(ctx.eng)
    issues = []
    if bad or [r[2] for r in results] != ['Khớp'] * 3:
        issues.append('R4 đối soát báo bất thường dù mọi thứ đúng: ' + str([r[2] for r in results]))
    if any(fl(after[p]) != fl(before[p]) for p in before) or set(after) != set(before):
        issues.append('R4 đối soát "chỉ đọc" nhưng hồ sơ trong OH đã thay đổi')
    return issues, 'kết quả đối soát: ' + str([r[2] for r in results])


def k05(ctx, base):
    rows, xlsx, header, folder = setup('K05', ['U', 'N', 'N'])
    run_ok(ctx, rows, folder, xlsx.name, header)
    ctx.tidy()
    es = audit_trail.read_entries(folder, xlsx.name)
    edit_phone(ctx.eng, pid_of(es, rows[1]['line']), '0977000555')            # hồ sơ bị người khác sửa
    r2 = rows[2]
    K.setup_manual(ctx.eng, r2['raw']['last'], r2['raw']['middle'], r2['raw']['given'], r2['truth']['dob'][-4:], '0911999111')   # bị tạo trùng
    ctx.tidy()
    results, bad = hau_kiem.doi_soat(ctx.eng, folder, xlsx.name, [r['row'] for r in rows])
    st = [r[2] for r in results]
    issues = []
    if st != ['Khớp', 'LỆCH', 'TRÙNG']:
        issues.append(f'R4 đối soát phải ra [Khớp, LỆCH, TRÙNG], thực tế {st}')
    return issues, f'kết quả: {st}; chi tiết: ' + ' | '.join(r[3][:60] for r in results)


def k06(ctx, base):
    rows, xlsx, header, folder = setup('K06', ['U', 'N', 'N'])
    run_ok(ctx, rows, folder, xlsx.name, header)
    ctx.tidy()
    ctx.relaunch()                                                         # OH mất dữ liệu (như phục hồi từ bản cũ)
    results, bad = hau_kiem.doi_soat(ctx.eng, folder, xlsx.name, [r['row'] for r in rows])
    st = [r[2] for r in results]
    issues = []
    if st != ['LỆCH', 'KHÔNG TÌM THẤY', 'KHÔNG TÌM THẤY']:
        issues.append(f'R4 đối soát phải ra [LỆCH, KHÔNG TÌM THẤY, KHÔNG TÌM THẤY], thực tế {st}')
    return issues, f'kết quả: {st}'


def k07(ctx, base):
    rows, xlsx, header, folder = setup('K07', ['N', 'U', 'N'])
    tgt = rows[2]
    plan = [dict(IJ.P('after', 'click:new-save', 'kill_rpa'), line=tgt['line'])]
    code, res = IJ.run_sub(dict(tag='K07a', xlsx=str(xlsx), lines=[r['line'] for r in rows], mode='sau', plan=plan, folder=str(folder)))
    ctx.tidy()
    es = audit_trail.read_entries(folder, xlsx.name)
    issues = []
    if code != 137:
        issues.append(f'LỖI HARNESS: RPA không bị tắt đúng bước (mã {code})')
    lines = sorted(e['line'] for e in es)
    if lines != sorted(r['line'] for r in rows[:2]):
        issues.append(f'R1 sau khi RPA bị tắt, nhật ký phải có đúng 2 dòng đã xong, thực tế {lines}')
    results, done = hau_kiem.khoi_phuc(ctx.eng, folder, xlsx.name)
    ctx.tidy()
    after = IJ.snap(ctx.eng)
    if no_addr(fl(after['DEMO0001'])) != no_addr(fl(base['DEMO0001'])):
        issues.append('R2 khôi phục sau khi RPA bị tắt giữa chừng không đưa DEMO0001 về giá trị trước')
    issues += ['S1 ' + b for b in others_unchanged(after, base, ('DEMO0001',))]
    return issues, f'RPA bị tắt ở dòng 3; nhật ký {lines}; khôi phục: ' + ' | '.join(f'{r[1]}: {r[2]}' for r in results)


SCEN = [
    scenario('K01', 'Vết trước/sau của từng hồ sơ đầy đủ và khớp OH', 'Muốn kiểm tra hoặc hoàn tác phải biết chính xác RPA đã đổi gì.', k01),
    scenario('K02', 'Khôi phục hồ sơ đã cập nhật về giá trị trước lượt chạy', 'Cập nhật nhầm phải đưa lại được; hồ sơ tạo mới không được tự ý đụng tới.', k02),
    scenario('K03', 'Từ chối khôi phục khi hồ sơ đã bị người khác sửa sau lượt chạy', 'Khôi phục không được ghi đè thay đổi của người khác.', k03),
    scenario('K04', 'Đối soát chỉ đọc khi mọi thứ đúng', 'Đối soát phải báo Khớp và không được ghi gì vào OH.', k04),
    scenario('K05', 'Đối soát phát hiện hồ sơ bị sửa lệch và bị tạo trùng', 'Sai sót phát sinh sau khi RPA ghi phải bị phát hiện.', k05),
    scenario('K06', 'Đối soát phát hiện hồ sơ biến mất / OH mất dữ liệu', 'Hồ sơ RPA đã tạo mà không còn trong OH phải được báo.', k06),
    scenario('K07', 'Khôi phục sau khi RPA bị tắt giữa lượt chạy', 'Vết phải còn cho các dòng đã xong; khôi phục vẫn dùng được.', k07),
]


def main():
    if not os.environ.get('KT_ONLY'):
        LOGF.write_text('', encoding='utf-8')
    started = datetime.now()
    out, holder = [], {}
    only = os.environ.get('KT_ONLY')
    for s in SCEN:
        if only and s['id'] not in only.split(','):
            continue
        t0 = time.time()
        ctx = IJ.Ctx()
        if 'base' not in holder:
            first = IJ.snap(ctx.eng)
            ctx.eng.leave_edit()
            second = IJ.snap(ctx.eng)                              # chỉ nhận trạng thái gốc khi hai lần đọc giống nhau
            ctx.eng.leave_edit()
            if {k: (v and fl(v)) for k, v in first.items()} != {k: (v and fl(v)) for k, v in second.items()}:
                raise SystemExit('Trạng thái gốc của OH không ổn định giữa hai lần đọc; dừng kiểm thử.')
            holder['base'] = second
        try:
            issues, summary = s['fn'](ctx, holder['base'])
        except Exception as exc:
            issues, summary = [f'LỖI HARNESS {type(exc).__name__}: {exc}'], ''
        finally:
            ctx.close()
        issues = list(dict.fromkeys(issues))
        r = dict(id=s['id'], group=GROUP, title=s['title'], risk=s['risk'], expected='SAFE', kw='', pre='', sev='Cao', note='', raw={}, truth=None,
                 line=0, pid='', actual=summary, actual_type='SAFE' if not issues else 'UNSAFE', before=None, after=None, recon=issues,
                 verdict='ĐẠT' if not issues else 'KHÔNG ĐẠT', why='; '.join(issues), dur=round(time.time() - t0, 1), rerun_of='', side=False)
        out.append(r)
        log(f'{r["id"]} {r["verdict"]} | {r["actual"][:150]} | {r["why"][:250]}')
    outfile = HERE / 'ket_qua_k.json'
    if only and outfile.exists():
        old = {c['id']: c for c in json.loads(outfile.read_text(encoding='utf-8'))['cases']}
        old.update({c['id']: c for c in out})
        out = [old[k] for k in sorted(old)]
    outfile.write_text(json.dumps(dict(meta=dict(started=started.isoformat(timespec='seconds'), finished=datetime.now().isoformat(timespec='seconds')), cases=out),
                                  ensure_ascii=False, indent=1), encoding='utf-8')
    log(f'Xong: {len(out)} ca, ĐẠT {sum(c["verdict"] == "ĐẠT" for c in out)}, KHÔNG ĐẠT {sum(c["verdict"] == "KHÔNG ĐẠT" for c in out)}')


if __name__ == '__main__':
    main()
