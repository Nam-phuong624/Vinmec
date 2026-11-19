"""Sinh báo cáo KIEM_THU_RPA.md từ kiem_thu/ket_qua.json (toàn bộ số liệu lấy từ lần chạy thật, không nhập tay)."""
import json
import sys
from collections import OrderedDict
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
DATA = json.loads((HERE / 'ket_qua.json').read_text(encoding='utf-8'))
CASES, META = DATA['cases'], DATA['meta']
_ij = HERE / 'ket_qua_ij_sau.json'
_ijb = HERE / 'ket_qua_ij_truoc.json'
IJ_META = json.loads(_ij.read_text(encoding='utf-8'))['meta'] if _ij.exists() else None
IJ_BEFORE = json.loads(_ijb.read_text(encoding='utf-8'))['cases'] if _ijb.exists() else []
if _ij.exists():
    CASES = CASES + json.loads(_ij.read_text(encoding='utf-8'))['cases']
_k = HERE / 'ket_qua_k.json'
if _k.exists():
    CASES = CASES + json.loads(_k.read_text(encoding='utf-8'))['cases']

SUGGEST = {
    'E06': 'Thêm kiểm tra họ tên chỉ gồm chữ cái, khoảng trắng, dấu nháy, gạch nối; ngoài ra chuyển sang "Lỗi" để người xử lý.',
    'E07': 'Như E06 (loại ký tự ngoài chữ cái).', 'E08': 'Như E06.',
    'E13': 'Chuẩn hóa giới tính: bỏ khoảng trắng, không phân biệt hoa/thường, chuẩn hóa Unicode (NFC) trước khi so với Nam/Nữ/Khác.',
    'E14': 'Như E13.', 'E15': 'Như E13 (chuẩn hóa Unicode).', 'E16': 'Như E13.',
    'E21': 'Chấp nhận thêm định dạng dd-mm-yyyy.', 'E23': 'Chặn ngày sinh ở tương lai.', 'E24': 'Chặn tuổi trên 120.',
    'E31': 'Chuẩn hóa SĐT: bỏ dấu cách, gạch ngang, dấu chấm trước khi kiểm tra.', 'E32': 'Chấp nhận số quốc tế (+84…) hoặc chuyển +84 thành 0.',
    'E33': 'Giới hạn độ dài SĐT (ví dụ 8 đến 15 chữ số).', 'E34': 'Cảnh báo/lỗi khi ô SĐT là số nguyên (đã mất số 0 đầu) hoặc có đúng 9 chữ số không bắt đầu bằng 0.',
    'E43': 'Kiểm tra độ dài địa chỉ ≤ 250 ký tự trước khi nhập, báo lỗi thay vì để OH cắt.',
    'C08': 'So sánh tên sau khi chuẩn hóa Unicode (NFC) để không coi là thay đổi.',
    'F05': 'Bắt thêm lỗi file hỏng (zipfile.BadZipFile, InvalidFileException) trong app.load() và báo "không đọc được file".',
    'G06': 'Bắt lỗi mất kết nối (COMError) và báo rõ "cửa sổ OH đã đóng, hãy mở lại OHDemo".',
    'D08': 'Không ghi đè tên khi hai tên chỉ khác dấu/hoa thường; hoặc ghi nhận và hỏi người dùng.',
    'C06': 'Cân nhắc không ghi đè tên khi chỉ khác hoa/thường.', 'C07': 'Như C06.',
    'C15': 'Quyết định nghiệp vụ: sửa tên đệm trong Excel có coi là cùng người không (hiện tạo hồ sơ mới).',
}


def esc(s, n=None):
    s = '' if s is None else str(s)
    s = s.replace('|', '¦').replace('\r', ' ').replace('\n', ' ⏎ ')
    if n and len(s) > n:
        s = s[:n - 1] + '…'
    return s


def fmt(v):
    if v is None or v == '':
        return '(trống)'
    if isinstance(v, int) and not isinstance(v, bool):
        return f'số {v}'
    if isinstance(v, str) and len(v) >= 10 and v[4:5] == '-' and v[10:11] in ('T', ' ') and v[:4].isdigit():
        return f'ngày giờ {v[:10]}'
    return str(v)


def inp(raw):
    if not raw:
        return '(đọc file)'
    keys = [('last', 'Họ'), ('middle', 'Đệm'), ('given', 'Tên'), ('dob', 'NS'), ('sex', 'GT'), ('phone', 'SĐT'), ('addr', 'ĐC'), ('nat', 'QT'), ('title', 'Title')]
    return '; '.join(f'{lab}={esc(fmt(raw.get(k)), 70)}' for k, lab in keys)


def short(c):
    return {'CREATE': 'Tạo mới', 'UPDATE': 'Cập nhật', 'SAME': 'Không đổi', 'ERROR': 'Lỗi (dừng dòng)', 'MANUAL': 'Cần điền tay', 'OTHER': 'Khác', 'SAFE': 'Không ghi sai, chạy lại hội tụ', 'UNSAFE': 'Vi phạm bất biến an toàn'}.get(c, c)


groups = OrderedDict()
for c in CASES:
    groups.setdefault(c['group'], []).append(c)
order = sorted(groups, key=lambda g: (g.split('.')[0] if not g.startswith('C. Cập nhật (') else 'C0', g))
total, passed = len(CASES), sum(c['verdict'] == 'ĐẠT' for c in CASES)
failed = [c for c in CASES if c['verdict'] == 'KHÔNG ĐẠT']
notrun = [c for c in CASES if c['verdict'] == 'CHƯA CHẠY']
out = []
w = out.append

w('# Kiểm thử RPA_OHDemo: các trường hợp có thể gây lỗi\n')
w(f'*Báo cáo sinh tự động từ lần chạy thật ngày {META["started"][:10].replace("-", "/")} ({META["started"][11:16]} – {META["finished"][11:16]}). '
  f'Toàn bộ số liệu bên dưới lấy từ file `kiem_thu/ket_qua.json`, không nhập tay.*\n')

w('## 1. Mục đích và phạm vi\n')
w('Kiểm tra RPA_OHDemo (đọc danh sách Excel và tự điền vào OHDemo) trong các tình huống có thể sinh lỗi, và ghi nhận kết quả thực tế của từng ca. '
  'Mục tiêu không phải chứng minh "không bao giờ lỗi", mà là: (1) tìm ra những chỗ RPA nhập sai hoặc nhập thầm lặng, (2) xác nhận dữ liệu sai/thiếu bị chặn và báo rõ, '
  '(3) có số liệu cụ thể để trình bày.\n')
w('Phạm vi: chương trình `RPA_OHDemo` (bộ điều khiển `rpa_tool/ohdemo_engine.py` và đọc file `shared/excel.py`) làm việc với `OHDemo.exe` (OH mô phỏng). '
  '**Không** gồm OH thật, việc in phiếu và chương trình In_Phieu.\n')

w('## 2. Môi trường và dữ liệu\n')
w('| Mục | Giá trị |\n|---|---|')
for k, v in (('Thời điểm chạy', f'{META["started"].replace("T", " ")} → {META["finished"].replace("T", " ")}'), ('Hệ điều hành', META['os']),
             ('Python', META['python']), ('Bộ điều khiển (ohdemo_engine.py)', f'SHA-256 `{META["engine_sha"]}…`'),
             ('OHDemo.exe', f'SHA-256 `{META["ohdemo_sha"]}…`'), ('Hạt giống sinh dữ liệu', META['seed']),
             ('Tổng số ca', total)):
    w(f'| {k} | {v} |')
w('')
w('**Dữ liệu:** sinh tự động bằng `kiem_thu/chay_kiem_thu.py` (cùng hạt giống thì ra cùng dữ liệu), lưu ở `kiem_thu/du_lieu_kiem_thu.xlsx` (đúng định dạng file ds bung). '
  'Tên người ghép từ danh sách họ, đệm, tên tiếng Việt có dấu; ngày sinh nhiều định dạng (chuỗi dd/mm/yyyy, yyyy-mm-dd, ddmmyyyy, ô ngày của Excel); '
  'địa chỉ 2 đến 3 phần; mỗi người duy nhất theo (họ tên, năm sinh) và SĐT. Ngoài dữ liệu hợp lệ còn có các ca sai, lỗi, thiếu đặt tay (nhóm D, E, F, G).\n')

w('## 3. Phương pháp\n')
w('1. **Mong đợi viết trước.** Mỗi ca có kết quả mong đợi (Tạo mới / Cập nhật / Không đổi / Lỗi / Cần điền tay) và, nếu là lỗi, từ khóa phải có trong thông báo.')
w('2. **Chạy thật.** Đưa từng dòng qua đúng hàm xử lý của RPA (`process`) trên OHDemo thật, cửa sổ OH hiện bình thường.')
w('3. **Đối soát độc lập.** Sau khi chạy, mở lại từng hồ sơ trong OH, đọc các trường và so với **dữ liệu gốc do người viết ca nêu** (không so với kết quả mà RPA tự tính), để bắt lỗi nhập sai thầm lặng.')
w('4. **Kiểm tra tác động phụ.** Với ca mong đợi "Lỗi", đếm số hồ sơ cùng tên trong OH trước và sau: phải không đổi (không được tạo hoặc sửa gì).')
w('5. **Chạy lại lần 2 (nhóm B).** Chạy lại toàn bộ nhóm A và H: phải ra "Không đổi", không tạo trùng, PID không đổi.')
w('6. **Tiêu chí ĐẠT:** thực tế đúng mong đợi **và** đối soát khớp **và** không có tác động phụ. Chỉ cần sai một điều kiện là KHÔNG ĐẠT.')
w('7. **Lưu ý về tiêu chí:** một số mong đợi (đánh dấu "mong đợi tiêu chí thực tế" trong ghi chú) là yêu cầu hợp lý của người dùng nhưng RPA hiện chưa làm; các ca này KHÔNG ĐẠT là có chủ ý để lộ ra điểm cần cải thiện.\n')

w('8. **Nhóm I và J (can thiệp và ngắt giữa chừng).** Mỗi ca chèn đúng một thao tác vào giữa hai bước của RPA (người dùng tìm hồ sơ khác, gõ vào ô, bấm nút, thu nhỏ cửa sổ...) hoặc tắt OH / tắt tiến trình RPA / bấm Dừng ở đúng bước đó, rồi đọc lại **toàn bộ** hồ sơ trong OH. '
  'ĐẠT khi giữ đủ các bất biến: S1 không đổi hồ sơ khác (không ghi nhầm người); S2 báo thành công thì dữ liệu phải khớp Excel, OH đã tắt thì không được báo thành công; S3 không tạo trùng hay hồ sơ ngoài ý định; '
  'S4 hồ sơ nửa vời phải được nêu trong thông báo; S5 (tắt RPA) dòng dở phải để lại dấu vết và dòng lỗi trước đó phải còn trong ds lỗi.xlsx; C1 chạy lại khi không còn can thiệp thì hội tụ đúng. '
  'Thao tác "người dùng" được chèn đồng bộ giữa hai bước (tái lập được), không chạy song song ngẫu nhiên.')

w('9. **Nhóm K (phát hiện và hoàn tác sau khi ghi).** Kiểm tra vết trước/sau khớp với hồ sơ thật trong OH, khôi phục hồ sơ cập nhật về giá trị trước (và từ chối khi hồ sơ đã bị người khác sửa), đối soát chỉ đọc không ghi gì vào OH, đối soát phát hiện lệch, trùng, hồ sơ mất, và khôi phục sau khi RPA bị tắt giữa lượt chạy.')

w('## 4. Tổng hợp kết quả\n')
w(f'**Tổng: {total} ca, ĐẠT {passed}, KHÔNG ĐẠT {len(failed)}' + (f', CHƯA CHẠY {len(notrun)}' if notrun else '') + f' ({passed / max(1, total - len(notrun)) * 100:.1f}% đạt trong số ca đã chạy).**\n')
w('| Nhóm | Số ca | Đạt | Không đạt | Tỷ lệ đạt |\n|---|---:|---:|---:|---:|')
for g in order:
    cs = groups[g]
    ok = sum(c['verdict'] == 'ĐẠT' for c in cs)
    ran = [c for c in cs if c['verdict'] != 'CHƯA CHẠY']
    w(f'| {g} | {len(cs)} | {ok} | {len(ran) - ok} | {(ok / len(ran) * 100 if ran else 0):.0f}% |')
w('')
bulk = [c for c in CASES if c['group'][0] in 'AHB']
bulk = [c for c in bulk if c['verdict'] != 'CHƯA CHẠY']
bok = sum(c['verdict'] == 'ĐẠT' for c in bulk)
times = [c['dur'] for c in CASES if c['group'][0] in 'AH' and c['dur']]
if times:
    w(f'**Hiệu năng (nhóm A và H, {len(times)} dòng tạo mới):** trung bình {sum(times) / len(times):.2f} giây/dòng, nhanh nhất {min(times):.2f}, chậm nhất {max(times):.2f} giây.\n')
if bulk:
    if bok == len(bulk):
        w(f'**Luồng chính ổn định:** {len(bulk)} lần chạy (tạo mới và chạy lại) đều đạt, đối soát khớp. Theo "quy tắc ba", 0 lỗi trong {len(bulk)} lần chỉ cho phép kết luận '
          f'tỷ lệ lỗi thật dưới khoảng {3 / len(bulk) * 100:.1f}% (độ tin cậy 95%), không phải bằng 0.\n')
    else:
        bad = len(bulk) - bok
        w(f'**Luồng chính:** {bok}/{len(bulk)} lần chạy đạt, {bad} lần không đạt (xem mục 5).\n')

w('## 5. Các phát hiện (ca không đạt)\n')
if not failed:
    w('Không có ca nào không đạt.\n')
else:
    w(f'Có **{len(failed)} ca không đạt**, nhóm theo mức nghiêm trọng khai báo cho ca (Cao = có thể nhập sai/trùng dữ liệu hoặc chặn quy trình; Thấp = bất tiện hoặc thay đổi thừa).\n')
    for sev in ('Cao', 'Trung bình', 'Thấp'):
        fs = [c for c in failed if c['sev'] == sev]
        if not fs:
            continue
        w(f'### Mức {sev} ({len(fs)} ca)\n')
        w('| Mã | Tình huống | Mong đợi | Thực tế | Lý do không đạt | Đề xuất |\n|---|---|---|---|---|---|')
        for c in fs:
            w(f'| {c["id"]} | {esc(c["title"], 60)} | {short(c["expected"])} | {short(c["actual_type"])}: {esc(c["actual"], 70)} | {esc(c["why"], 140)} | {esc(SUGGEST.get(c["id"], "Xem chi tiết ca ở mục 6."), 120)} |')
        w('')

if IJ_BEFORE:
    after = {c['id']: c for c in CASES if c['group'][0] in 'IJ'}
    fb = [c for c in IJ_BEFORE if c['verdict'] != 'ĐẠT']
    w('### Nhóm I và J: so sánh trước và sau khi sửa mã\n')
    w(f'Cùng bộ {len(IJ_BEFORE)} ca được chạy trên mã **trước khi sửa** ({sum(c["verdict"] == "ĐẠT" for c in IJ_BEFORE)} đạt, {len(fb)} không đạt) rồi trên mã **sau khi sửa** '
      f'({sum(c["verdict"] == "ĐẠT" for c in after.values())} đạt, {sum(c["verdict"] != "ĐẠT" for c in after.values())} không đạt).\n')
    w('| Mã | Tình huống | Trước khi sửa | Sau khi sửa |\n|---|---|---|---|')
    for c in fb:
        a = after.get(c['id'], {})
        w(f'| {c["id"]} | {esc(c["title"], 70)} | {esc(c["why"], 170)} | {a.get("verdict", "—")}: {esc((a.get("actual") or "").split(" | ")[0], 150)} |')
    w('')

w('## 6. Kết quả chi tiết từng ca\n')
w('Cột "Đối soát": **khớp** = hồ sơ đọc lại từ OH khớp dữ liệu gốc; **—** = không áp dụng (ca báo lỗi, hoặc chưa đọc lại); còn lại nêu sai lệch. '
  '"Tác động phụ" cho ca mong đợi Lỗi: số hồ sơ cùng tên trước → sau.\n')
for g in order:
    cs = groups[g]
    w(f'### {g}\n')
    risks = {c['risk'] for c in cs if c['risk']}
    if len(risks) == 1:
        w(f'*Rủi ro kiểm tra:* {next(iter(risks))}\n')
    bulk_group = g[0] in 'AHB'
    if bulk_group:
        w('| Mã | Dòng | Dữ liệu vào | Mong đợi | Thực tế | PID | Đối soát | Kết quả | Giây |\n|---|---:|---|---|---|---|---|---|---:|')
        for c in cs:
            rec = 'khớp' if c.get('recon_done', c['group'][0] in 'IJK') and not c['recon'] else ('; '.join(c['recon']) if c['recon'] else '—')
            w(f'| {c["id"]} | {c["line"]} | {inp(c["raw"])} | {short(c["expected"])} | {short(c["actual_type"])} | {c["pid"] or "—"} | {esc(rec, 110)} | {c["verdict"]} | {c["dur"]} |')
    else:
        for c in cs:
            rec = 'khớp' if c.get('recon_done', c['group'][0] in 'IJK') and not c['recon'] else ('; '.join(c['recon']) if c['recon'] else '—')
            side = f'{c["before"]} → {c["after"]}' if c['before'] is not None else '—'
            w(f'**{c["id"]}. {esc(c["title"])}** — **{c["verdict"]}**\n')
            w('| | |\n|---|---|')
            w(f'| Rủi ro | {esc(c["risk"])} |')
            if c['pre']:
                w(f'| Tiền điều kiện | {esc(c["pre"])} |')
            if c['raw']:
                w(f'| Dữ liệu vào (dòng {c["line"]}) | {inp(c["raw"])} |')
            w(f'| Mong đợi | {short(c["expected"])}{(" · từ khóa: " + esc(c["kw"])) if c["kw"] else ""} |')
            w(f'| Thực tế | {short(c["actual_type"])}: {esc(c["actual"], 300)} |')
            w(f'| Đối soát | {esc(rec, 300)} |')
            if c['expected'] == 'ERROR' and c['before'] is not None:
                w(f'| Tác động phụ (số hồ sơ cùng tên) | {side} |')
            if c['why']:
                w(f'| Lý do không đạt | {esc(c["why"], 400)} |')
            if c['note']:
                w(f'| Ghi chú | {esc(c["note"], 400)} |')
            w(f'| Thời gian | {c["dur"]} giây |')
            w('')
    w('')

w('## 7. Điều chưa kiểm thử được và giới hạn\n')
for line in ('Chỉ thử với OHDemo (bản mô phỏng). Hành vi trên OH thật (tên ô, hộp thoại, tốc độ, quyền) có thể khác; cần nghiệm thu riêng.',
             'Chưa thử tình huống khóa màn hình, thoát Remote Desktop, máy ngủ, hoặc OH chạy ở màn hình/độ phân giải khác.',
             'Nhóm I mô phỏng người dùng bằng thao tác chèn đồng bộ giữa hai bước của RPA; chưa thử thao tác song song ngẫu nhiên nhiều người cùng lúc. Khoảng hở rất ngắn giữa lần kiểm tra cuối và lần bấm Lưu vẫn tồn tại, nên sau khi lưu RPA đọc lại hồ sơ và báo lỗi nếu lệch.',
             'Ca I06 (người dùng sửa họ rồi RPA lưu) và các ca tương tự: RPA báo lỗi nêu rõ PID nhưng hồ sơ đã bị lưu dữ liệu lạ; việc sửa lại là của người duyệt, RPA không tự hồi phục vì tìm hồ sơ theo họ tên.',
             'Chưa thử danh sách lớn hơn khoảng 200 dòng liên tục hoặc chạy nhiều giờ.',
             'Dữ liệu ngoài danh sách (ví dụ 1 triệu ký tự trong một ô) và bảng mã đặc biệt ngoài tiếng Việt chưa được thử.',
             'Nhóm F kiểm tra đọc file bằng đúng hàm của RPA và đối chiếu với kiểu lỗi mà `app.load()` bắt; chưa mở giao diện Tk cho từng ca.',
             'Kết quả đạt trên bộ dữ liệu này không bảo đảm đạt trên dữ liệu khác; chỉ chứng minh được trong phạm vi các ca đã nêu.'):
    w(f'- {line}')
w('')
w('## 8. Cách chạy lại\n')
w('```powershell\ncd Prototype\\RPA\nconda activate vinmec\npython kiem_thu\\chay_kiem_thu.py      # khoảng 40 phút; cửa sổ OH sẽ nhảy lên trước\npython kiem_thu\\nhom_i_j.py sau            # nhóm I, J (khoảng 30 phút); tham số truoc = so sánh với bản mã đã lưu\npython kiem_thu\\viet_bao_cao.py       # sinh lại KIEM_THU_RPA.md từ ket_qua.json\n```\n')
w('Biến môi trường để thử nhanh: `KT_FAST=1` (rút gọn nhóm C, D, E), `KT_A=<số>` và `KT_H=<số>` (số người ở nhóm A và H). Trong lúc chạy, đừng thao tác trong cửa sổ OHDemo.\n')

(HERE.parent / 'KIEM_THU_RPA.md').write_text('\n'.join(out), encoding='utf-8')
print('đã ghi KIEM_THU_RPA.md,', total, 'ca,', passed, 'đạt')
