# -*- coding: utf-8 -*-
"""Đổi địa chỉ cũ (xã, huyện, tỉnh) sang địa chỉ mới (xã, tỉnh) sau sáp nhập 2025.

Dùng:  python tra_cuu.py "Xã Tản Hồng" "Huyện Ba Vì" "Hà Nội" [--thon "Thôn 3"]
Dữ liệu: du-lieu/tat-ca.csv (Dorabot, CC BY 4.0, chép từ nghị quyết UBTVQH).
"""
import csv, re, sys, unicodedata
from pathlib import Path

PREFIX = re.compile(r"^(thanh pho|thi tran|thi xa|tinh|huyen|quan|phuong|xa|tp\.?)\s+")

def norm(s):
    s = unicodedata.normalize("NFD", s.replace("đ", "d").replace("Đ", "D"))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn").lower()
    s = re.sub(r"[.,\-]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return PREFIX.sub("", s)

def load():
    p = Path(__file__).parent / "du-lieu" / "tat-ca.csv"
    idx = {}
    for r in csv.DictReader(open(p, encoding="utf-8-sig")):
        k = (norm(r["tinh_cu"]), norm(r["huyen_cu"]), norm(r["xa_cu"]))
        idx.setdefault(k, []).append(r)
    return idx

def tra(xa, huyen, tinh, idx=None):
    idx = idx or load()
    t, h, x = norm(tinh), norm(huyen), norm(xa)
    return [r for k, rows in idx.items() if k[0] == t and k[2] == x and (not h or k[1] == h) for r in rows]

if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    thon = sys.argv[sys.argv.index("--thon") + 1] if "--thon" in sys.argv else ""
    if thon: a.remove(thon)
    if len(a) != 3:
        sys.exit(__doc__)
    res = tra(*a)
    if not res:
        sys.exit("Không tìm thấy. Kiểm tra lại tên xã/huyện/tỉnh cũ.")
    for r in res:
        print(f"{thon + ', ' if thon else ''}{r['xa_moi']}, {r['tinh_moi']}  [{r['phan']}, {r['nghi_quyet']}]")
    if len(res) > 1:
        print("LƯU Ý: xã cũ bị chia cho nhiều xã mới; cần thôn/ấp để chọn đúng dòng (xem nghị quyết).")
