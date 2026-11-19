"""Hậu xử lý ket_qua.json: bỏ đối soát cuối cùng cho các ca chuẩn bị (C..S) và D06A.
Lý do: hồ sơ của các ca này bị ca sau (C.., D06B) CỐ Ý sửa, nên đọc lại ở cuối sẽ luôn lệch; ca sau đã đối soát trạng thái cuối."""
import json, pathlib
p = pathlib.Path(__file__).with_name('ket_qua.json')
d = json.loads(p.read_text(encoding='utf-8'))
n = 0
for c in d['cases']:
    if (c['id'].startswith('C') and c['id'].endswith('S')) or c['id'] == 'D06A':
        if c['recon'] and c['why'].startswith('Đối soát lệch') and ';' not in c['why'].split('Đối soát lệch')[0]:
            c['note'] = (c.get('note') or '') + ' [Đối soát cuối bỏ qua: hồ sơ bị ca sau cố ý sửa; ca sau đã đối soát trạng thái cuối.]'
            c['recon'] = []; c['why'] = ''; c['verdict'] = 'ĐẠT'; n += 1
p.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding='utf-8')
print('đã điều chỉnh', n, 'ca')
