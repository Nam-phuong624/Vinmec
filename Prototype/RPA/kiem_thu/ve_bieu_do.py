"""Vẽ MỘT hình tổng hợp bằng chứng an toàn của RPA từ kết quả kiểm thử mới nhất (không nhập tay số liệu).

Nguồn: kiem_thu/ket_qua.json (nhóm A–H) và kiem_thu/ket_qua_ij_sau.json (nhóm I, J) trên mã hiện tại.
Mỗi ca được phân loại:
  Tự động đúng / Chuyển người duyệt đúng / Chịu can thiệp-ngắt mà không ghi sai  → an toàn;
  VI PHẠM (dữ liệu sai vẫn được nhập, ghi lệch Excel, hồ sơ thừa/trùng, ghi nhầm người) → vi phạm.
Chạy:  python kiem_thu\\ve_bieu_do.py   →  bieu_do/an_toan_rpa.png
"""
import json
import sys
import textwrap
from collections import Counter, OrderedDict
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyBboxPatch, Rectangle

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
OUT = HERE.parent / 'bieu_do'
OUT.mkdir(exist_ok=True)
DATA = json.loads((HERE / 'ket_qua.json').read_text(encoding='utf-8'))
IJ = json.loads((HERE / 'ket_qua_ij_sau.json').read_text(encoding='utf-8'))
KK = json.loads((HERE / 'ket_qua_k.json').read_text(encoding='utf-8'))
CASES = DATA['cases'] + IJ['cases'] + KK['cases']
finished = DATA['meta'].get('finished', '')[:10]

for f in ('segoeui.ttf', 'segoeuib.ttf'):
    font_manager.fontManager.addfont(rf'C:\Windows\Fonts\{f}')
plt.rcParams['font.family'] = 'Segoe UI'

AUTO, REVIEW, ROBUST, WRONG = 'Tự động đúng', 'Chuyển người duyệt đúng', 'Chịu can thiệp / bị ngắt mà không ghi sai', 'VI PHẠM an toàn'
DETECT = 'Phát hiện và hoàn tác được sau khi ghi'
COLOR = {AUTO: '#2e9e5b', REVIEW: '#2f7fd1', ROBUST: '#12a3a3', WRONG: '#d93a3a', DETECT: '#7a5af8'}
INK, GREY, BG = '#1d2733', '#667085', '#ffffff'
WRITE, STOP = ('CREATE', 'UPDATE', 'SAME'), ('ERROR', 'MANUAL')


def classify(c):
    if c['verdict'] != 'ĐẠT':
        return WRONG
    exp, act = c['expected'], c['actual_type']
    side = c.get('before') is not None and c.get('after') is not None and c['before'] >= 0 and c['after'] != c['before']
    if (exp in STOP and act in WRITE) or (exp == 'ERROR' and side) or (act in WRITE and c.get('recon')):
        return WRONG
    if c['group'][0] == 'K':
        return DETECT
    if c['group'][0] in 'IJ':
        return ROBUST
    return REVIEW if act in STOP else AUTO


for c in CASES:
    c['cls'] = classify(c)
TOTAL = len(CASES)
bad_total = sum(c['cls'] == WRONG for c in CASES)
CNT = Counter(c['cls'] for c in CASES)

GROUPS = OrderedDict()
for c in CASES:
    g = 'C. Cập nhật người đã có' if c['group'].startswith('C.') else c['group']
    GROUPS.setdefault(g, []).append(c)
GROUPS = OrderedDict(sorted(GROUPS.items(), key=lambda kv: kv[0][0]))


def subset(fn):
    cs = [c for c in CASES if fn(c)]
    return len(cs), sum(c['cls'] == WRONG for c in cs)


# Các điều cần chứng minh và số ca kiểm tra mỗi điều (đếm từ dữ liệu, không nhập tay)
CLAIMS = [
    ('Dữ liệu hợp lệ được nhập đúng, đọc lại khớp Excel', subset(lambda c: c['group'][0] in 'ACDH' and c['expected'] in WRITE)),
    ('Dữ liệu sai, thiếu, file hỏng bị chặn, không ghi vào OH', subset(lambda c: c['group'][0] in 'DEFG' and c['expected'] in STOP)),
    ('Chạy lại cùng danh sách không tạo hồ sơ trùng', subset(lambda c: c['group'][0] == 'B')),
    ('Người dùng thao tác trên OH khi RPA chạy: không ghi nhầm người, không trùng', subset(lambda c: c['group'][0] == 'I')),
    ('OH / RPA bị tắt hay bấm Dừng giữa chừng: không ghi sai, dòng dở có dấu vết', subset(lambda c: c['group'][0] == 'J')),
    ('Sai sót sau khi ghi được phát hiện (đối soát) và hoàn tác (khôi phục), không ghi đè thay đổi của người khác', subset(lambda c: c['group'][0] == 'K')),
]


def tile(ax, x, y, w, h, big, small, color):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.0,rounding_size=0.012', fc='#f6f8fa', ec='#d8dee6', lw=1.2))
    ax.add_patch(Rectangle((x, y), 0.006, h, fc=color, ec='none'))
    ax.text(x + 0.02, y + h * 0.58, big, fontsize=30, fontweight='bold', color=color, va='center')
    ax.text(x + 0.02, y + h * 0.2, small, fontsize=12.5, color=GREY, va='center')


fig = plt.figure(figsize=(19.2, 10.8), dpi=100, facecolor=BG)
ax0 = fig.add_axes([0, 0, 1, 1]); ax0.axis('off')
ax0.text(0.5, 0.955, 'Kiểm thử cơ chế hoạt động của RPA lên OH', fontsize=26, fontweight='bold', color=INK, va='center', ha='center')
ax0.text(0.03, 0.915, f'{TOTAL} ca chạy thật trên OHDemo ngày {finished}. Sau mỗi ca, toàn bộ hồ sơ trong OH được đọc lại và đối chiếu với dữ liệu gốc.', fontsize=13.5, color=GREY, va='center')

main_runs = [c for c in CASES if c['group'][0] in 'ABH']
ij = [c for c in CASES if c['group'][0] in 'IJ']
kk = [c for c in CASES if c['group'][0] == 'K']
ok_color = COLOR[AUTO] if bad_total == 0 else COLOR[WRONG]
tile(ax0, 0.03, 0.775, 0.22, 0.105, f'{TOTAL - bad_total}/{TOTAL}', 'ca đạt (không vi phạm an toàn)', ok_color)
tile(ax0, 0.265, 0.775, 0.22, 0.105, str(bad_total), 'ca ghi sai dữ liệu / không qua người duyệt', ok_color)
tile(ax0, 0.5, 0.775, 0.22, 0.105, f'{sum(c["cls"] != WRONG for c in ij)}/{len(ij)}', 'ca bị can thiệp hoặc bị ngắt mà không ghi sai', ok_color)
tile(ax0, 0.735, 0.775, 0.235, 0.105, f'{sum(c["cls"] != WRONG for c in main_runs)}/{len(main_runs)}', 'lần tạo mới, chạy lại và khối lượng đúng', ok_color)

ax = fig.add_axes([0.255, 0.2, 0.43, 0.49], facecolor=BG)
names = list(GROUPS)[::-1]
left = [0] * len(names)
for cls in (AUTO, REVIEW, ROBUST, DETECT, WRONG):
    vals = [sum(1 for c in GROUPS[n] if c['cls'] == cls) for n in names]
    if not any(vals):
        continue
    ax.barh(names, vals, left=left, color=COLOR[cls], edgecolor='white', height=0.68, label=cls)
    for i, v in enumerate(vals):
        if v >= 6:
            ax.text(left[i] + v / 2, i, str(v), ha='center', va='center', color='white', fontsize=11.5, fontweight='bold')
    left = [a + b for a, b in zip(left, vals)]
for i, n in enumerate(names):
    ax.text(left[i] + 2, i, str(len(GROUPS[n])), va='center', fontsize=11.5, color=GREY)
ax.set_xlim(0, max(left) * 1.1)
ax.tick_params(axis='y', labelsize=12, length=0, colors=INK)
ax.tick_params(axis='x', labelsize=10.5, colors=GREY)
for s in ('top', 'right', 'left'):
    ax.spines[s].set_visible(False)
ax.spines['bottom'].set_color('#d0d5dd')
ax.set_title('Số ca theo nhóm và kết quả', loc='left', fontsize=15, fontweight='bold', color=INK, pad=12)
ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.1), ncol=2, frameon=False, fontsize=11)

ax1 = fig.add_axes([0.715, 0.2, 0.265, 0.49]); ax1.axis('off'); ax1.set_xlim(0, 1); ax1.set_ylim(0, 1)
ax1.text(0, 1.0, 'Điều đã kiểm chứng', fontsize=15, fontweight='bold', color=INK, va='bottom')
ax1.text(0.80, 0.93, 'Ca', fontsize=11.5, color=GREY, ha='right'); ax1.text(1.0, 0.93, 'Vi phạm', fontsize=11.5, color=GREY, ha='right')
y = 0.84
for text, (n, bad) in CLAIMS:
    lines = textwrap.wrap(text, 38)
    for k, line in enumerate(lines):
        ax1.text(0, y - k * 0.04, line, fontsize=11.5, color=INK, va='center')
    mid = y - (len(lines) - 1) * 0.02
    ax1.text(0.80, mid, str(n), fontsize=13, color=INK, ha='right', va='center')
    ax1.text(1.0, mid, str(bad), fontsize=14, fontweight='bold', color=COLOR[AUTO] if bad == 0 else COLOR[WRONG], ha='right', va='center')
    y -= 0.04 * len(lines) + 0.07
    ax1.plot([0, 1], [y + 0.04, y + 0.04], color='#e4e7ec', lw=0.8)

ax0.text(0.03, 0.02, '"Chuyển người duyệt" = RPA báo Lỗi hoặc Cần điền tay và ghi vào ds lỗi.xlsx. "Vi phạm" gồm: dữ liệu sai vẫn được nhập, ghi lệch so với dữ liệu gốc, '
         'hồ sơ trùng hoặc thừa, ghi nhầm hồ sơ người khác, báo thành công khi dữ liệu sai.', fontsize=10.5, color=GREY)
fig.savefig(OUT / 'an_toan_rpa.png', facecolor=BG)
plt.close(fig)
print('đã vẽ', OUT / 'an_toan_rpa.png')
print({k: CNT[k] for k in (AUTO, REVIEW, ROBUST, DETECT, WRONG)}, CLAIMS)
